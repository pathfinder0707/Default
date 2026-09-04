"""Wide parameter search over TDT, selected on train and paid out on test.

The earlier study tested one parameterisation. That is a test of a
parameterisation, not of a method, so this searches the space properly -- and
because a wide search will always find something, the search happens on
2016-2022 alone and every number that matters is measured on 2023-2026, which
selection never touches.

Two readings the first pass never tried, both defensible from the slides:

  polarity   [1-7] is called "continuation of previous fractal" and [1-13]
             "reversal inside of the previous fractal". The first pass faded
             the counted leg in both cases. If those words carry trade
             direction, a 7 should be traded WITH the leg and a 13 against it.
             Both polarities are searched for both counts.

  signal     The first pass required the leg to have ENDED on a key count,
             which a trader only knows k candles later. But a trader watching a
             count act when it REACHES 7 -- no knowledge of the leg's end at
             all. Reach signals need only the origin pivot, so they fire far
             earlier, and they are searched alongside.

Nothing here looks ahead. A swing of strength k is unknown for k candles, so a
terminal signal is dated end+k and a reach signal max(bar_of_count, origin+k).
"""
import numpy as np

import counting
import tdtcore
from counting import DOWN, UP

MAX_REACH = 120          # cap on how far a reach count may run from its origin


# ------------------------------------------------------------- lean counting
def pivots(bars, k):
    """Alternating swing pivots, collapsed to extremes. (idx, dir) arrays."""
    ih, il = counting.swings(bars["h"], bars["l"], k)
    if not len(ih) and not len(il):
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    idx = np.concatenate([ih, il])
    dr = np.concatenate([np.full(len(ih), DOWN, np.int64),
                         np.full(len(il), UP, np.int64)])
    o = np.argsort(idx, kind="stable")
    idx, dr = idx[o], dr[o]

    keep_i, keep_d = [], []
    h, l = bars["h"], bars["l"]
    for i, d in zip(idx.tolist(), dr.tolist()):
        if keep_d and keep_d[-1] == d:
            p = keep_i[-1]
            if (h[i] > h[p]) if d == DOWN else (l[i] < l[p]):
                keep_i[-1] = i
        else:
            keep_i.append(i)
            keep_d.append(d)
    return np.array(keep_i, np.int64), np.array(keep_d, np.int64)


def _rail(bars, mode, direction):
    if mode == "wick":
        return bars["h"] if direction == UP else bars["l"]
    top = np.maximum(bars["o"], bars["c"])
    bot = np.minimum(bars["o"], bars["c"])
    return top if direction == UP else bot


def count_bars(bars, origin, direction, mode, stop, keys, max_count):
    """(terminal_count, {key: bar_index}) for one leg, without allocating objects.

    terminal_count is the number standing at `stop-1`; keys maps each key count
    to the bar that took it, or -1.
    """
    at = {kk: -1 for kk in keys}
    end = min(len(bars["c"]), stop)
    if origin >= end:
        return 0, at
    if mode == "classic":
        n = min(end - origin, max_count)
        for kk in keys:
            if kk <= n:
                at[kk] = origin + kk - 1
        return n, at

    rail = _rail(bars, mode, direction)
    ref = rail[origin]
    n = 1
    if 1 in at:
        at[1] = origin
    up = direction == UP
    for i in range(origin + 1, end):
        v = rail[i]
        if (v > ref) if up else (v < ref):
            n += 1
            ref = v
            if n in at:
                at[n] = i
            if n >= max_count:
                break
    return n, at


def legs_fast(bars, k, mode, keys=(7, 13, 21), max_count=120):
    """Swing-to-swing legs plus, for each, where every key count landed.

    Returns a dict of parallel arrays. `at7/at13/at21` are bar indices, -1 when
    the count never got there inside the leg.
    """
    pi, pd = pivots(bars, k)
    if len(pi) < 2:
        z = np.zeros(0, np.int64)
        return {"start": z, "end": z, "dir": z, "terminal": z,
                "at": {kk: z.copy() for kk in keys}}
    starts, ends, dirs, term = [], [], [], []
    at = {kk: [] for kk in keys}
    for a, d, b in zip(pi[:-1].tolist(), pd[:-1].tolist(), pi[1:].tolist()):
        n, hit = count_bars(bars, a, d, mode, b + 1, keys, max_count)
        starts.append(a); ends.append(b); dirs.append(d); term.append(n)
        for kk in keys:
            at[kk].append(hit[kk])
    out = {"start": np.array(starts, np.int64), "end": np.array(ends, np.int64),
           "dir": np.array(dirs, np.int64), "terminal": np.array(term, np.int64),
           "at": {kk: np.array(at[kk], np.int64) for kk in keys}}
    out.update(segment_extremes(bars, out["start"], out["end"]))
    return out


