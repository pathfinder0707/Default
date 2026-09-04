"""Run the whole TDT study and write ALL.json.

  python run_all.py                 real bars, D1 counts   (needs bars.npz)
  python run_all.py --tf H4         real bars, H4 counts
  python run_all.py --synthetic     a random walk, no data needed

The synthetic mode exists so the pipeline and the report can be exercised
without the feed, and everything it produces is stamped synthetic:true and
banner-flagged in the report. A random walk has no TDT structure in it by
construction, so those numbers are a test of the plumbing and a null for the
method -- never a result about the market.
"""
import argparse
import json
import os
import time

import numpy as np

import backtest
import counting
import models
import nulltest
import tdtcore

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "ALL.json")


def synthetic(n=4000, seed=4, drift=0.0):
    """A driftless random walk with candle bodies -- structure-free by design.

    Built directly at the study timeframe rather than resampled up from
    minutes: the point is to have enough candles to count, not to imitate a
    session clock. n is the candle count the study actually sees.
    """
    rng = np.random.default_rng(seed)
    c = np.cumsum(rng.normal(drift, 1.0, n)) + 15000.0
    o = np.r_[c[0], c[:-1]]
    wick = rng.uniform(0.1, 1.4, n)
    h = np.maximum(o, c) + wick * rng.uniform(0, 1, n)
    l = np.minimum(o, c) - wick * rng.uniform(0, 1, n)
    return {"o": o, "h": h, "l": l, "c": c,
            "ts": np.arange(n, dtype=np.int64),
            "src": np.arange(n), "n": np.ones(n, np.int64)}


