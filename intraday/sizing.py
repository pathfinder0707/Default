"""Which PO3 size matches which intraday timeframe -- and how much it drifts.

Purely descriptive. No hypothesis, no null. This is the sizing table a trader
needs before any of the structural tests mean anything.
"""
import json
import os

import numpy as np

import core

TFS = [("1m", 1), ("5m", 5), ("15m", 15), ("30m", 30), ("60m", 60), ("4h", 240)]


def agg_ranges(bars, minutes, window="RTH"):
    """Realized high-low range of every non-overlapping `minutes` block."""
    st, sp, _ = core.session_slices(bars, window)
    h, l = bars["h"], bars["l"]
    out = []
    for a, b in zip(st, sp):
        n = (b - a) // minutes * minutes
        if n <= 0:
            continue
        hh = h[a:a + n].reshape(-1, minutes).max(axis=1)
        ll = l[a:a + n].reshape(-1, minutes).min(axis=1)
        out.append(hh - ll)
    return np.concatenate(out) if out else np.array([])


def session_ranges(bars, window="RTH"):
    st, sp, dates = core.session_slices(bars, window)
    h, l = bars["h"], bars["l"]
    r = np.array([h[a:b].max() - l[a:b].min() for a, b in zip(st, sp)])
    return r, dates


def nearest_po3(x):
    """Closest power of three in log space."""
    p = np.array(core.PO3, float)
    return p[np.argmin(np.abs(np.log(x[:, None]) - np.log(p[None, :])), axis=1)]


def main():
    bars = core.load()
    res = {"timeframes": [], "sessions": [], "drift": []}

    print("=== realized range by timeframe (RTH only) ===")
    print("%-6s %8s %8s %8s %8s %8s  %s" % ("tf", "n", "p25", "median", "p75", "p90", "nearest PO3 (median)"))
    for name, m in TFS:
        r = agg_ranges(bars, m)
        if len(r) == 0:
            continue
        med = float(np.median(r))
        row = {
            "tf": name, "minutes": m, "n": int(len(r)),
            "p25": float(np.percentile(r, 25)), "median": med,
            "p75": float(np.percentile(r, 75)), "p90": float(np.percentile(r, 90)),
            "nearest_po3": float(nearest_po3(np.array([med]))[0]),
        }
        res["timeframes"].append(row)
        print("%-6s %8d %8.1f %8.1f %8.1f %8.1f  %8.0f"
              % (name, row["n"], row["p25"], med, row["p75"], row["p90"], row["nearest_po3"]))

    print("\n=== session range by window ===")
    print("%-8s %6s %8s %8s %8s  %s" % ("window", "n", "p25", "median", "p75", "nearest PO3"))
    for w in ("RTH", "NYAM", "NYPM", "LONDON", "ASIA"):
        r, _ = session_ranges(bars, w)
        if len(r) == 0:
            continue
        med = float(np.median(r))
        row = {"window": w, "n": int(len(r)), "p25": float(np.percentile(r, 25)),
               "median": med, "p75": float(np.percentile(r, 75)),
               "nearest_po3": float(nearest_po3(np.array([med]))[0])}
        res["sessions"].append(row)
        print("%-8s %6d %8.1f %8.1f %8.1f  %8.0f"
              % (w, row["n"], row["p25"], med, row["p75"], row["nearest_po3"]))

    print("\n=== the drift problem: RTH range and price level by year ===")
    print("%-6s %7s %10s %10s %10s %9s  %s"
          % ("year", "days", "med close", "med range", "range %", "nearest", "PO3 as % of price"))
    r, dates = session_ranges(bars, "RTH")
    yrs = dates // 10000
    st, sp, _ = core.session_slices(bars, "RTH")
    closes = np.array([bars["c"][b - 1] for a, b in zip(st, sp)])
    for y in np.unique(yrs):
        s = yrs == y
        med = float(np.median(r[s]))
        mc = float(np.median(closes[s]))
        npo = float(nearest_po3(np.array([med]))[0])
        row = {"year": int(y), "days": int(s.sum()), "med_close": mc,
               "med_range": med, "range_pct": med / mc * 100,
               "nearest_po3": npo, "po3_pct": npo / mc * 100}
        res["drift"].append(row)
        print("%-6d %7d %10.0f %10.1f %9.2f%% %9.0f  %.2f%%"
              % (y, row["days"], mc, med, row["range_pct"], npo, row["po3_pct"]))

    # how often does each PO3 size contain the RTH range?
    print("\n=== P(RTH range <= R), by year ===")
    hdr = "  ".join("%7d" % p for p in core.PO3)
    print("%-6s  %s" % ("year", hdr))
    cont = []
    for y in np.unique(yrs):
        s = yrs == y
        row = {"year": int(y)}
        cells = []
        for p in core.PO3:
            v = float((r[s] <= p).mean())
            row["p%d" % p] = v
            cells.append("%6.1f%%" % (v * 100))
        cont.append(row)
        print("%-6d  %s" % (y, "  ".join(cells)))
    res["containment"] = cont

    with open(os.path.join(core.HERE, "sizing.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print("\nwrote sizing.json")


if __name__ == "__main__":
    main()
