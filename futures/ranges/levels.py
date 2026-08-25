"""Are the twenty Goldbach levels actually different from each other?

The stratified confluence test threw this up as a side effect. Holding the
level fixed, confluence added nothing -- but the levels themselves came out
spread across roughly four percentage points of rejection rate, with 0 and 50
at the top and 11, 41, 59, 89 at the bottom. On 26,000 touches per level that
is worth testing on its own, because it is a different claim from anything
tested so far: not "does the lattice matter" but "within the lattice, are some
lines better than others".

THE NULL is a within-day label permutation. Each day's touches keep their
outcomes and their timing; only which of the twenty levels they belong to is
shuffled, inside the day, so the heavy intraday clustering is preserved
exactly. If level identity carries no information, the true spread across the
twenty rates should look like a typical draw from that.

Reported both as an omnibus (is the spread unusual at all?) and per level with
day-clustered intervals, since the interesting part is which ones.
"""
import json
import os

import numpy as np

import controls as ct

HERE = os.path.dirname(os.path.abspath(__file__))
NPERM = 2000
NBOOT = 2000

# 0 is the block boundary and 50 the midpoint -- both belong to ANY evenly
# spaced grid. The other eighteen are Goldbach's own percentages.
STRUCTURAL = {0, 50}


def main():
    L, idx, res = ct.collect()
    rej = (res == 1).astype(np.float64)
    date = np.asarray(np.load(os.path.join(HERE, "bars.npz"))["date"])[idx]
    pct = np.round(np.mod(L, 81.0) / 81.0 * 100.0).astype(np.int64) % 100

    lv = np.array(sorted(set(pct.tolist())))
    code = np.searchsorted(lv, pct)
    nlv = len(lv)
    u, day = np.unique(date, return_inverse=True)
    nd = len(u)
    print("%s touches, %d levels, %s days, overall reject %.4f\n"
          % ("{:,}".format(len(L)), nlv, "{:,}".format(nd), rej.mean()))

    def rates(cd):
        s = np.bincount(cd, weights=rej, minlength=nlv)
        n = np.bincount(cd, minlength=nlv).astype(float)
        return s / np.maximum(n, 1), n

    true_r, cnt = rates(code)
    true_spread = true_r.max() - true_r.min()
    true_sd = true_r.std(ddof=1)

    # ---- omnibus: within-day permutation of the level labels --------------
    order = np.argsort(day, kind="stable")
    day_s, code_s = day[order], code[order]
    starts = np.searchsorted(day_s, np.arange(nd))
    ends = np.append(starts[1:], len(day_s))
    rej_s = rej[order]

    rng = np.random.default_rng(19)
    sp, sd = np.empty(NPERM), np.empty(NPERM)
    for t in range(NPERM):
        perm = code_s.copy()
        for a, b in zip(starts, ends):
            if b - a > 1:
                perm[a:b] = perm[a:b][rng.permutation(b - a)]
        s = np.bincount(perm, weights=rej_s, minlength=nlv)
        n = np.bincount(perm, minlength=nlv).astype(float)
        r = s / np.maximum(n, 1)
        sp[t] = r.max() - r.min()
        sd[t] = r.std(ddof=1)

    print("=== omnibus: does level identity carry information? ===")
    print("  spread across the 20 levels:  true %.4f   permuted %.4f (sd %.4f)"
          % (true_spread, sp.mean(), sp.std(ddof=1)))
    print("  z = %+.2f     permutations exceeding the true spread: %d / %d"
          % ((true_spread - sp.mean()) / sp.std(ddof=1), int((sp >= true_spread).sum()), NPERM))
    print("  dispersion (sd across levels): true %.4f   permuted %.4f   z = %+.2f"
          % (true_sd, sd.mean(), (true_sd - sd.mean()) / sd.std(ddof=1)))

    # ---- per level, with day-clustered intervals --------------------------
    print("\n=== per level ===")
    print("  %-7s %-20s %9s %9s %19s"
          % ("level", "name", "touches", "reject", "95% CI (by day)"))
    ds = np.zeros((nlv, nd))
    dn = np.zeros((nlv, nd))
    np.add.at(ds, (code, day), rej)
    np.add.at(dn, (code, day), 1.0)
    pick = rng.integers(0, nd, size=(NBOOT, nd))

    from gbr import LEVEL_NAME
    rows = []
    for i, p in enumerate(lv):
        bs = ds[i][pick].sum(1) / np.maximum(dn[i][pick].sum(1), 1)
        lo, hi = np.percentile(bs, [2.5, 97.5])
        rows.append({"pct": int(p), "name": LEVEL_NAME.get(int(p), ""),
                     "n": int(cnt[i]), "reject": float(true_r[i]),
                     "lo": float(lo), "hi": float(hi),
                     "structural": int(p) in STRUCTURAL})
        print("  %-7d %-20s %9s %9.4f   [%.4f, %.4f]%s"
              % (p, LEVEL_NAME.get(int(p), ""), "{:,}".format(int(cnt[i])),
                 true_r[i], lo, hi, "  <- grid" if int(p) in STRUCTURAL else ""))

    # ---- is it just the boundary and the midpoint? ------------------------
    st = np.isin(lv, list(STRUCTURAL))
    gb = ~st
    w_st = cnt[st] / cnt[st].sum()
    w_gb = cnt[gb] / cnt[gb].sum()
    r_st = float((true_r[st] * w_st).sum())
    r_gb = float((true_r[gb] * w_gb).sum())
    print("\n=== is it only the lines any grid would have? ===")
    print("  block boundary + midpoint (0, 50):  %.4f  on %s touches"
          % (r_st, "{:,}".format(int(cnt[st].sum()))))
    print("  the eighteen Goldbach percentages:  %.4f  on %s touches"
          % (r_gb, "{:,}".format(int(cnt[gb].sum()))))
    print("  difference: %+.2f pp" % ((r_st - r_gb) * 100))

    idx_st = np.flatnonzero(st)
    idx_gb = np.flatnonzero(gb)
    b_st = ds[idx_st].sum(0)[pick].sum(1) / np.maximum(dn[idx_st].sum(0)[pick].sum(1), 1)
    b_gb = ds[idx_gb].sum(0)[pick].sum(1) / np.maximum(dn[idx_gb].sum(0)[pick].sum(1), 1)
    d = b_st - b_gb
    print("  95%% CI on the difference: [%+.4f, %+.4f]   share above zero %.3f"
          % (np.percentile(d, 2.5), np.percentile(d, 97.5), float((d > 0).mean())))

    # dispersion among the eighteen alone -- the Goldbach-specific claim
    sp18, sd18 = np.empty(NPERM), np.empty(NPERM)
    for t in range(NPERM):
        perm = code_s.copy()
        for a, b in zip(starts, ends):
            if b - a > 1:
                perm[a:b] = perm[a:b][rng.permutation(b - a)]
        s = np.bincount(perm, weights=rej_s, minlength=nlv)
        n = np.bincount(perm, minlength=nlv).astype(float)
        r = (s / np.maximum(n, 1))[gb]
        sp18[t] = r.max() - r.min()
        sd18[t] = r.std(ddof=1)
    t18 = true_r[gb]
    print("\n  among the eighteen alone -- spread true %.4f  permuted %.4f  z=%+.2f"
          % (t18.max() - t18.min(), sp18.mean(),
             (t18.max() - t18.min() - sp18.mean()) / sp18.std(ddof=1)))
    print("  dispersion true %.4f  permuted %.4f  z=%+.2f"
          % (t18.std(ddof=1), sd18.mean(),
             (t18.std(ddof=1) - sd18.mean()) / sd18.std(ddof=1)))

    json.dump({"levels": rows,
               "omnibus": {"spread": float(true_spread),
                           "perm_mean": float(sp.mean()),
                           "perm_sd": float(sp.std(ddof=1)),
                           "z": float((true_spread - sp.mean()) / sp.std(ddof=1)),
                           "exceed": int((sp >= true_spread).sum()), "nperm": NPERM},
               "structural_vs_gb": {"structural": r_st, "goldbach": r_gb,
                                    "diff": r_st - r_gb,
                                    "lo": float(np.percentile(d, 2.5)),
                                    "hi": float(np.percentile(d, 97.5))}},
              open(os.path.join(HERE, "levels.json"), "w"), indent=1)
    print("\nwrote levels.json")


if __name__ == "__main__":
    main()
