"""Does ANY definition of candle 1 make 7, 13 and 21 work?

Every result in this review is conditional on where the count starts, and the
slides never say. They draw a "1" on a chart and count forward. I inferred a
fractal swing pivot, which is a guess -- and if it is the wrong guess then the
whole review tests a method nobody teaches.

So this stops guessing and tries the alternatives. Eight origin definitions,
spanning the readings a practitioner might plausibly mean, each counted three
ways, each asked the same question:

    given a count starting here, is the candle at count n unusually likely to
    be a turn?

The test is deliberately generous to TDT:

  * A "turn" is a local extreme in EITHER direction -- a swing high or a swing
    low over +/- TURN_WINDOW candles. Direction is never assumed, so the test
    cannot fail because I picked the wrong side of the trade.
  * The comparison is against the neighbouring counts from the SAME origin
    set, so an origin that simply lands near turns in general gets no credit;
    only a spike at 7, 13 or 21 specifically counts.
  * No costs, no stops, no execution assumptions. Nothing to get wrong.

If a spike exists under any of these, it will show up here. If none does, the
conclusion stops depending on my choice of origin.
"""
import numpy as np

import counting
import tdtcore

TURN_WINDOW = 5           # a turn is a local extreme over +/- this many candles
MAX_COUNT = 30
KEYS = (7, 13, 21)


# ------------------------------------------------------------------- turns
def turn_mask(bars, m=TURN_WINDOW):
    """True where a candle is a local high or a local low over +/- m candles.

    Direction-agnostic on purpose: TDT says the count marks a decision point,
    not which way it resolves, so requiring a particular direction would be a
    stricter test than the claim.
    """
    h, l = bars["h"], bars["l"]
    n = len(h)
    hi = np.full(n, -np.inf)
    lo = np.full(n, np.inf)
    for off in range(1, m + 1):
        hi[off:] = np.maximum(hi[off:], h[:-off])
        hi[:-off] = np.maximum(hi[:-off], h[off:])
        lo[off:] = np.minimum(lo[off:], l[:-off])
        lo[:-off] = np.minimum(lo[:-off], l[off:])
    valid = np.zeros(n, bool)
    valid[m:n - m] = True
    return valid & ((h > hi) | (l < lo))


# --------------------------------------------------------- origin definitions
def origin_swing(bars, k):
    """Fractal pivot of strength k -- the definition used everywhere else."""
    ih, il = counting.swings(bars["h"], bars["l"], k)
    o = np.sort(np.concatenate([ih, il]))
    # a pivot is not knowable for k candles, so the count can only be acted on
    # from o+k; the origin itself is still the pivot bar
    return o, k


def origin_session_open(bars, raw, src, hour):
    """The first candle of each session at a given New York hour."""
    hh = raw["hh"][src]
    mm = raw["mm"][src]
    at = (hh == hour) & (mm < 15)
    idx = np.flatnonzero(at)
    if not len(idx):
        return idx, 0
    # keep the first candle of each contiguous run
    keep = np.r_[True, np.diff(idx) > 1]
    return idx[keep], 0


def origin_htf_open(bars, raw, src, block_hours=4):
    """The first candle of each higher-timeframe block."""
    hh = raw["hh"][src].astype(np.int64)
    blk = hh // block_hours
    chg = np.r_[True, np.diff(blk) != 0]
    return np.flatnonzero(chg), 0


def origin_sweep(bars, raw, src, side="high"):
    """The candle that takes out the previous session's high or low.

    A liquidity sweep -- the origin an ICT/CRT-influenced reader is most likely
    to mean by "1", and the most credible alternative to a swing pivot.
    """
    sess = tdtcore.session_index({"hh": raw["hh"][src]})
    n = len(bars["c"])
    out = []
    # running previous-session extremes
    starts = np.r_[0, np.flatnonzero(np.diff(sess) != 0) + 1]
    stops = np.r_[starts[1:], n]
    prev_hi = prev_lo = None
    for a, b in zip(starts.tolist(), stops.tolist()):
        if prev_hi is not None:
            seg = slice(a, b)
            if side == "high":
                hit = np.flatnonzero(bars["h"][seg] > prev_hi)
            else:
                hit = np.flatnonzero(bars["l"][seg] < prev_lo)
            if len(hit):
                out.append(a + int(hit[0]))
        prev_hi = bars["h"][a:b].max()
        prev_lo = bars["l"][a:b].min()
    return np.array(sorted(out), np.int64), 0


