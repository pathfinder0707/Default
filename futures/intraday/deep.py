"""Does the S2 plateau survive the checks that kill most backtest results?

1. Phase null      -- shift the lattice origin. If the edge fade works equally
                      at every phase, the lattice is doing nothing and what is
                      left is generic mean reversion at a bracket size.
2. Per year        -- an edge that lives in 2023 and dies in 2026 is not an edge.
3. Cost            -- 0.5 / 1 / 2 / 3 points round trip.
4. Random time     -- same trade count and bracket, entries at random bars,
                      direction fading the same 5-bar move. Tells us how much
                      the LEVEL adds over the timing rule alone.
5. Volatility scale-- R set from trailing realized range instead of a constant,
                      since NQ's daily range doubled across the sample.
"""
import json
import os

import numpy as np

import core
import strat

RNG = np.random.default_rng(11)
NPHASE = 20
R_FOCUS = [123.0, 156.0, 197.0, 243.0, 729.0]


def run_s2(bars, st, sp, Rs, phases=None):
    """S2 with a per-session R (and optional per-session phase)."""
    out = []
    for n, (a, b) in enumerate(zip(st, sp)):
        R = float(Rs[n])
        ph = 0.0 if phases is None else float(phases[n])
        out += strat.s2_edge_fade(bars, [a], [b], R, ph)
    return out


def s2_random_time(bars, st, sp, Rs, n_per_session=3):
    """Control: same bracket, same fade-the-5-bar-move rule, random entry bars."""
    h, l, c = bars["h"], bars["l"], bars["c"]
    out = []
    for n, (a, b) in enumerate(zip(st, sp)):
        R = float(Rs[n])
        risk = strat.STOP_F * R
        if risk < strat.MIN_STOP_PTS:
            continue
        H, L, C = h[a:b], l[a:b], c[a:b]
        if len(H) < 60:
            continue
        picks = np.sort(RNG.choice(np.arange(10, len(H) - 5), size=n_per_session, replace=False))
        last = -999
        for i in picks:
            i = int(i)
            if i - last < 30:
                continue
            j = max(0, i - 5)
            entry = C[i]
            if C[j] == entry:
                continue
            is_long = not (C[j] < entry)
            stop = entry - risk if is_long else entry + risk
            target = entry + risk if is_long else entry - risk
            out.append(strat._trade(H[i + 1:], L[i + 1:], C[i + 1:], entry,
                                    stop, target, is_long, risk))
            last = i
    return out


def trailing_range_R(bars, st, sp, f, lookback=20):
    """Per-session R = f x trailing median RTH range (previous sessions only)."""
    h, l = bars["h"], bars["l"]
    rng = np.array([h[a:b].max() - l[a:b].min() for a, b in zip(st, sp)])
    out = np.empty(len(rng))
    for i in range(len(rng)):
        prev = rng[max(0, i - lookback):i]
        out[i] = f * (np.median(prev) if len(prev) >= 5 else np.median(rng[:20]))
    return out, rng


