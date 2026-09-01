"""Is the whole level-reaction result just long-side drift?

stack.py produced a table with one shape and one shape only: every long setup
positive, every short setup negative, at both R values, under every filter,
under every stop/target pair. break_up +0.23 / break_dn -0.79. reject_dn +0.44
/ reject_up -1.44. The "quiet" filter did not change that pattern, it doubled
it -- quiet bars resolve slowly, so they hold longer.

If a level carried information, the two sides would be mirror images. Instead
the split is by DIRECTION, which is what index drift looks like.

The control: take the same stop/target geometry, the same holding horizon, the
same ATR scaling, and fire it at RANDOM times with no reference to any level.
If random longs earn what signal longs earn and random shorts lose what signal
shorts lose, then every number in stack.py is the S&P/NQ risk premium seen
through a stop, and the Goldbach level contributed nothing.
"""
import json
import os

import numpy as np

import stack

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    o, h, l, c, v = (np.asarray(npz[k]).astype(np.float64)
                     for k in ("o", "h", "l", "c", "v"))
    date = np.asarray(npz["date"]); hh = np.asarray(npz["hh"])
    mm = np.asarray(npz["mm"])

    start, end = stack.htf_index(date, hh, mm, 30)
    bo, bh, bl, bc, bv = stack.bucket_ohlc(o, h, l, c, v, start, end)
    a30 = stack.atr(bh, bl, bc, 20)
    good = np.flatnonzero(np.isfinite(a30) & (a30 > 0) & (end + 1 < len(c)))

    rng = np.random.default_rng(17)
    pick = rng.choice(good, size=30000, replace=False)
    ei = end[pick] + 1
    px = c[end[pick]]
    aa = a30[pick]
    days = date[end[pick]]

    print("30,000 random 30-minute bars, no level involved, same geometry\n")
    print("  %-9s %-6s %6s %7s %10s   %s"
          % ("stop/tgt", "side", "n", "win", "net/trade", "95% CI"))
    out = {}
    rb = np.random.default_rng(23)
    for stop_a, tgt_a in ((0.75, 1.5), (1.0, 1.0), (0.75, 2.25)):
        for side_s, nm in ((+1.0, "long"), (-1.0, "short")):
            s = np.full(len(ei), side_s)
            stop = px - s * stop_a * aa
            tgt = px + s * tgt_a * aa
            pnl = stack.race(h, l, ei, s, px, stop, tgt)
            gd = np.isfinite(pnl)
            lo, hi = stack.boot(pnl[gd], days[gd], rb)
            out["%.2f/%.2f|%s" % (stop_a, tgt_a, nm)] = {
                "n": int(gd.sum()), "mean": float(pnl[gd].mean()),
                "win": float((pnl[gd] > 0).mean()),
                "lo": float(lo), "hi": float(hi)}
            print("  %-9s %-6s %6s %7.3f %+10.3f   [%+.2f, %+.2f]"
                  % ("%.2f/%.2f" % (stop_a, tgt_a), nm,
                     "{:,}".format(int(gd.sum())), (pnl[gd] > 0).mean(),
                     pnl[gd].mean(), lo, hi))

    print()
    print("=" * 88)
    print("SIDE BY SIDE -- signal at a Goldbach level vs a coin flip")
    print("=" * 88)
    sj = json.load(open(os.path.join(HERE, "stack.json")))
    print("  %-9s %-6s %12s %12s %10s"
          % ("stop/tgt", "side", "at GB level", "random time", "difference"))
    for stop_a, tgt_a in ((0.75, 1.5), (1.0, 1.0), (0.75, 2.25)):
        tag = "%.2f/%.2f" % (stop_a, tgt_a)
        for side_s, nm, keys in (
                (+1, "long", ["243|all|%s|break_up" % tag,
                              "243|all|%s|reject_dn" % tag]),
                (-1, "short", ["243|all|%s|break_dn" % tag,
                               "243|all|%s|reject_up" % tag])):
            sig = float(np.mean([sj[k]["true"] for k in keys if k in sj]))
            ran = out["%s|%s" % (tag, nm)]["mean"]
            print("  %-9s %-6s %+12.3f %+12.3f %+10.3f"
                  % (tag, nm, sig, ran, sig - ran))

    json.dump(out, open(os.path.join(HERE, "drift.json"), "w"), indent=1)
    print("\nwrote drift.json")


if __name__ == "__main__":
    main()
