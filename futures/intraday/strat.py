"""Intraday PO3 strategy backtests, swept across a continuum of block sizes.

Three strategies, rules fixed before any result was looked at. Each runs for
every R on a log-spaced continuum from 27 to 6561 with the exact powers of
three forced in. The continuum IS the null: if a power of three is special,
the metric must PEAK at 3^n rather than varying smoothly with size.

Fill model, deliberately conservative:
  * Level entries are resting limit orders at a price the bar actually traded
    through, detected by the bar's high/low straddling the level -- never by a
    close that has already moved past it.
  * Stop and target are resolved from the entry bar INCLUSIVE, so a bar that
    blows straight through the level is charged as a loss rather than granted a
    free entry.
  * When one bar's range contains both stop and target, the stop is taken.
  * Cost is charged round-trip on every trade.
Outcomes are reported as target / stop / timeout so the R-multiple is real
rather than inferred from a bare win rate.
"""
import json
import os

import numpy as np

import core

COST = 1.0          # points round-trip on NQ
STOP_F = 0.10       # stop distance as a fraction of R
MAX_PER_SESSION = 3
MIN_STOP_PTS = 2.0  # below this a stop sits inside one bar's noise


def _resolve(h, l, stop, target, is_long):
    """First-passage from the entry bar inclusive. Returns (px, bars, outcome)."""
    if len(h) == 0:
        return None, 0, "timeout"
    if is_long:
        hit_t, hit_s = h >= target, l <= stop
    else:
        hit_t, hit_s = l <= target, h >= stop
    it = int(np.argmax(hit_t)) if hit_t.any() else 10 ** 9
    isx = int(np.argmax(hit_s)) if hit_s.any() else 10 ** 9
    if it == 10 ** 9 and isx == 10 ** 9:
        return None, len(h), "timeout"
    if isx <= it:
        return stop, isx + 1, "stop"
    return target, it + 1, "target"


def _trade(h, l, c, entry, stop, target, is_long, risk):
    px, held, how = _resolve(h, l, stop, target, is_long)
    if px is None:
        px = c[-1] if len(c) else entry
    gross = (px - entry) if is_long else (entry - px)
    return {"pnl": gross - COST, "bars": held, "risk": risk, "how": how}


# ------------------------------------------------------------------ S1
def s1_block_traverse(bars, st, sp, R, phase=0.0):
    """Sweep the near block edge, then traverse to the far edge.

    The framework's own mechanic: the edge is run for liquidity, price rejects,
    and works to the opposite side of the dealing range. The edge is known at
    the session open, so a resting limit there is realistic.
    """
    h, l, c, o = bars["h"], bars["l"], bars["c"], bars["o"]
    off = R * phase / 100.0
    risk = STOP_F * R
    if risk < MIN_STOP_PTS:
        return []
    out = []
    for a, b in zip(st, sp):
        O = o[a]
        lo_edge = np.floor((O - off) / R) * R + off
        hi_edge = lo_edge + R
        near_is_low = (O - lo_edge) <= (hi_edge - O)
        edge = lo_edge if near_is_low else hi_edge
        H, L, C = h[a:b], l[a:b], c[a:b]
        touch = np.flatnonzero((L <= edge) & (H >= edge))
        if len(touch) == 0:
            continue
        i = int(touch[0])
        is_long = near_is_low
        stop = edge - risk if is_long else edge + risk
        target = hi_edge if is_long else lo_edge
        out.append(_trade(H[i:], L[i:], C[i:], edge, stop, target, is_long, risk))
    return out


# ------------------------------------------------------------------ S2
def s2_edge_fade(bars, st, sp, R, phase=0.0):
    """Fade every lattice boundary touch, 1:1 stop and target."""
    h, l, c = bars["h"], bars["l"], bars["c"]
    off = R * phase / 100.0
    risk = STOP_F * R
    if risk < MIN_STOP_PTS:
        return []
    out = []
    for a, b in zip(st, sp):
        H, L, C = h[a:b], l[a:b], c[a:b]
        if len(H) < 30:
            continue
        k = np.floor((C - off) / R).astype(np.int64)
        lo_k, hi_k = int(k.min()), int(k.max())

        # collect every (time, edge) touch, then process them in TIME order --
        # taking them in price order picks trades using knowledge of which
        # levels get visited later in the session, which is not tradeable.
        events = []
        for kk in range(lo_k, hi_k + 2):
            edge = R * kk + off
            for i in np.flatnonzero((L <= edge) & (H >= edge)):
                events.append((int(i), edge))
        events.sort()

        used, last = 0, -999
        for i, edge in events:
            if used >= MAX_PER_SESSION:
                break
            if i - last < 30:
                continue
            j = max(0, i - 5)                  # approach direction, 5 bars back
            if C[j] == edge:
                continue
            is_long = not (C[j] < edge)        # arrived from below -> fade down
            stop = edge - risk if is_long else edge + risk
            target = edge + risk if is_long else edge - risk
            out.append(_trade(H[i:], L[i:], C[i:], edge, stop, target, is_long, risk))
            used += 1
            last = i
    return out


