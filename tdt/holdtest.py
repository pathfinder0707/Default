"""Is 7 special, and what does a fixed-time hold actually pay?

Two questions the parameter sweep raised but could not answer.

First: the sweep's strongest survivor was `reach 7, follow` on classic
counting, and classic counting numbers every candle, so "the count reaches 7"
is arithmetically identical to "six candles after the pivot". The contrast
against a plain origin+6 entry came out at exactly +0.0000R, t=+0.00 -- not
close to zero, the same trades. So the question is whether the offset 6 is
special or whether the whole neighbourhood pays the same. If the curve runs
smooth through 6, the number 7 is decoration on a time delay.

Second: strip the stop and the target out entirely. Enter on the signal, hold
a fixed number of candles, exit at the close. Nothing survives except the
signal's directional content, and drawdown and profit can be read straight off
the equity curve.

Overlap matters here. Signals fire faster than trades close, so the headline
figures are non-overlapping -- a new signal is skipped while a position is
open -- which is what one account can actually trade. The overlapping series
is reported alongside for comparison.
"""
import numpy as np

import sweep
import tdtcore

POINT_VALUE = 20.0        # NQ: $20 per index point
COST_PTS = sweep.COST_PTS


def fixed_hold(xb, x0, td, hold, cost=COST_PTS):
    """Enter at the open of x0, exit at the close `hold` bars later."""
    xn = len(xb["c"])
    ok = (x0 + hold) < xn
    x0, td = x0[ok], td[ok]
    entry = xb["o"][x0]
    exit_px = xb["c"][x0 + hold]
    pts = (exit_px - entry) * td - cost
    return x0, pts


def non_overlapping(x0, pts, hold):
    """Keep only signals that fire while flat, in time order."""
    order = np.argsort(x0, kind="stable")
    x0, pts = x0[order], pts[order]
    keep, free = [], -1
    for i, b in enumerate(x0.tolist()):
        if b >= free:
            keep.append(i)
            free = b + hold
    keep = np.array(keep, np.int64)
    return x0[keep], pts[keep]