def segment_extremes(bars, start, end):
    """Low, high and mean range over each [start,end] span.

    Computed once per (timeframe, k, mode) rather than per config: the spans do
    not depend on rr, timeout, pad, polarity or key, and doing it inside the
    grid loop is what makes a sweep this size intractable.
    """
    lo = np.empty(len(start))
    hi = np.empty(len(start))
    for j, (a, b) in enumerate(zip(start.tolist(), end.tolist())):
        seg = slice(a, b + 1)
        lo[j] = bars["l"][seg].min()
        hi[j] = bars["h"][seg].max()
    return {"seg_lo": lo, "seg_hi": hi, "atr": atr_at(bars, start, end + 1)}


def reach_signals(bars, k, mode, key, max_reach=MAX_REACH):
    """Every confirmed swing origin whose forward count reaches `key`.

    The count runs forward from the origin with no reference to any later
    pivot, because a trader watching a count does not know where the leg will
    end. Fires on the candle that takes the number.
    """
    pi, pd = pivots(bars, k)
    n = len(bars["c"])
    sig_bar, sig_dir, sig_org = [], [], []
    for a, d in zip(pi.tolist(), pd.tolist()):
        _, hit = count_bars(bars, a, d, mode, min(n, a + max_reach + 1),
                            (key,), max_reach)
        b = hit[key]
        if b >= 0:
            sig_bar.append(b); sig_dir.append(d); sig_org.append(a)
    out = {"end": np.array(sig_bar, np.int64), "dir": np.array(sig_dir, np.int64),
           "start": np.array(sig_org, np.int64)}
    out.update(segment_extremes(bars, out["start"], out["end"]))
    return out


# ------------------------------------------------------- vectorized simulator
def simulate_vec(xb, x0, d, stop, target, timeout, cost=0.0):
    """Resolve every trade at once, O(timeout) numpy passes rather than O(n).

    Same tie-break as backtest.simulate: a bar spanning both stop and target
    books the stop, since intrabar order is unknowable from OHLC.
    """
    xh, xl, xc = xb["h"], xb["l"], xb["c"]
    xn = len(xc)
    m = len(x0)
    outcome = np.full(m, 2, np.int8)          # 0 stop, 1 target, 2 timeout
    exit_i = np.minimum(x0 + timeout, xn - 1)
    exit_px = np.full(m, np.nan)
    done = np.zeros(m, bool)
    up = d == UP

    for step in range(timeout + 1):
        i = x0 + step
        live = (~done) & (i < xn)
        if not live.any():
            break
        j = np.flatnonzero(live)
        ij = i[j]
        hi, lo = xh[ij], xl[ij]
        u = up[j]
        hit_s = np.where(u, lo <= stop[j], hi >= stop[j])
        hit_t = np.where(u, hi >= target[j], lo <= target[j])
        js = j[hit_s]
        jt = j[hit_t & ~hit_s]
        if len(js):
            outcome[js] = 0; exit_i[js] = i[js]; exit_px[js] = stop[js]; done[js] = True
        if len(jt):
            outcome[jt] = 1; exit_i[jt] = i[jt]; exit_px[jt] = target[jt]; done[jt] = True

    rem = np.flatnonzero(~done)
    if len(rem):
        ei = np.minimum(exit_i[rem], xn - 1)
        exit_i[rem] = ei
        exit_px[rem] = xc[ei]

    return outcome, exit_i, exit_px