def origin_expansion(bars, mult=2.0, look=20):
    """The first candle whose range exceeds `mult` times the recent average."""
    rng = bars["h"] - bars["l"]
    cs = np.concatenate([[0.0], np.cumsum(rng)])
    n = len(rng)
    idx = np.arange(n)
    lo = np.maximum(idx - look, 0)
    avg = (cs[idx] - cs[lo]) / np.maximum(1, idx - lo)
    big = rng > mult * np.maximum(avg, 1e-9)
    big[:look] = False
    # first of each run, so a volatile stretch does not flood the sample
    return np.flatnonzero(big & ~np.r_[False, big[:-1]]), 0


def origin_engulf(bars):
    """An engulfing candle -- body covering the prior candle's body."""
    o, c = bars["o"], bars["c"]
    top = np.maximum(o, c)
    bot = np.minimum(o, c)
    eng = np.zeros(len(o), bool)
    eng[1:] = (top[1:] >= top[:-1]) & (bot[1:] <= bot[:-1]) & \
              ((top[1:] - bot[1:]) > (top[:-1] - bot[:-1]))
    return np.flatnonzero(eng), 0


# ------------------------------------------------------------------- the test
def count_positions(bars, origins, mode, max_count=MAX_COUNT):
    """Bar index of each count 1..max_count, for every origin. -1 where absent.

    Rows are origins, columns are counts. Classic is pure arithmetic; the
    contraction modes walk the expansion rule forward.
    """
    n = len(bars["c"])
    pos = np.full((len(origins), max_count), -1, np.int64)
    if mode == "classic":
        for j in range(max_count):
            b = origins + j
            pos[:, j] = np.where(b < n, b, -1)
        return pos

    # Contraction modes need a direction; take the one the leg opens in, from
    # the first candle's close against the origin's close.
    #
    # The counted candles are exactly the running-max records of the rail from
    # the origin, so this reads them off with numpy per origin rather than
    # walking candle by candle and allocating a Count object each time. That is
    # the difference between this finishing in a minute and in two hours.
    up = bars["c"][np.minimum(origins + 1, n - 1)] >= bars["c"][origins]
    top = np.maximum(bars["o"], bars["c"])
    bot = np.minimum(bars["o"], bars["c"])
    rail_up = bars["h"] if mode == "wick" else top
    rail_dn = bars["l"] if mode == "wick" else bot
    span = max_count * 6      # enough room for max_count records in most legs

    for i, o in enumerate(origins.tolist()):
        end = min(n, o + span)
        if end - o < 2:
            continue
        w = rail_up[o:end] if up[i] else rail_dn[o:end]
        run = np.maximum.accumulate(w) if up[i] else np.minimum.accumulate(w)
        rec = np.empty(len(w), bool)
        rec[0] = True
        rec[1:] = run[1:] != run[:-1]
        idx = np.flatnonzero(rec)[:max_count]
        pos[i, :len(idx)] = o + idx
    return pos


def hazard_by_count(bars, origins, mode, turns, max_count=MAX_COUNT):
    """P(the candle at count n is a local turn), for n = 1..max_count."""
    pos = count_positions(bars, origins, mode, max_count)
    rows = []
    for j in range(max_count):
        b = pos[:, j]
        ok = b >= 0
        if ok.sum() < 50:
            rows.append({"n": j + 1, "n_obs": int(ok.sum()), "p": float("nan")})
            continue
        rows.append({"n": j + 1, "n_obs": int(ok.sum()),
                     "p": float(turns[b[ok]].mean())})
    return rows


def neighbour_z(rows, keys=KEYS, gap=1, width=4):
    """Each key count against nearby counts, skipping immediate neighbours."""
    by = {r["n"]: r for r in rows}
    out = []
    for key in keys:
        near = [by[m]["p"] for m in range(key - gap - width, key + gap + width + 1)
                if m in by and abs(m - key) > gap and np.isfinite(by[m]["p"])]
        r = by.get(key)
        if r is None or not np.isfinite(r["p"]) or len(near) < 4:
            out.append({"key": key, "z": float("nan"), "n_obs": r["n_obs"] if r else 0})
            continue
        near = np.asarray(near, float)
        sd = near.std(ddof=1)
        out.append({"key": int(key), "p": r["p"], "baseline": float(near.mean()),
                    "z": float((r["p"] - near.mean()) / sd) if sd > 0 else float("nan"),
                    "n_obs": r["n_obs"]})
    return out


# ------------------------------------------------------------------- driver
def origin_sets(bars, raw, src):
    """Every origin definition worth trying, as {name: bar indices}."""
    return {
        "swing pivot k=2": origin_swing(bars, 2)[0],
        "swing pivot k=3": origin_swing(bars, 3)[0],
        "swing pivot k=5": origin_swing(bars, 5)[0],
        "CME session open 18:00": origin_session_open(bars, raw, src, 18)[0],
        "RTH open 09:30": origin_session_open(bars, raw, src, 9)[0],
        "H4 block open": origin_htf_open(bars, raw, src, 4)[0],
        "sweep of prior session high": origin_sweep(bars, raw, src, "high")[0],
        "sweep of prior session low": origin_sweep(bars, raw, src, "low")[0],
        "range expansion candle": origin_expansion(bars)[0],
        "engulfing candle": origin_engulf(bars)[0],
    }