def curve_stats(pts):
    """Equity statistics on a sequence of per-trade point results."""
    if len(pts) < 10:
        return None
    eq = np.cumsum(pts)
    peak = np.maximum.accumulate(np.concatenate([[0.0], eq]))
    dd = peak - np.concatenate([[0.0], eq])
    wins, losses = pts[pts > 0], pts[pts <= 0]
    sd = pts.std(ddof=1)
    return {
        "n": int(len(pts)),
        "total_pts": float(eq[-1]),
        "mean_pts": float(pts.mean()),
        "win_rate": float((pts > 0).mean()),
        "t": float(pts.mean() / (sd / np.sqrt(len(pts)))) if sd > 0 else float("nan"),
        "max_dd_pts": float(dd.max()),
        "pf": float(wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() else float("inf"),
        "total_usd": float(eq[-1] * POINT_VALUE),
        "max_dd_usd": float(dd.max() * POINT_VALUE),
        "ret_dd": float(eq[-1] / dd.max()) if dd.max() > 0 else float("nan"),
        "equity": [round(float(v), 1) for v in eq[::max(1, len(eq) // 300)]],
    }


def signals_at_offset(bars, k, offset, follow=True):
    """Every confirmed swing pivot, entered `offset` candles later.

    This is exactly what a classic count of offset+1 selects, with the count
    removed, which is the point of the comparison.
    """
    pi, pd = sweep.pivots(bars, k)
    ends = pi + offset
    keep = ends < len(bars["c"]) - 1
    return pi[keep], pd[keep] * (1 if follow else -1), ends[keep]


def run(tf="M15", k=6, mode="classic", follow=True, from_year=2016):
    raw = tdtcore.load(from_year=from_year)
    bars = tdtcore.resample(raw, tf)
    em = tdtcore.exec_map(raw, tf, sweep.EXEC_OF[tf])
    yrs = raw["yr"][em["bars"]["src"]]
    return raw, bars, em, yrs


def _stop_target_stats(bars, em, yrs, k, offset, years, rr=3.0, timeout=20, pad=0.25):
    """The candidate rule at an arbitrary entry offset, with stop and target."""
    so, td, se = signals_at_offset(bars, k, offset, follow=True)
    ec = np.maximum(se, so + k)
    keep = ec < len(bars["c"]) - 1
    so, td, ec = so[keep], td[keep], ec[keep]
    segs = sweep.segment_extremes(bars, so, ec)
    buf = pad * segs["atr"]
    stop = np.where(td == sweep.UP, segs["seg_lo"] - buf, segs["seg_hi"] + buf)
    cfg = {"rr": rr, "timeout": timeout, "pad": pad, "k": k}
    st = sweep.evaluate({"entry_i": ec + 1, "dir": td, "stop": stop},
                        em["bars"], em["xmap"], cfg, COST_PTS, yrs, years)
    if st:
        st.pop("_r", None)
    return st


def _rule_nonoverlap(bars, em, yrs, k, offset, years, rr=3.0, timeout=20, pad=0.25):
    """The peak rule, taking only trades that open while flat."""
    so, td, se = signals_at_offset(bars, k, offset, follow=True)
    ec = np.maximum(se, so + k)
    keep = ec < len(bars["c"]) - 1
    so, td, ec = so[keep], td[keep], ec[keep]
    segs = sweep.segment_extremes(bars, so, ec)
    buf = pad * segs["atr"]
    stop = np.where(td == sweep.UP, segs["seg_lo"] - buf, segs["seg_hi"] + buf)

    x0 = em["xmap"][ec + 1]
    yr = yrs[np.clip(x0, 0, len(yrs) - 1)]
    sel = (yr >= years[0]) & (yr <= years[1])
    x0, td, stop = x0[sel], td[sel], stop[sel]
    entry = em["bars"]["o"][x0]
    risk = np.abs(entry - stop)
    g = (risk > 0) & np.isfinite(risk) & (((entry - stop) * td) > 0)
    x0, td, stop, entry, risk = x0[g], td[g], stop[g], entry[g], risk[g]
    if len(x0) < 50:
        return None
    target = entry + td * rr * risk
    _, ei, px = sweep.simulate_vec(em["bars"], x0, td, stop, target, timeout)
    pts = (px - entry) * td - COST_PTS

    order = np.argsort(x0, kind="stable")
    keep_i, free = [], -1
    for i in order.tolist():
        if x0[i] >= free:
            keep_i.append(i)
            free = ei[i]
    p = pts[np.array(keep_i)]
    st = curve_stats(p)
    if st:
        st["r_mean"] = float((p / risk[np.array(keep_i)]).mean())
    return st


# ------------------------------------------------------------------- driver
def main():
    import json
    import os

    HERE = os.path.dirname(os.path.abspath(__file__))
    TF, HOLD = "M15", 20
    raw = tdtcore.load(from_year=2016)
    bars = tdtcore.resample(raw, TF)
    em = tdtcore.exec_map(raw, TF, sweep.EXEC_OF[TF])
    yrs = raw["yr"][em["bars"]["src"]]

    def build(k, off, follow):
        so, td, se = signals_at_offset(bars, k, off, follow=follow)
        ec = np.maximum(se, so + k) + 1
        ok = ec < len(bars["c"]) - 1
        return em["xmap"][ec[ok]], td[ok]

    def period(x0, d, years, hold):
        yr = yrs[np.clip(x0, 0, len(yrs) - 1)]
        sel = (yr >= years[0]) & (yr <= years[1])
        xx, pts = fixed_hold(em["bars"], x0[sel], d[sel], hold)
        xx, pts = non_overlapping(xx, pts, hold)
        return curve_stats(pts)

    out = {"meta": {"tf": TF, "hold": HOLD, "cost_pts": COST_PTS,
                    "point_value": POINT_VALUE,
                    "train": [2016, 2022], "test": [2023, 2026]},
           "offset": {}, "hold": {}, "split": {}}

    for k in (2, 6):
        # offset neighbourhood: is TDT's number better than the ones beside it?
        rows = []
        for off in range(k, 25):
            x0, d = build(k, off, True)
            for lbl, yy in (("train", (2016, 2022)), ("test", (2023, 2026))):
                st = period(x0, d, yy, HOLD)
                if st:
                    rows.append({"offset": off, "count": off + 1, "period": lbl,
                                 **{kk: v for kk, v in st.items() if kk != "equity"}})
        out["offset"][str(k)] = rows

        # hold-duration curve on TDT's own count 7
        x0, d = build(k, 6, True)
        hrows = []
        for h in (2, 4, 8, 12, 20, 30, 50, 80, 120):
            for lbl, yy in (("train", (2016, 2022)), ("test", (2023, 2026))):
                st = period(x0, d, yy, h)
                if st:
                    hrows.append({"hold": h, "period": lbl,
                                  **{kk: v for kk, v in st.items() if kk != "equity"}})
        out["hold"][str(k)] = hrows

        # the split that matters: same rule, both periods, both polarities
        sp = {}
        for pol, fol in (("follow", True), ("fade", False)):
            xx, dd = build(k, 6, fol)
            for lbl, yy in (("train", (2016, 2022)), ("test", (2023, 2026))):
                st = period(xx, dd, yy, HOLD)
                if st:
                    sp["%s|%s" % (pol, lbl)] = st
        out["split"][str(k)] = sp

    # The decisive scan: for each swing strength, where does the edge peak?
    # If it peaks on TDT's 7 regardless of k, the number means something. If it
    # tracks k, the number is an artefact of the pivot filter -- offsets below k
    # are masked because the pivot is not knowable yet, so they collapse onto k.
    kscan = []
    for kk in (2, 3, 4, 6, 8):
        for off in range(1, 13):
            st = _stop_target_stats(bars, em, yrs, kk, off, (2023, 2026))
            if st:
                kscan.append({"k": kk, "offset": off, "count": off + 1,
                              "t": st["t"], "n": st["n"], "exp_r": st["exp_r"],
                              "masked": off < kk})
    out["kscan"] = kscan

    # What the rule at the peak actually pays when only one position is held at
    # a time -- the overlapping series counts concurrent trades that a single
    # account cannot take, so this is the tradeable figure.
    out["rule"] = {}
    for kk in (4, 6, 8):
        for lbl, yy in (("train", (2016, 2022)), ("test", (2023, 2026))):
            r = _rule_nonoverlap(bars, em, yrs, kk, kk, yy)
            if r:
                out["rule"]["%d|%s" % (kk, lbl)] = r

    with open(os.path.join(HERE, "HOLD.json"), "w") as fh:
        json.dump(out, fh, separators=(",", ":"), default=float)
    print("wrote HOLD.json")
    for k in ("2", "6"):
        for key, st in out["split"][k].items():
            print("  k=%s %-14s n=%5d mean %+6.2f pts  total $%s  maxDD $%s  t=%+.2f"
                  % (k, key, st["n"], st["mean_pts"],
                     format(round(st["total_usd"]), ","),
                     format(round(st["max_dd_usd"]), ","), st["t"]))
    return out


if __name__ == "__main__":
    main()
