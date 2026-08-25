"""Controls on the confluence result -- the first positive finding in this repo.

Touches of an R=81 Goldbach level reject more often when other PO3 scales mark
the same price: 39.1% at confluence 0-1 rising to 42.4% at confluence 5, while
shifted lattices stay flat at 39.3%. Before that means anything it has to
survive the obvious alternative explanations.

  ROUND NUMBERS   deep confluence sits near multiples of the big blocks, which
                  are large roundish prices. Round decimals have already shown
                  a real effect in this repo (z -3.39 in the structure test),
                  so this is the confound most likely to be the whole story.
                  Two ways at it: rerun with round-number prices excluded, and
                  build the identical statistic on a purely round-number
                  "confluence" map to see how it compares.

  WHICH SCALES    is it confluence at all, or just proximity to a 2187/6561
                  level? Split the count into big scales and small scales and
                  see which carries it.

  ERA             a real structural effect should not live in one regime.

  CLUSTERING      522,544 touches are not independent -- one afternoon makes
                  hundreds. The trend is re-tested resampling whole days.
"""
import json
import os

import numpy as np

import gbr
import baserate as br
from edge import atr

HERE = os.path.dirname(os.path.abspath(__file__))
PERIOD = 6561.0
NBIN = 52488
TOL = 0.5
CACHE = os.path.join(HERE, "touches_81.npz")


def bin_of(px):
    return np.clip((np.mod(px, PERIOD) * (NBIN / PERIOD)).astype(np.int64),
                   0, NBIN - 1)


def conf_map(scales, tol=TOL):
    centre = (np.arange(NBIN) + 0.5) * (PERIOD / NBIN)
    out = np.zeros(NBIN, np.int8)
    for R in scales:
        pct = np.mod(centre, R) / R * 100.0
        d = np.abs(pct[:, None] - gbr.LEVELS[None, :])
        d = np.minimum(d, 100.0 - d)
        out += (d.min(axis=1) <= tol)
    return out


def collect():
    """Every resolved touch of an R=81 level, with bar index and level price."""
    if os.path.exists(CACHE):
        z = np.load(CACHE)
        print("loaded cached touches")
        return z["L"], z["idx"], z["res"]
    npz = np.load(os.path.join(HERE, "bars.npz"))
    h, l, c = (np.asarray(npz[k]) for k in ("h", "l", "c"))
    a = atr(h, l, c)
    n = len(c)
    cmin, cmax = c.copy(), c.copy()
    for off in range(1, 60):
        cmin[off:] = np.minimum(cmin[off:], c[:-off])
        cmax[off:] = np.maximum(cmax[off:], c[:-off])
    cmin = np.concatenate([[c[0]], cmin[:-1]])
    cmax = np.concatenate([[c[0]], cmax[:-1]])

    R = 81.0
    Ls, ids, rs = [], [], []
    for pct in gbr.LEVELS:
        o = R * pct / 100.0
        for idx, L, up in br.approaches(h, l, c, a, cmin, cmax, o, R, n):
            r = br.resolve_touch(h, l, idx, L, a[idx], up, n)
            k = r != 0
            Ls.append(L[k]); ids.append(idx[k]); rs.append(r[k])
    L = np.concatenate(Ls); idx = np.concatenate(ids); res = np.concatenate(rs)
    np.savez_compressed(CACHE, L=L, idx=idx, res=res)
    return L, idx, res


def table(rej, code, label, nulls_fn=None, minn=500):
    """Reject rate by code value, optionally against a null labelling."""
    rows = []
    print("  %-16s %10s %10s %10s %9s" % (label, "touches", "reject", "null", "edge"))
    for j in range(int(code.max()) + 1):
        m = code == j
        if m.sum() < minn:
            continue
        p = float(rej[m].mean())
        nm = nulls_fn(j) if nulls_fn else float("nan")
        rows.append({"code": j, "n": int(m.sum()), "reject": p, "null": nm})
        print("  %-16d %10s %10.4f %10.4f %+8.2fpp"
              % (j, "{:,}".format(int(m.sum())), p, nm,
                 (p - nm) * 100 if nm == nm else float("nan")))
    return rows


def trend(rows):
    xs = np.array([r["code"] for r in rows], float)
    ys = np.array([r["reject"] for r in rows])
    w = np.sqrt(np.array([r["n"] for r in rows], float))
    return float(np.polyfit(xs, ys, 1, w=w)[0])