def atr_at(bars, lo, hi):
    """Mean candle range over each [lo,hi) span, vectorized via cumsum."""
    rng = bars["h"] - bars["l"]
    cs = np.concatenate([[0.0], np.cumsum(rng)])
    lo = np.clip(lo, 0, len(rng))
    hi = np.clip(np.maximum(hi, lo + 1), 0, len(rng))
    return (cs[hi] - cs[lo]) / (hi - lo)


# ------------------------------------------------------------------ configs
TRAIN_YEARS = (2016, 2022)
TEST_YEARS = (2023, 2026)

GRID = {
    "tf":       ["D1", "H4", "H1", "M15"],
    "mode":     ["classic", "wick", "body"],
    "k":        [2, 3, 4, 5, 6],
    "signal":   ["terminal", "reach"],
    "key":      [7, 13, 21],
    "polarity": ["fade", "follow"],
    "tol":      [0, 1],
    "rr":       [1.0, 1.5, 2.0, 3.0],
    "timeout":  [10, 20, 40],
    "pad":      [0.25, 0.5],
}

# Execution timeframe per counting timeframe: one step finer, which is what
# Model #2 means by "counts on D1, execution on H1".
EXEC_OF = {"D1": "H1", "H4": "M15", "H1": "M15", "M15": "M15"}

# NQ round-turn cost in index points: $4 commission plus one tick of slippage
# each way, at $20 a point and a 0.25-point tick.
COST_PTS = 0.75


def build_signals(bars, L, cfg, reach):
    """Entry bar, trade direction and stop for one config -- indexing only."""
    key, sgn = cfg["key"], (1 if cfg["polarity"] == "follow" else -1)

    if cfg["signal"] == "terminal":
        term = L["terminal"]
        sel = np.abs(term - key) <= cfg["tol"]
        for other in (7, 13, 21):
            if other != key:
                sel &= np.abs(term - key) <= np.abs(term - other)
        idx = np.flatnonzero(sel)
        if not len(idx):
            return None
        src, confirmed = L, L["end"][idx] + cfg["k"]
    else:
        idx = np.arange(len(reach["end"]))
        if not len(idx):
            return None
        src = reach
        confirmed = np.maximum(reach["end"][idx], reach["start"][idx] + cfg["k"])

    d = src["dir"][idx]
    entry_i = confirmed + 1
    ok = entry_i < len(bars["c"]) - 1
    if not ok.any():
        return None
    idx, d, entry_i = idx[ok], d[ok], entry_i[ok]

    # Trade direction first: the stop is defined by what the TRADE risks, not
    # by which way the counted leg ran. Deriving the extreme from the leg
    # direction instead puts the stop on the profit side of a fade, where every
    # "stop" books +1R and the config reports a 95% win rate.
    td = d * sgn
    buf = cfg["pad"] * src["atr"][idx]
    stop = np.where(td == UP, src["seg_lo"][idx] - buf, src["seg_hi"][idx] + buf)
    return {"entry_i": entry_i, "dir": td, "stop": stop}


def evaluate(sig, xb, xmap, cfg, cost_pts, year_of_exec, years):
    """Simulate one config and return stats for the trades inside `years`."""
    x0 = xmap[sig["entry_i"]]
    xn = len(xb["c"])
    ok = x0 < xn - 1
    if not ok.any():
        return None
    x0, td, stop = x0[ok], sig["dir"][ok], sig["stop"][ok]

    yr = year_of_exec[x0]
    inyr = (yr >= years[0]) & (yr <= years[1])
    if inyr.sum() < 20:
        return None
    x0, td, stop = x0[inyr], td[inyr], stop[inyr]

    entry = xb["o"][x0]
    risk = np.abs(entry - stop)
    # the stop must sit on the side the trade actually risks; anything else is
    # a sign convention error, not a trade
    good = (risk > 0) & np.isfinite(risk) & (((entry - stop) * td) > 0)
    if good.sum() < 20:
        return None
    x0, td, stop, entry, risk = x0[good], td[good], stop[good], entry[good], risk[good]
    target = entry + td * cfg["rr"] * risk

    outcome, exit_i, exit_px = simulate_vec(xb, x0, td, stop, target, cfg["timeout"])
    pts = (exit_px - entry) * td - cost_pts
    r = pts / risk
    sd = r.std(ddof=1) if len(r) > 1 else np.nan
    return {
        "n": int(len(r)),
        "win_rate": float((pts > 0).mean()),
        "exp_r": float(r.mean()),
        "sd_r": float(sd),
        "t": float(r.mean() / (sd / np.sqrt(len(r)))) if len(r) > 1 and sd > 0 else float("nan"),
        "total_r": float(r.sum()),
        "p_target": float((outcome == 1).mean()),
        "p_stop": float((outcome == 0).mean()),
        "med_risk": float(np.median(risk)),
        "_r": r,
    }


