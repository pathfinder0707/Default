"""Is it confluence, or just that some Goldbach levels are better than others?

The two are entangled by construction. An R=81 level at 0% is also a 27-level
every single time, because 81 = 3 x 27; a level at 50% never is. So confluence
depth is partly determined by WHICH of the twenty levels you are looking at,
and "deep confluence rejects more" could just be "level 0 rejects more" wearing
a disguise. That would still be a lattice result, but a different and much
narrower one.

The test is a stratified one: hold the level identity fixed and ask whether
confluence still separates touches WITHIN it. If the effect is really about
which level it is, the within-level spread collapses to nothing. If confluence
survives inside single levels, it is doing work of its own.

Part two asks the only question that decides whether any of this is tradeable:
does the extra rejection show up as expectancy on the structure entry?
"""
import json
import os

import numpy as np

import gbr
import baserate as br
import controls as ct
from edge import (atr, first_hits, find_retests, structure_trade, dedup,
                  BREAK_MIN, RETEST_MAX, HORIZON, DEDUP, RMULTS, FAV, ADV, BIG)

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    L, idx, res = ct.collect()
    rej = (res == 1)
    conf5 = ct.conf_map([27, 243, 729, 2187, 6561])
    b = ct.bin_of(L)
    c = conf5[b]

    # which of the 20 levels is each touch? recover from the level price
    pct = np.round(np.mod(L, 81.0) / 81.0 * 100.0).astype(int) % 100

    print("=== stratified by level: does confluence still separate? ===")
    print("  %-7s %8s %9s %10s %10s %9s"
          % ("level", "touches", "conf seen", "low conf", "high conf", "spread"))
    rows, spreads, weights = [], [], []
    for p in sorted(set(pct.tolist())):
        m = pct == p
        if m.sum() < 2000:
            continue
        cc = c[m]
        rr = rej[m]
        seen = sorted(set(cc.tolist()))
        if len(seen) < 2:
            print("  %-7d %8s %9s %10s %10s %9s"
                  % (p, "{:,}".format(int(m.sum())), "only c=%d" % seen[0],
                     "%.4f" % rr.mean(), "-", "-"))
            rows.append({"pct": int(p), "n": int(m.sum()), "single_conf": seen[0],
                         "reject": float(rr.mean())})
            continue
        thr = np.median(cc)
        lo, hi = cc <= thr, cc > thr
        if lo.sum() < 300 or hi.sum() < 300:
            lo, hi = cc == seen[0], cc == seen[-1]
        if lo.sum() < 300 or hi.sum() < 300:
            continue
        a_, b_ = float(rr[lo].mean()), float(rr[hi].mean())
        rows.append({"pct": int(p), "n": int(m.sum()),
                     "conf_values": seen, "low": a_, "high": b_,
                     "spread": b_ - a_, "n_low": int(lo.sum()),
                     "n_high": int(hi.sum())})
        spreads.append(b_ - a_)
        weights.append(min(lo.sum(), hi.sum()))
        print("  %-7d %8s %9s %10.4f %10.4f %+8.2fpp"
              % (p, "{:,}".format(int(m.sum())),
                 ",".join(str(s) for s in seen), a_, b_, (b_ - a_) * 100))

    if spreads:
        sp = np.array(spreads); w = np.array(weights, float)
        print("\n  %d levels admit a within-level comparison" % len(sp))
        print("  weighted mean within-level spread: %+.2f pp"
              % ((sp * w).sum() / w.sum() * 100))
        print("  levels with a positive spread: %d of %d"
              % (int((sp > 0).sum()), len(sp)))

    # ---------------- does it pay? -----------------------------------------
    print("\n=== does the extra rejection become expectancy? ===")
    npz = np.load(os.path.join(HERE, "bars.npz"))
    h, l, cl = (np.asarray(npz[k]) for k in ("h", "l", "c"))
    a = atr(h, l, cl)
    n = len(cl)

    R = 81.0
    Ls, ids, ups = [], [], []
    for p in gbr.LEVELS:
        off = R * p / 100.0
        li = np.floor((cl - off) / R)
        d = np.diff(li)
        for up in (True, False):
            cr = np.flatnonzero(d > 0) + 1 if up else np.flatnonzero(d < 0) + 1
            cr = cr[(cr > 20) & (cr + RETEST_MAX + HORIZON < n)]
            cr = dedup(cr, DEDUP)
            if len(cr) == 0:
                continue
            Lk = off + R * (li[cr] if up else li[cr] + 1)
            rt, _ = find_retests(h, l, cr, Lk, a[cr], up, n)
            ok = rt >= 0
            if not ok.any():
                continue
            i = rt[ok]
            st, rk = structure_trade(h, l, cl, i, Lk[ok], a[i], up, n, RMULTS)
            Ls.append(Lk[ok]); ids.append(i)
            ups.append(np.stack([st[m] for m in RMULTS], axis=1))
    Lr = np.concatenate(Ls)
    ST = np.concatenate(ups)
    cr_ = conf5[ct.bin_of(Lr)]
    print("  %s retest trades\n" % "{:,}".format(len(Lr)))

    res2 = []
    for q, rm in enumerate(RMULTS):
        print("  target %.1fR   break-even %.3f" % (rm, 1 / (1 + rm)))
        for band, m in (("confluence 0-1", cr_ <= 1), ("confluence 2", cr_ == 2),
                        ("confluence 3+", cr_ >= 3)):
            r = ST[m, q]
            live = r != 0
            if live.sum() < 500:
                continue
            p_ = float((r[live] == 1).mean())
            evr = p_ * rm - (1 - p_)
            res2.append({"rr": rm, "band": band, "n": int(live.sum()),
                         "p": p_, "ev_r": evr})
            print("     %-16s %9s  win %.4f   EV %+.3fR"
                  % (band, "{:,}".format(int(live.sum())), p_, evr))
        print()

    json.dump({"stratified": rows, "trade": res2},
              open(os.path.join(HERE, "disentangle.json"), "w"), indent=1)
    print("wrote disentangle.json")


if __name__ == "__main__":
    main()
