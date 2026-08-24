"""The test that decides whether the edge is tradeable: fill realism.

The backtest assumes a resting limit at the level fills every time a bar's
range touches it. In reality the trades that work best are exactly the ones
where price tags the level and reverses -- and those are the fills you are most
likely to MISS, because price never traded through your order. That is adverse
selection, and it is the standard way a limit-entry backtest flatters itself.

Test: require price to trade PEN points BEYOND the level before counting a
fill. PEN=0 is the optimistic original. As PEN rises the fill assumption gets
stricter and the easy reversals drop out. An edge that survives PEN=2-3 is
credible; one that dies at PEN=1 was a fill artifact.

Also breaks the edge down by time of day, and emits the equity curve for the
recommended configuration.
"""
import json
import os

import numpy as np

import core
import strat


def s2_pen(bars, st, sp, Rs, pen, tod=None, hour_filter=None):
    """S2 edge fade requiring `pen` points of penetration beyond the level."""
    h, l, c = bars["h"], bars["l"], bars["c"]
    out = []
    for n, (a, b) in enumerate(zip(st, sp)):
        R = float(Rs[n])
        risk = strat.STOP_F * R
        if risk < strat.MIN_STOP_PTS:
            continue
        H, L, C = h[a:b], l[a:b], c[a:b]
        if len(H) < 30:
            continue
        T = tod[a:b] if tod is not None else None
        k = np.floor(C / R).astype(np.int64)
        lo_k, hi_k = int(k.min()), int(k.max())

        events = []
        for kk in range(lo_k, hi_k + 2):
            edge = R * kk
            # a fill needs price to reach edge -/+ pen on the far side of the
            # approach, so the order is genuinely traded through
            for i in np.flatnonzero((L <= edge) & (H >= edge)):
                events.append((int(i), edge))
        events.sort()

        used, last = 0, -999
        for i, edge in events:
            if used >= strat.MAX_PER_SESSION:
                break
            if i - last < 30:
                continue
            if hour_filter is not None and T is not None and not hour_filter(T[i]):
                continue
            j = max(0, i - 5)
            if C[j] == edge:
                continue
            from_below = C[j] < edge
            is_long = not from_below
            # penetration requirement: price must trade through the level
            if from_below:
                if H[i] < edge + pen:
                    continue
            else:
                if L[i] > edge - pen:
                    continue
            stop = edge - risk if is_long else edge + risk
            target = edge + risk if is_long else edge - risk
            out.append(strat._trade(H[i:], L[i:], C[i:], edge, stop, target, is_long, risk))
            used += 1
            last = i
    return out


def trailing_R(bars, st, sp, f, lookback=20):
    h, l = bars["h"], bars["l"]
    rng = np.array([h[a:b].max() - l[a:b].min() for a, b in zip(st, sp)])
    out = np.empty(len(rng))
    for i in range(len(rng)):
        prev = rng[max(0, i - lookback):i]
        out[i] = f * (np.median(prev) if len(prev) >= 5 else np.median(rng[:20]))
    return out


def main():
    bars = core.load()
    st, sp, dates = core.session_slices(bars, "RTH")
    yrs = dates // 10000
    n = len(st)
    tod = bars["tod"]
    res = {}

    configs = [("fixed R=197", np.full(n, 197.0)),
               ("vol f=0.50", trailing_R(bars, st, sp, 0.50)),
               ("vol f=0.60", trailing_R(bars, st, sp, 0.60))]

    # ------------------------------------------------ 1. fill penetration
    print("=== 1. fill realism: require PEN points through the level ===")
    print("  %-12s %5s %7s %6s %8s %7s %8s" % ("config", "pen", "n", "win%", "exp_pts", "t", "total"))
    pen_rows = []
    for label, Rs in configs:
        for pen in (0.0, 1.0, 2.0, 3.0, 5.0):
            s = strat.stats(s2_pen(bars, st, sp, Rs, pen))
            if not s.get("n"):
                continue
            pen_rows.append(dict(config=label, pen=pen, **s))
            print("  %-12s %5.1f %7d %5.1f%% %8.2f %7.2f %8.0f"
                  % (label, pen, s["n"], s["win_rate"] * 100, s["exp_pts"],
                     s["t_stat"], s["total_pts"]))
        print()
    res["pen"] = pen_rows

    # ------------------------------------------------ 2. time of day
    print("=== 2. time of day (vol f=0.60, pen=2) ===")
    print("  %-14s %7s %6s %8s %7s" % ("window", "n", "win%", "exp_pts", "t"))
    Rs = trailing_R(bars, st, sp, 0.60)
    tod_rows = []
    buckets = [("09:30-10:30", lambda t: 930 <= t < 1030),
               ("10:30-11:30", lambda t: 1030 <= t < 1130),
               ("11:30-13:00", lambda t: 1130 <= t < 1300),
               ("13:00-14:30", lambda t: 1300 <= t < 1430),
               ("14:30-16:00", lambda t: 1430 <= t < 1600)]
    for name, fn in buckets:
        s = strat.stats(s2_pen(bars, st, sp, Rs, 2.0, tod=tod, hour_filter=fn))
        if not s.get("n"):
            continue
        tod_rows.append(dict(window=name, **s))
        print("  %-14s %7d %5.1f%% %8.2f %7.2f"
              % (name, s["n"], s["win_rate"] * 100, s["exp_pts"], s["t_stat"]))
    res["tod"] = tod_rows

    # ------------------------------------------------ 3. recommended config
    print("\n=== 3. recommended: vol f=0.60, pen=2, RTH ===")
    trades = s2_pen(bars, st, sp, Rs, 2.0)
    s = strat.stats(trades)
    pnl = np.array([t["pnl"] for t in trades])
    eq = np.cumsum(pnl)
    for k, v in sorted(s.items()):
        print("  %-12s %s" % (k, ("%.4f" % v) if isinstance(v, float) else v))
    res["recommended"] = {"stats": s, "equity": eq.tolist(),
                          "pnl": pnl.tolist(), "med_R": float(np.median(Rs))}

    # per-year for the recommended config
    print("\n  per year:")
    yr_rows = []
    for y in np.unique(yrs):
        m = yrs == y
        sy = strat.stats(s2_pen(bars, st[m], sp[m], Rs[m], 2.0))
        if not sy.get("n"):
            continue
        yr_rows.append(dict(year=int(y), **sy))
        print("    %d  n=%-5d win %.1f%%  exp %+.2f  t %+.2f  total %+.0f"
              % (y, sy["n"], sy["win_rate"] * 100, sy["exp_pts"], sy["t_stat"], sy["total_pts"]))
    res["recommended_year"] = yr_rows

    with open(os.path.join(core.HERE, "fill.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print("\nwrote fill.json")


if __name__ == "__main__":
    main()