def main():
    import json
    import os
    import time

    HERE = os.path.dirname(os.path.abspath(__file__))
    t0 = time.time()
    raw = tdtcore.load(from_year=2016)
    out = {"meta": {"turn_window": TURN_WINDOW, "keys": list(KEYS),
                    "built": time.strftime("%Y-%m-%d %H:%M:%S")},
           "results": []}

    for tf in ("M15", "H1"):
        bars = tdtcore.resample(raw, tf)
        src = bars["src"]
        turns = turn_mask(bars)
        base = float(turns.mean())
        out["meta"]["base_rate_%s" % tf] = base
        print("\n%s -- %s candles, base turn rate %.2f%%"
              % (tf, "{:,}".format(len(bars["c"])), 100 * base))

        rng = np.random.default_rng(19)
        for name, org in origin_sets(bars, raw, src).items():
            if len(org) < 200:
                continue
            # 20,000 origins estimates a proportion to about +/-0.4%, which is
            # far finer than any effect being looked for here
            if len(org) > 20000:
                org = np.sort(rng.choice(org, 20000, replace=False))
            for mode in counting.MODES:
                rows = hazard_by_count(bars, org, mode, turns)
                nz = neighbour_z(rows)
                for r in nz:
                    out["results"].append({
                        "tf": tf, "origin": name, "mode": mode,
                        "n_origins": int(len(org)), **r})
                best = max((r for r in nz if np.isfinite(r.get("z", np.nan))),
                           key=lambda r: r["z"], default=None)
                if best:
                    print("  %-28s %-8s  best key %2d  z=%+5.2f  p=%.3f (base %.3f)"
                          % (name, mode, best["key"], best["z"], best["p"], base))
            out.setdefault("curves", {})["%s|%s" % (tf, name)] = \
                hazard_by_count(bars, org, "classic", turns)

    # The clock is the confound to rule out before believing any hit. NQ has
    # enormous time-of-day structure -- 09:30 New York, the cash open, turns
    # three times as often as an average candle -- so any origin on a fixed
    # clock grid can put a key count on top of it and inherit the effect.
    bars15 = tdtcore.resample(raw, "M15")
    src15 = bars15["src"]
    t15 = turn_mask(bars15)
    hh, mm = raw["hh"][src15], raw["mm"][src15]
    clock = []
    for h in range(24):
        for m in (0, 15, 30, 45):
            sel = (hh == h) & (mm == m)
            if sel.sum() > 200:
                clock.append({"time": "%02d:%02d" % (h, m),
                              "p": float(t15[sel].mean()), "n": int(sel.sum())})
    out["clock"] = sorted(clock, key=lambda r: -r["p"])

    # and the control that settles it: shift the HTF block grid by an hour so
    # the same count lands on a different clock time
    shifted = []
    for shift in (0, 1, 2, 3):
        h2 = (raw["hh"][src15].astype(np.int64) - shift) % 24
        blk = h2 // 4
        org = np.flatnonzero(np.r_[True, np.diff(blk) != 0])
        rows = hazard_by_count(bars15, org, "classic", t15)
        for r in neighbour_z(rows):
            shifted.append({"shift_hours": shift, **r})
    out["htf_shift_control"] = shifted
    print("\nHTF block grid shifted -- does the count-7 hit survive?")
    for r in shifted:
        if r["key"] == 7:
            print("  blocks shifted %dh: count 7 p=%.3f  z=%+.2f"
                  % (r["shift_hours"], r.get("p", float("nan")), r["z"]))

    zs = [r["z"] for r in out["results"] if np.isfinite(r.get("z", np.nan))]
    out["meta"]["n_tests"] = len(zs)
    out["meta"]["max_z"] = float(max(zs)) if zs else float("nan")
    out["meta"]["min_z"] = float(min(zs)) if zs else float("nan")
    # with this many tests, some large z is expected from noise alone
    out["meta"]["expected_max_z_null"] = float(
        np.sqrt(2 * np.log(max(2, len(zs)))))

    with open(os.path.join(HERE, "ORIGINS.json"), "w") as fh:
        json.dump(out, fh, separators=(",", ":"), default=float)
    print("\n%d tests | max z %+.2f | min z %+.2f | expected max under null %+.2f"
          % (len(zs), out["meta"]["max_z"], out["meta"]["min_z"],
             out["meta"]["expected_max_z_null"]))
    print("wrote ORIGINS.json in %.0fs" % (time.time() - t0))
    return out


if __name__ == "__main__":
    main()