def main():
    bars = core.load()
    st, sp, dates = core.session_slices(bars, "RTH")
    yrs = dates // 10000
    n = len(st)
    res = {}

    # ---------------------------------------------------------- 1. phase null
    print("=== 1. phase null: does the lattice origin matter? ===")
    print("  %-7s %7s %8s %9s   %-28s" % ("R", "n", "exp_pts", "t", "phase null (20 origins)"))
    phase_rows = []
    for R in R_FOCUS:
        Rs = np.full(n, R)
        true = strat.stats(run_s2(bars, st, sp, Rs))
        nulls = []
        for j in range(1, NPHASE):
            ph = np.full(n, j * 100.0 / NPHASE)
            nulls.append(strat.stats(run_s2(bars, st, sp, Rs, ph)).get("exp_pts", np.nan))
        nulls = np.array([x for x in nulls if np.isfinite(x)])
        z = (true["exp_pts"] - nulls.mean()) / nulls.std(ddof=1) if len(nulls) > 2 else float("nan")
        rank = int((nulls >= true["exp_pts"]).sum() + 1)
        phase_rows.append({"R": R, "n": true["n"], "exp_pts": true["exp_pts"],
                           "t": true["t_stat"], "null_mean": float(nulls.mean()),
                           "null_sd": float(nulls.std(ddof=1)), "z": float(z),
                           "rank": rank, "nulls": nulls.tolist()})
        print("  %-7.0f %7d %8.2f %9.2f   mean %6.2f  sd %5.2f  z %+5.2f  rank %2d/20"
              % (R, true["n"], true["exp_pts"], true["t_stat"],
                 nulls.mean(), nulls.std(ddof=1), z, rank))
    res["phase"] = phase_rows

    # ---------------------------------------------------------- 2. per year
    print("\n=== 2. per year ===")
    print("  %-7s %6s %7s %7s %8s %7s %8s" % ("R", "year", "n", "win%", "exp_pts", "t", "total"))
    year_rows = []
    for R in R_FOCUS:
        Rs = np.full(n, R)
        for y in np.unique(yrs):
            m = yrs == y
            s = strat.stats(run_s2(bars, st[m], sp[m], Rs[m]))
            if not s.get("n"):
                continue
            year_rows.append(dict(R=R, year=int(y), **s))
            print("  %-7.0f %6d %7d %6.1f%% %8.2f %7.2f %8.0f"
                  % (R, y, s["n"], s["win_rate"] * 100, s["exp_pts"], s["t_stat"], s["total_pts"]))
    res["year"] = year_rows

    # ---------------------------------------------------------- 3. cost
    print("\n=== 3. cost sensitivity (points round trip) ===")
    print("  %-7s %8s %8s %8s %8s" % ("R", "0.5", "1.0", "2.0", "3.0"))
    cost_rows = []
    base = strat.COST
    for R in R_FOCUS:
        Rs = np.full(n, R)
        cells, row = [], {"R": R}
        for cst in (0.5, 1.0, 2.0, 3.0):
            strat.COST = cst
            s = strat.stats(run_s2(bars, st, sp, Rs))
            row["c%.1f" % cst] = s.get("exp_pts", float("nan"))
            cells.append("%8.2f" % s.get("exp_pts", float("nan")))
        strat.COST = base
        cost_rows.append(row)
        print("  %-7.0f %s" % (R, "".join(cells)))
    res["cost"] = cost_rows

    # ---------------------------------------------------------- 4. random time
    print("\n=== 4. random-time control (level replaced by a random bar) ===")
    print("  %-7s %8s %8s   %8s %8s" % ("R", "lvl exp", "lvl t", "rand exp", "rand t"))
    rand_rows = []
    for R in R_FOCUS:
        Rs = np.full(n, R)
        lv = strat.stats(run_s2(bars, st, sp, Rs))
        rd = strat.stats(s2_random_time(bars, st, sp, Rs))
        rand_rows.append({"R": R, "lvl_exp": lv.get("exp_pts"), "lvl_t": lv.get("t_stat"),
                          "rand_exp": rd.get("exp_pts"), "rand_t": rd.get("t_stat"),
                          "rand_n": rd.get("n")})
        print("  %-7.0f %8.2f %8.2f   %8.2f %8.2f"
              % (R, lv.get("exp_pts", 0), lv.get("t_stat", 0),
                 rd.get("exp_pts", 0), rd.get("t_stat", 0)))
    res["random"] = rand_rows

    # ------------------------------------------------- 5. volatility-scaled R
    print("\n=== 5. R scaled to trailing 20-day median range ===")
    print("  %-6s %8s %7s %7s %8s %7s   %s" % ("f", "med R", "n", "win%", "exp_pts", "t", "per-year exp_pts"))
    vol_rows = []
    for f in (0.25, 0.4, 0.5, 0.6, 0.75, 1.0, 1.5):
        Rs, rng = trailing_range_R(bars, st, sp, f)
        s = strat.stats(run_s2(bars, st, sp, Rs))
        if not s.get("n"):
            continue
        peryr = []
        for y in np.unique(yrs):
            m = yrs == y
            sy = strat.stats(run_s2(bars, st[m], sp[m], Rs[m]))
            peryr.append((int(y), sy.get("exp_pts", float("nan")), sy.get("n", 0)))
        vol_rows.append({"f": f, "med_R": float(np.median(Rs)), **s,
                         "per_year": [{"year": a, "exp_pts": b, "n": c} for a, b, c in peryr]})
        print("  %-6.2f %8.0f %7d %6.1f%% %8.2f %7.2f   %s"
              % (f, np.median(Rs), s["n"], s["win_rate"] * 100, s["exp_pts"], s["t_stat"],
                 "  ".join("%d:%+6.2f" % (a, b) for a, b, _ in peryr)))
    res["vol"] = vol_rows

    with open(os.path.join(core.HERE, "deep.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print("\nwrote deep.json")


if __name__ == "__main__":
    main()