# ------------------------------------------------------------------- driver
def bootstrap_ci(r, n_boot=2000, seed=3, alpha=0.05):
    """Percentile bootstrap CI for mean R."""
    r = np.asarray(r, float)
    if len(r) < 20:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = r[rng.integers(0, len(r), size=(n_boot, len(r)))].mean(axis=1)
    return (float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2)))


def control_stats(bars, L, xb, xmap, yr, years, rr=2.0, timeout=20, pad=0.25,
                  cost=COST_PTS):
    """Fade every leg regardless of count -- the benchmark any TDT config must beat.

    Same entry, stop, target and timeout. Only membership differs, which is the
    whole question: does the count select better legs, or merely fewer?
    """
    cfg = {"key": 7, "polarity": "fade", "signal": "terminal", "tol": 99,
           "k": 0, "rr": rr, "timeout": timeout, "pad": pad}
    idx = np.arange(len(L["start"]))
    td = L["dir"][idx] * -1
    buf = pad * L["atr"][idx]
    stop = np.where(td == UP, L["seg_lo"][idx] - buf, L["seg_hi"][idx] + buf)
    sig = {"entry_i": L["end"][idx] + 1, "dir": td, "stop": stop}
    ok = sig["entry_i"] < len(bars["c"]) - 1
    sig = {k: v[ok] for k, v in sig.items()}
    return evaluate(sig, xb, xmap, cfg, cost, yr, years)


def iter_configs():
    """The search space, with reach's meaningless tol collapsed."""
    from itertools import product
    g = GRID
    for tf, mode, k, signal, key, pol, rr, to, pad in product(
            g["tf"], g["mode"], g["k"], g["signal"], g["key"],
            g["polarity"], g["rr"], g["timeout"], g["pad"]):
        tols = g["tol"] if signal == "terminal" else [0]
        for tol in tols:
            yield {"tf": tf, "mode": mode, "k": k, "signal": signal, "key": key,
                   "polarity": pol, "tol": tol, "rr": rr, "timeout": to, "pad": pad}


