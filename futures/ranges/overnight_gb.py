"""Does Goldbach improve a real edge?

The benchmark found one thing that pays with the identical machinery that
returned flat on every lattice test: holding the overnight session long earns
+5.56 points net per night, 95% CI [+2.11, +9.00], across 3,596 sessions,
positive in both halves of the sample.

That is the fair test the lattice has never been given. Every Goldbach test in
this repo has asked the lattice to BE an edge from nothing. This asks something
much easier: take an edge that already exists, and see whether knowing where
price sits in the PO3 block improves it.

If the framework is a map of where price is in a dealing range -- which is the
one description of it that has survived everything -- then the map should say
something about a position held from the RTH close to the next open. Entering
near a block extreme should differ from entering at equilibrium.

Conditioning is on the block position of the RTH CLOSE, which is the entry
price and is known before the trade is taken. Scored against shifted lattices
and split discovery / validation, same as everything else.
"""
import json
import os

import numpy as np

import gbr

HERE = os.path.dirname(os.path.abspath(__file__))
COST = 0.45
SPLIT = 2019
NPHASE = 12
NBOOT = 2000


def sessions(date, tod):
    rth = (tod >= 930) & (tod < 1600)
    u = np.unique(date[rth])
    io = np.zeros(len(u), np.int64)
    ic = np.zeros(len(u), np.int64)
    for i, d in enumerate(u):
        m = np.flatnonzero(rth & (date == d))
        io[i], ic[i] = m[0], m[-1]
    return u, io, ic


def boot(pnl, days, rng):
    u, inv = np.unique(days, return_inverse=True)
    nd = len(u)
    s = np.bincount(inv, weights=pnl, minlength=nd)
    cnt = np.bincount(inv, minlength=nd).astype(float)
    pick = rng.integers(0, nd, size=(NBOOT, nd))
    bs = s[pick].sum(1) / np.maximum(cnt[pick].sum(1), 1)
    return np.percentile(bs, [2.5, 97.5])


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    c = np.asarray(npz["c"])
    date = np.asarray(npz["date"])
    tod = np.asarray(npz["hh"]) * 100 + np.asarray(npz["mm"])
    u, io, ic = sessions(date, tod)

    entry_i = ic[:-1]                      # prior RTH close
    exit_i = io[1:]                        # next RTH open
    pnl = c[exit_i] - c[entry_i] - COST
    days = u[1:]
    yr = days // 10000
    rng = np.random.default_rng(9)

    lo, hi = boot(pnl, days, rng)
    print("overnight, unconditional: %+.3f net over %s nights   CI [%+.3f, %+.3f]"
          % (pnl.mean(), "{:,}".format(len(pnl)), lo, hi))
    print("  discovery %+.3f   validation %+.3f\n"
          % (pnl[yr < SPLIT].mean(), pnl[yr >= SPLIT].mean()))

    out = {"uncond": {"mean": float(pnl.mean()), "n": int(len(pnl)),
                      "lo": float(lo), "hi": float(hi)}}
    px = c[entry_i]

    for R in (243.0, 729.0, 2187.0):
        print("=" * 88)
        print("R=%d   conditioned on where the RTH close sits in the block" % R)
        print("=" * 88)
        print("  %-22s %7s %10s %10s %9s   %-20s"
              % ("block position", "nights", "net/night", "shifted", "vs all",
                 "95% CI (by day)"))
        out[str(int(R))] = {}

        def pos(phase):
            return np.mod(px - R * phase / 100.0, R) / R * 100.0

        p0 = pos(0.0)
        bands = [("0-10  low extreme", 0, 10), ("10-25", 10, 25),
                 ("25-40", 25, 40), ("40-60  equilibrium", 40, 60),
                 ("60-75", 60, 75), ("75-90", 75, 90),
                 ("90-100  high extreme", 90, 100)]
        for lab, a, b in bands:
            m = (p0 >= a) & (p0 < b)
            if m.sum() < 150:
                continue
            l2, h2 = boot(pnl[m], days[m], rng)
            nv = []
            for j in range(1, NPHASE):
                pj = pos(j * 100.0 / NPHASE)
                mj = (pj >= a) & (pj < b)
                if mj.sum() >= 150:
                    nv.append(float(pnl[mj].mean()))
            nm = float(np.mean(nv)) if nv else float("nan")
            out[str(int(R))][lab] = {"n": int(m.sum()), "mean": float(pnl[m].mean()),
                                     "null": nm, "lo": float(l2), "hi": float(h2)}
            flag = "  <<<" if l2 > lo else ""
            print("  %-22s %7s %+10.3f %+10.3f %+9.3f   [%+.2f, %+.2f]%s"
                  % (lab, "{:,}".format(int(m.sum())), pnl[m].mean(), nm,
                     pnl[m].mean() - pnl.mean(), l2, h2, flag))

        # does the best band hold out of sample?
        best = max(out[str(int(R))].items(), key=lambda kv: kv[1]["mean"])
        lab = best[0]
        a, b = [x for x in bands if x[0] == lab][0][1:]
        m = (p0 >= a) & (p0 < b)
        d_, v_ = m & (yr < SPLIT), m & (yr >= SPLIT)
        print("  best band '%s': discovery %+.3f (n=%d)   validation %+.3f (n=%d)\n"
              % (lab, pnl[d_].mean(), d_.sum(), pnl[v_].mean(), v_.sum()))
        out[str(int(R))][lab]["disc"] = float(pnl[d_].mean())
        out[str(int(R))][lab]["val"] = float(pnl[v_].mean())

    json.dump(out, open(os.path.join(HERE, "overnight_gb.json"), "w"), indent=1)
    print("wrote overnight_gb.json")
    print("\nA band only matters if its interval clears the UNCONDITIONAL")
    print("lower bound of %+.3f -- otherwise the lattice has added nothing to an"
          % lo)
    print("edge that was already there.")


if __name__ == "__main__":
    main()