# ------------------------------------------------------------------ S3
def s3_range_complete(bars, st, sp, R, phase=0.0):
    """Once the session has expanded by R, fade the last extension.

    Entry is a market order at the close of the trigger bar, so resolution
    starts on the following bar.
    """
    h, l, c = bars["h"], bars["l"], bars["c"]
    risk = STOP_F * R
    if risk < MIN_STOP_PTS:
        return []
    out = []
    for a, b in zip(st, sp):
        H, L, C = h[a:b], l[a:b], c[a:b]
        if len(H) < 30:
            continue
        rh = np.maximum.accumulate(H)
        rl = np.minimum.accumulate(L)
        done = np.flatnonzero((rh - rl) >= R)
        if len(done) == 0:
            continue
        i = int(done[0])
        if i >= len(H) - 2 or i == 0:
            continue
        up = rh[i] > rh[i - 1]
        is_long = not up
        entry = C[i]
        stop = entry - risk if is_long else entry + risk
        target = entry + 2 * risk if is_long else entry - 2 * risk
        out.append(_trade(H[i + 1:], L[i + 1:], C[i + 1:], entry, stop, target, is_long, risk))
    return out


STRATS = {"S1_traverse": s1_block_traverse,
          "S2_edge_fade": s2_edge_fade,
          "S3_range_complete": s3_range_complete}


def stats(trades):
    if not trades:
        return {"n": 0}
    pnl = np.array([t["pnl"] for t in trades])
    risk = np.array([t["risk"] for t in trades])
    how = [t["how"] for t in trades]
    r = pnl / risk
    wins, losses = pnl[pnl > 0], pnl[pnl <= 0]
    eq = np.cumsum(pnl)
    dd = float((np.maximum.accumulate(eq) - eq).max()) if len(eq) else 0.0
    sd = pnl.std(ddof=1) if len(pnl) > 2 else 0.0
    return {
        "n": int(len(pnl)),
        # cost is a constant per-trade shift, so storing the gross mean and the
        # dispersion lets any cost be applied later without re-running:
        #   exp_net = exp_gross - cost      t = (exp_gross - cost)/(sd/sqrt(n))
        "exp_gross": float(pnl.mean() + COST),
        "sd": float(sd),
        "win_rate": float((pnl > 0).mean()),
        "p_target": float(np.mean([x == "target" for x in how])),
        "p_stop": float(np.mean([x == "stop" for x in how])),
        "p_timeout": float(np.mean([x == "timeout" for x in how])),
        "exp_pts": float(pnl.mean()),
        "exp_R": float(r.mean()),
        "total_pts": float(pnl.sum()),
        "pf": float(wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() < 0 else float("inf"),
        "max_dd": dd,
        "t_stat": float(pnl.mean() / (sd / np.sqrt(len(pnl)))) if sd > 0 else 0.0,
        "med_bars": float(np.median([t["bars"] for t in trades])),
        "risk_pts": float(risk[0]),
    }


def main():
    bars = core.load()
    grid = core.r_grid()
    res = {"cost": COST, "stop_f": STOP_F, "min_stop": MIN_STOP_PTS,
           "grid": grid.tolist(), "sweep": {}}

    for window in ("RTH", "NYAM"):
        st, sp, dates = core.session_slices(bars, window)
        print("\n########  %s  (%d sessions)  ########" % (window, len(st)))
        for name, fn in STRATS.items():
            rows = []
            for R in grid:
                s = stats(fn(bars, st, sp, float(R)))
                s["R"] = float(R)
                s["po3"] = core.is_po3(float(R))
                rows.append(s)
            res["sweep"]["%s|%s" % (window, name)] = rows
            live = [s for s in rows if s.get("n", 0) >= 40]
            print("\n  %s" % name)
            print("    %-7s %6s %6s %6s %6s %8s %7s %6s %8s %7s"
                  % ("R", "n", "tgt%", "stop%", "to%", "exp_pts", "exp_R", "pf", "total", "t"))
            for s in live:
                if not (s["po3"] or abs(s["t_stat"]) > 2.5):
                    continue
                print("    %-7.0f %6d %5.0f%% %5.0f%% %5.0f%% %8.2f %7.3f %6.2f %8.0f %7.2f%s"
                      % (s["R"], s["n"], s["p_target"] * 100, s["p_stop"] * 100,
                         s["p_timeout"] * 100, s["exp_pts"], s["exp_R"], s["pf"],
                         s["total_pts"], s["t_stat"], "  <-- PO3" if s["po3"] else ""))

    with open(os.path.join(core.HERE, "strat.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print("\nwrote strat.json")


if __name__ == "__main__":
    main()