def main():
    import json
    import time
    t_start = time.time()

    raw = tdtcore.load(from_year=2016)
    tfs = sorted(set(GRID["tf"]))
    series, execs, years_of = {}, {}, {}
    for tf in tfs:
        series[tf] = tdtcore.resample(raw, tf)
        execs[tf] = tdtcore.exec_map(raw, tf, EXEC_OF[tf])
        years_of[tf] = raw["yr"][execs[tf]["bars"]["src"]]
        print("  %-4s %8s candles, exec on %-4s %8s candles"
              % (tf, "{:,}".format(len(series[tf]["c"])), EXEC_OF[tf],
                 "{:,}".format(len(execs[tf]["bars"]["c"]))))

    print("\nbuilding caches ...")
    legc, reachc = {}, {}
    for tf in tfs:
        for k in GRID["k"]:
            for mode in GRID["mode"]:
                legc[(tf, k, mode)] = legs_fast(series[tf], k, mode)
                for key in GRID["key"]:
                    reachc[(tf, k, mode, key)] = reach_signals(series[tf], k, mode, key)
    print("  %d leg caches, %d reach caches in %.0fs"
          % (len(legc), len(reachc), time.time() - t_start))

    configs = list(iter_configs())
    print("\nsearching %s configs on TRAIN %d-%d ..."
          % ("{:,}".format(len(configs)), *TRAIN_YEARS))
    rows = []
    t0 = time.time()
    for ci, cfg in enumerate(configs):
        tf = cfg["tf"]
        L = legc[(tf, cfg["k"], cfg["mode"])]
        R = reachc[(tf, cfg["k"], cfg["mode"], cfg["key"])]
        sig = build_signals(series[tf], L, cfg, R)
        if sig is None:
            continue
        st = evaluate(sig, execs[tf]["bars"], execs[tf]["xmap"], cfg,
                      COST_PTS, years_of[tf], TRAIN_YEARS)
        if st is None or st["n"] < 100:
            continue
        st.pop("_r", None)
        rows.append(dict(cfg, **st))
        if (ci + 1) % 5000 == 0:
            print("    %s/%s  %.0fs" % ("{:,}".format(ci + 1),
                  "{:,}".format(len(configs)), time.time() - t0))
    print("  %s configs met the 100-trade floor, in %.0fs"
          % ("{:,}".format(len(rows)), time.time() - t0))

    # one finalist per reading, so twelve near-identical neighbours of a single
    # lucky config cannot fill the shortlist
    fams = {}
    for r in rows:
        fam = (r["signal"], r["key"], r["polarity"])
        if fam not in fams or r["t"] > fams[fam]["t"]:
            fams[fam] = r
    finalists = sorted(fams.values(), key=lambda r: -r["t"])
    print("\n%d families -> %d finalists carried to TEST %d-%d"
          % (len(fams), len(finalists), *TEST_YEARS))

    # controls on both periods, per timeframe used by a finalist
    controls = {}
    for tf in sorted({f["tf"] for f in finalists}):
        for k in sorted({f["k"] for f in finalists if f["tf"] == tf}):
            for mode in sorted({f["mode"] for f in finalists
                                if f["tf"] == tf and f["k"] == k}):
                L = legc[(tf, k, mode)]
                for period, yrs in (("train", TRAIN_YEARS), ("test", TEST_YEARS)):
                    c = control_stats(series[tf], L, execs[tf]["bars"],
                                      execs[tf]["xmap"], years_of[tf], yrs)
                    if c:
                        c.pop("_r", None)
                        controls["%s|%d|%s|%s" % (tf, k, mode, period)] = c

    out_finals = []
    for f in finalists:
        tf = f["tf"]
        L = legc[(tf, f["k"], f["mode"])]
        R = reachc[(tf, f["k"], f["mode"], f["key"])]
        sig = build_signals(series[tf], L, f, R)
        te = evaluate(sig, execs[tf]["bars"], execs[tf]["xmap"], f,
                      COST_PTS, years_of[tf], TEST_YEARS)
        rec = {"config": {kk: f[kk] for kk in
                          ("tf", "mode", "k", "signal", "key", "polarity",
                           "tol", "rr", "timeout", "pad")},
               "train": {kk: f[kk] for kk in
                         ("n", "win_rate", "exp_r", "t", "total_r", "sd_r",
                          "p_target", "p_stop", "med_risk")}}
        if te is None:
            rec["test"] = None
        else:
            r = te.pop("_r")
            lo, hi = bootstrap_ci(r)
            rec["test"] = dict(te, ci_lo=lo, ci_hi=hi)
            rec["test_equity"] = [round(float(v), 3) for v in np.cumsum(r)][::max(1, len(r) // 300)]
        rec["control_key"] = "%s|%d|%s" % (tf, f["k"], f["mode"])
        out_finals.append(rec)

    payload = {
        "meta": {
            "built": time.strftime("%Y-%m-%d %H:%M:%S"),
            "train_years": list(TRAIN_YEARS), "test_years": list(TEST_YEARS),
            "cost_pts": COST_PTS, "grid": GRID,
            "configs_searched": len(configs), "configs_scored": len(rows),
            "families": len(fams),
            "bonferroni_alpha": 0.05 / max(1, len(finalists)),
        },
        "finalists": out_finals,
        "controls": controls,
        "train_t_distribution": sorted(round(r["t"], 3) for r in rows),
        "top_train": sorted(rows, key=lambda r: -r["t"])[:40],
    }
    with open("SWEEP.json", "w") as fh:
        json.dump(payload, fh, separators=(",", ":"), default=float)
    print("wrote SWEEP.json in %.0fs total" % (time.time() - t_start))
    return payload


if __name__ == "__main__":
    main()