def main():
    L, idx, res = collect()
    rej = (res == 1)
    npz = np.load(os.path.join(HERE, "bars.npz"))
    yr = np.asarray(npz["yr"])[idx]
    date = np.asarray(npz["date"])[idx]
    print("%s resolved touches, overall reject %.4f\n"
          % ("{:,}".format(len(L)), rej.mean()))

    conf5 = conf_map([27, 243, 729, 2187, 6561])
    b = bin_of(L)
    c_true = conf5[b]
    rng = np.random.default_rng(11)
    shifts = rng.integers(1, NBIN, size=200)

    def nullfn(j):
        vals = []
        for s in shifts:
            mm = np.roll(conf5, s)[b] == j
            if mm.sum() >= 500:
                vals.append(float(rej[mm].mean()))
        return float(np.mean(vals)) if vals else float("nan")

    out = {}

    # ---------- 1. round numbers ------------------------------------------
    print("=== 1. is deep confluence just round numbers? ===")
    d100 = np.minimum(np.mod(L, 100.0), 100.0 - np.mod(L, 100.0))
    for j in range(6):
        m = c_true == j
        if m.sum() >= 500:
            print("   confluence %d: median distance to a round 100 = %6.1f pts"
                  % (j, np.median(d100[m])))

    far = d100 > 10.0
    print("\n   restricted to levels more than 10 points from a round 100"
          " (%s of %s touches):" % ("{:,}".format(int(far.sum())),
                                    "{:,}".format(len(L))))
    rows_far = table(rej[far], c_true[far], "confluence",
                     lambda j: float(np.mean(
                         [rej[far][np.roll(conf5, s)[b[far]] == j].mean()
                          for s in shifts[:60]
                          if (np.roll(conf5, s)[b[far]] == j).sum() >= 500])))
    out["far_from_round"] = rows_far
    if len(rows_far) >= 3:
        print("   trend: %+.4f per scale" % trend(rows_far))

    print("\n   the same statistic on a ROUND-NUMBER confluence map"
          " (25/50/100/500/1000):")
    rnd = np.zeros(len(L), np.int8)
    for step in (25.0, 50.0, 100.0, 500.0, 1000.0):
        d = np.minimum(np.mod(L, step), step - np.mod(L, step))
        rnd += (d <= 0.5 * step / 81.0 * 0.5 + 1e-9) | (d < 1.0)
    rows_rnd = table(rej, rnd, "round depth")
    out["round_map"] = rows_rnd

    # ---------- 2. which scales carry it ----------------------------------
    print("\n=== 2. which scales carry it? ===")
    for name, scales in (("big 2187+6561", [2187, 6561]),
                         ("mid 729", [729]),
                         ("small 27+243", [27, 243])):
        cm = conf_map(scales)[b]
        print("\n   %s:" % name)
        r = table(rej, cm, "levels marked")
        out["scales_" + name.split()[0]] = r

    # ---------- 3. era ----------------------------------------------------
    print("\n=== 3. does it hold in every era? ===")
    print("  %-12s %8s %8s %8s %8s %9s"
          % ("era", "c<=1", "c=2", "c>=3", "n c>=3", "spread"))
    eras = []
    for lab, lo, hi in (("2010-2014", 2010, 2014), ("2015-2019", 2015, 2019),
                        ("2020-2026", 2020, 2026)):
        s = (yr >= lo) & (yr <= hi)
        lowm = s & (c_true <= 1)
        midm = s & (c_true == 2)
        him = s & (c_true >= 3)
        if him.sum() < 300:
            continue
        a_, b_, c_ = (float(rej[lowm].mean()), float(rej[midm].mean()),
                      float(rej[him].mean()))
        eras.append({"era": lab, "low": a_, "mid": b_, "high": c_,
                     "n_high": int(him.sum()), "spread": c_ - a_})
        print("  %-12s %8.4f %8.4f %8.4f %8s %+8.2fpp"
              % (lab, a_, b_, c_, "{:,}".format(int(him.sum())),
                 (c_ - a_) * 100))
    out["eras"] = eras

    # ---------- 4. day-clustered significance -----------------------------
    print("\n=== 4. significance resampling whole days ===")
    hi_m = c_true >= 3
    lo_m = c_true <= 1
    u, inv = np.unique(date, return_inverse=True)
    nd = len(u)

    def day_sums(mask):
        s = np.bincount(inv[mask], weights=rej[mask].astype(float), minlength=nd)
        n = np.bincount(inv[mask], minlength=nd).astype(float)
        return s, n

    sh, nh = day_sums(hi_m)
    sl, nl = day_sums(lo_m)
    obs = sh.sum() / nh.sum() - sl.sum() / nl.sum()
    rg = np.random.default_rng(3)
    pick = rg.integers(0, nd, size=(2000, nd))
    diff = (sh[pick].sum(1) / np.maximum(nh[pick].sum(1), 1)
            - sl[pick].sum(1) / np.maximum(nl[pick].sum(1), 1))
    lo_ci, hi_ci = np.percentile(diff, [2.5, 97.5])
    print("   reject(confluence>=3) - reject(confluence<=1) = %+.4f" % obs)
    print("   95%% CI resampling %s days: [%+.4f, %+.4f]" % ("{:,}".format(nd),
                                                             lo_ci, hi_ci))
    print("   share of resamples above zero: %.3f" % float((diff > 0).mean()))
    out["day_boot"] = {"obs": float(obs), "lo": float(lo_ci), "hi": float(hi_ci),
                       "p_pos": float((diff > 0).mean()), "days": int(nd)}

    with open(os.path.join(HERE, "controls.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote controls.json")


if __name__ == "__main__":
    main()
