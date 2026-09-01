"""Is the overnight block-position result real, or an autocorrelation artifact?

overnight_gb.py found two cells that clear the unconditional lower bound:
R=729 equilibrium at +15.49/night and R=2187 [10-25] at +15.13/night, both
roughly +10 above their shifted-lattice nulls. That is the first Goldbach
result in this repo to survive its own test, so it gets attacked harder.

Two specific threats:

  1. AUTOCORRELATION. The lattice is anchored to absolute price. At R=729,
     NQ traversed roughly forty blocks in sixteen years, so block position
     is not a per-night property -- it is a regime that persists for weeks
     or months. If the 660 nights in a band come from a handful of
     contiguous episodes, the day-clustered bootstrap is counting the same
     observation hundreds of times and its interval is fiction. The unit of
     independence is the EPISODE, not the night.

  2. MULTIPLICITY. Twenty-one cells were scanned and two cleared at 95%.
     One is the expected false-positive count. The fix is a max-statistic
     test: draw many random lattice offsets, take the largest band deviation
     each one produces anywhere in the same 21-cell grid, and ask where the
     true maximum falls in that distribution. That prices in the search.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
COST = 0.45
SPLIT = 2019
NBOOT = 4000
NPERM = 400
BANDS = [("0-10", 0, 10), ("10-25", 10, 25), ("25-40", 25, 40),
         ("40-60", 40, 60), ("60-75", 60, 75), ("75-90", 75, 90),
         ("90-100", 90, 100)]
RS = (243.0, 729.0, 2187.0)


def sessions(date, tod):
    rth = (tod >= 930) & (tod < 1600)
    u = np.unique(date[rth])
    io = np.zeros(len(u), np.int64)
    ic = np.zeros(len(u), np.int64)
    for i, d in enumerate(u):
        m = np.flatnonzero(rth & (date == d))
        io[i], ic[i] = m[0], m[-1]
    return u, io, ic


def episodes(mask):
    """Contiguous runs of band membership, in chronological order."""
    idx = np.flatnonzero(mask)
    if len(idx) == 0:
        return np.array([], np.int64), 0
    brk = np.flatnonzero(np.diff(idx) > 1)
    eid = np.zeros(len(idx), np.int64)
    eid[brk + 1] = 1
    return np.cumsum(eid), int(eid.sum()) + 1


def cluster_ci(pnl, cid, rng, nb=NBOOT):
    """Bootstrap resampling whole clusters, whatever the cluster is."""
    u, inv = np.unique(cid, return_inverse=True)
    nc = len(u)
    if nc < 4:
        return float("nan"), float("nan")
    s = np.bincount(inv, weights=pnl, minlength=nc)
    n = np.bincount(inv, minlength=nc).astype(float)
    pick = rng.integers(0, nc, size=(nb, nc))
    bs = s[pick].sum(1) / np.maximum(n[pick].sum(1), 1)
    return tuple(np.percentile(bs, [2.5, 97.5]))


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    c = np.asarray(npz["c"])
    date = np.asarray(npz["date"])
    tod = np.asarray(npz["hh"]) * 100 + np.asarray(npz["mm"])
    u, io, ic = sessions(date, tod)

    pnl = c[io[1:]] - c[ic[:-1]] - COST
    days = u[1:]
    yr = days // 10000
    px = c[ic[:-1]]
    base = pnl.mean()
    rng = np.random.default_rng(11)
    out = {"uncond": float(base), "n": int(len(pnl))}

    print("overnight unconditional %+.3f net over %s nights\n"
          % (base, "{:,}".format(len(pnl))))

    # ---- threat 1: how many INDEPENDENT observations are there? ----------
    print("=" * 92)
    print("THREAT 1 -- block position is a slow regime, not a nightly draw")
    print("=" * 92)
    print("  %-6s %-8s %7s %8s %10s   %-18s %-18s"
          % ("R", "band", "nights", "episodes", "net/night",
             "CI clustered by day", "CI clustered by episode"))
    for R in RS:
        p0 = np.mod(px, R) / R * 100.0
        for lab, a, b in BANDS:
            m = (p0 >= a) & (p0 < b)
            if m.sum() < 150:
                continue
            eid, ne = episodes(m)
            dlo, dhi = cluster_ci(pnl[m], days[m], rng)
            elo, ehi = cluster_ci(pnl[m], eid, rng)
            out.setdefault(str(int(R)), {})[lab] = {
                "n": int(m.sum()), "episodes": ne, "mean": float(pnl[m].mean()),
                "day_lo": float(dlo), "day_hi": float(dhi),
                "ep_lo": float(elo), "ep_hi": float(ehi)}
            print("  %-6d %-8s %7s %8d %+10.3f   [%+7.2f, %+7.2f] [%+7.2f, %+7.2f]"
                  % (R, lab, "{:,}".format(int(m.sum())), ne, pnl[m].mean(),
                     dlo, dhi, elo, ehi))
        print()

    # median episode length tells the story in one number
    R = 729.0
    p0 = np.mod(px, R) / R * 100.0
    m = (p0 >= 40) & (p0 < 60)
    eid, ne = episodes(m)
    lens = np.bincount(eid)
    print("  R=729 equilibrium: %d nights arrive in %d episodes,"
          " median %d consecutive nights, longest %d"
          % (m.sum(), ne, int(np.median(lens)), int(lens.max())))
    print("  So the effective sample is nearer %d than %d.\n" % (ne, m.sum()))

    # ---- threat 2: price the 21-cell search ------------------------------
    print("=" * 92)
    print("THREAT 2 -- twenty-one cells were scanned; two cleared at 95%")
    print("=" * 92)
    true_max = 0.0
    true_cell = None
    for R in RS:
        p0 = np.mod(px, R) / R * 100.0
        for lab, a, b in BANDS:
            m = (p0 >= a) & (p0 < b)
            if m.sum() >= 150 and pnl[m].mean() - base > true_max:
                true_max = pnl[m].mean() - base
                true_cell = "R=%d %s" % (R, lab)

    null_max = np.empty(NPERM)
    for t in range(NPERM):
        off = rng.random(len(RS))
        best = -1e9
        for k, R in enumerate(RS):
            pj = np.mod(px - R * off[k], R) / R * 100.0
            for lab, a, b in BANDS:
                mj = (pj >= a) & (pj < b)
                if mj.sum() >= 150:
                    best = max(best, pnl[mj].mean() - base)
        null_max[t] = best

    p = float((null_max >= true_max).mean())
    print("  best true cell         %-14s %+.3f above unconditional" % (true_cell, true_max))
    print("  same search on %d random lattice offsets:" % NPERM)
    print("    median best cell     %+.3f" % np.median(null_max))
    print("    95th pct best cell   %+.3f" % np.percentile(null_max, 95))
    print("    max best cell        %+.3f" % null_max.max())
    print("  p = %.3f  (fraction of random lattices that beat the real one)\n" % p)
    out["maxstat"] = {"cell": true_cell, "true": float(true_max),
                      "null_med": float(np.median(null_max)),
                      "null_p95": float(np.percentile(null_max, 95)),
                      "p": p}

    # ---- threat 3: is it just the era? -----------------------------------
    print("=" * 92)
    print("THREAT 3 -- does the band just select a period?")
    print("=" * 92)
    print("  the overnight edge itself was %+.3f before %d and %+.3f after"
          % (pnl[yr < SPLIT].mean(), SPLIT, pnl[yr >= SPLIT].mean()))
    print("  %-6s %-8s %10s %10s %10s %10s"
          % ("R", "band", "disc", "vs disc", "val", "vs val"))
    for R in RS:
        p0 = np.mod(px, R) / R * 100.0
        for lab, a, b in BANDS:
            m = (p0 >= a) & (p0 < b)
            if m.sum() < 150:
                continue
            d_, v_ = m & (yr < SPLIT), m & (yr >= SPLIT)
            if d_.sum() < 60 or v_.sum() < 60:
                continue
            dm, vm = pnl[d_].mean(), pnl[v_].mean()
            rec = out[str(int(R))][lab]
            rec["disc"] = float(dm); rec["val"] = float(vm)
            rec["disc_rel"] = float(dm - pnl[yr < SPLIT].mean())
            rec["val_rel"] = float(vm - pnl[yr >= SPLIT].mean())
            print("  %-6d %-8s %+10.3f %+10.3f %+10.3f %+10.3f"
                  % (R, lab, dm, dm - pnl[yr < SPLIT].mean(),
                     vm, vm - pnl[yr >= SPLIT].mean()))
        print()

    json.dump(out, open(os.path.join(HERE, "overnight_gb2.json"), "w"), indent=1)
    print("wrote overnight_gb2.json")


if __name__ == "__main__":
    main()