def describe(bars, tf, source):
    return {"source": source, "tf": tf, "bars": int(len(bars["c"])),
            "first_ts": int(bars["ts"][0]) if "ts" in bars else None,
            "last_ts": int(bars["ts"][-1]) if "ts" in bars else None,
            "built": time.strftime("%Y-%m-%d %H:%M:%S"),
            "key_counts": list(tdtcore.KEY_COUNTS)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--synthetic", action="store_true",
                    help="run on a random walk instead of bars.npz")
    ap.add_argument("--tf", default="D1", choices=sorted(tdtcore.TF_MINUTES),
                    help="timeframe the counts run on (default D1)")
    ap.add_argument("--k", type=int, default=3, help="swing strength for legs")
    ap.add_argument("--ks", default="5,3,2",
                    help="three swing strengths for Model #3, coarsest first")
    ap.add_argument("--tol", type=int, default=1,
                    help="how far a terminal count may sit from 7/13/21")
    ap.add_argument("--horizon", type=int, default=10,
                    help="forward bars for the grade test")
    ap.add_argument("--cost", type=float, default=0.0,
                    help="points charged per round turn")
    ap.add_argument("--exec-tf", default=None, choices=sorted(tdtcore.TF_MINUTES),
                    help="finer timeframe to resolve entries/stops/targets on "
                         "(Model #2 teaches D1 counts with H1 execution)")
    ap.add_argument("--from-year", type=int, default=2016,
                    help="first year to include; the NQ feed's session coverage "
                         "ramps from under 2h/day in 2010 to 23h/day by 2022, so "
                         "earlier daily candles are not comparable (default 2016)")
    ap.add_argument("--to-year", type=int, default=None)
    ap.add_argument("--n", type=int, default=4000,
                    help="candles to generate in --synthetic mode")
    ap.add_argument("--out", default=OUT)
    args = ap.parse_args()

    ks = tuple(int(x) for x in args.ks.split(","))
    if len(ks) != 3:
        raise SystemExit("--ks needs exactly three strengths, got %r" % args.ks)

    exec_bars = None
    if args.synthetic:
        # already at the study timeframe; resampling a structure-free walk
        # would only shrink the sample for nothing.
        bars = synthetic(args.n)
        source = "synthetic random walk (no market data)"
        if args.exec_tf:
            raise SystemExit("--exec-tf needs real bars; it has no meaning on a "
                             "synthetic series generated at one timeframe")
    else:
        raw = tdtcore.load(from_year=args.from_year, to_year=args.to_year)
        bars = tdtcore.resample(raw, args.tf)
        source = "bars.npz"
        if args.exec_tf and args.exec_tf != args.tf:
            exec_bars = tdtcore.exec_map(raw, args.tf, args.exec_tf)
    meta = describe(bars, "synthetic" if args.synthetic else args.tf, source)
    meta["synthetic"] = bool(args.synthetic)
    meta["k"] = args.k
    meta["ks"] = list(ks)
    meta["tol"] = args.tol
    meta["cost"] = args.cost
    meta["exec_tf"] = args.exec_tf if exec_bars else args.tf
    meta["from_year"] = None if args.synthetic else args.from_year
    meta["to_year"] = None if args.synthetic else args.to_year
    if exec_bars:
        meta["exec_bars"] = int(len(exec_bars["bars"]["c"]))
    print("%s  %s  %s candles on %s%s"
          % ("SYNTHETIC" if args.synthetic else "real", source,
             "{:,}".format(meta["bars"]), args.tf,
             ("  (execution on %s, %s candles)"
              % (args.exec_tf, "{:,}".format(meta["exec_bars"]))) if exec_bars else ""))

    t0 = time.time()
    print("counting legs ...")
    leg_summary = {}
    for mode in counting.MODES:
        lgs = models.legs(bars, k=args.k, mode=mode, tol=args.tol)
        term = np.array([lg.terminal for lg in lgs], np.int64) if lgs else np.array([0])
        leg_summary[mode] = {
            "legs": len(lgs),
            "keyed": sum(1 for lg in lgs if lg.key),
            "mean_terminal": float(term.mean()),
            "median_terminal": float(np.median(term)),
            "hist": np.bincount(np.clip(term, 0, 40), minlength=41).tolist(),
        }
        print("  %-8s %5d legs, %4d terminate near a key count, median %d"
              % (mode, len(lgs), leg_summary[mode]["keyed"],
                 leg_summary[mode]["median_terminal"]))

    print("null tests ...")
    nulls = nulltest.run(bars, k=args.k, ks=ks, horizon=args.horizon,
                         exec_bars=exec_bars, tol=args.tol)
    for mode in counting.MODES:
        for row in nulls["neighbour"][mode]:
            if np.isfinite(row.get("z", float("nan"))):
                print("  %-8s count %2d  hazard %.3f  vs neighbours %.3f  z=%+.2f  (%d at risk)"
                      % (mode, row["key"], row["hazard"], row["baseline"],
                         row["z"], row["at_risk"]))

    print("does the count select better legs? ...")
    for mode in counting.MODES:
        ft = nulls["filter"][mode]
        by = {r["set"]: r for r in ft["rows"]}
        c = ft.get("contrast", {})
        print("  %-8s tdt %+.4fR (n=%d)  every leg %+.4fR (n=%d)  "
              "rejects %+.4fR (n=%d)  diff t=%s"
              % (mode, by["tdt"]["exp_r"], by["tdt"]["n"],
                 by["all"]["exp_r"], by["all"]["n"],
                 by["rejected"]["exp_r"], by["rejected"]["n"],
                 ("%+.2f" % c["t"]) if "t" in c else "n/a"))
        print("           -> %s" % ft["verdict"])

    print("backtest ...")
    bt = backtest.run(bars, k=args.k, ks=ks, cost=args.cost, tol=args.tol,
                      exec_bars=exec_bars, exec_tf=meta["exec_tf"])
    for mode in counting.MODES:
        s = bt["model2"][mode]["stats"]
        if s.get("n"):
            print("  model2 %-8s n=%4d  win %.3f  exp %+.3fR  t=%+.2f"
                  % (mode, s["n"], s["win_rate"], s["exp_r"], s["t"]))
    for mode in counting.MODES:
        for row in bt["model3"][mode]["by_verdict"]:
            print("  model3 %-8s %-13s n=%4d  win %.3f  exp %+.3fR  t=%+.2f"
                  % (mode, row["value"], row["n"], row["win_rate"],
                     row["exp_r"], row["t"]))

    payload = {"meta": meta, "legs": leg_summary, "null": nulls, "backtest": bt}
    with open(args.out, "w") as fh:
        json.dump(payload, fh, separators=(",", ":"), default=float)
    print("\nwrote %s (%.0f KB) in %.1fs"
          % (args.out, os.path.getsize(args.out) / 1024, time.time() - t0))


if __name__ == "__main__":
    main()
