"""Do levels marked by SEVERAL PO3 scales at once react more?

This is the claim in its strongest and most testable form. On the trader's
chart the lines are not evenly spread -- they bunch. Where several PO3 scales
put a level at nearly the same price you get a thick cluster, and the reported
experience is that some levels "work wonder" while others do nothing. Cluster
depth is the obvious candidate for what separates them, and it is exactly what
the eye picks up from the chart.

  CONFLUENCE  for an R=81 Goldbach level, how many of the OTHER scales
              (27, 243, 729, 2187, 6561) also place a Goldbach level within
              half a percentage point of that same price.

R=81 itself is excluded from the count so that a level never scores a point for
matching itself -- otherwise the true lattice would carry a guaranteed +1 that
no shifted lattice can have, and the comparison would be rigged.

THE NULL is the subtle part. Shifting the lattice would change which prices are
events, so instead the event set is held fixed at the true R=81 levels and only
the CONFLUENCE LABEL is recomputed from a shifted nested family. Both the true
and the shifted labelling then partition the same pool of touches, and the
question becomes: does the real confluence structure sort those touches into
better and worse ones more sharply than an arbitrary one does?

Outcome is the touch test from baserate.py -- filled at the line, with the
arriving bar's push past it counted as heat against the fade.
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
OTHER = [27, 243, 729, 2187, 6561]      # 81 excluded on purpose
TOL = 0.5                                # percentage points
NNULL = 200


def confluence_map():
    """For each bin of the 6561 window: how many other scales mark a level."""
    centre = (np.arange(NBIN) + 0.5) * (PERIOD / NBIN)
    conf = np.zeros(NBIN, np.int8)
    for R in OTHER:
        pct = np.mod(centre, R) / R * 100.0
        d = np.abs(pct[:, None] - gbr.LEVELS[None, :])
        d = np.minimum(d, 100.0 - d)
        conf += (d.min(axis=1) <= TOL)
    return conf


def bin_of(px):
    return np.clip((np.mod(px, PERIOD) * (NBIN / PERIOD)).astype(np.int64),
                   0, NBIN - 1)


def main():
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

    conf = confluence_map()
    print("confluence map over %s bins (%.3f pts each), scales %s, tol %.1fpp"
          % ("{:,}".format(NBIN), PERIOD / NBIN, OTHER, TOL))
    cov = np.bincount(conf, minlength=len(OTHER) + 1) / NBIN
    print("  share of price space by confluence: %s\n"
          % "  ".join("c=%d %.3f" % (i, v) for i, v in enumerate(cov) if v > 0))

    # ---- collect every touch of an R=81 Goldbach level ---------------------
    R = 81.0
    lv, res = [], []
    for pct in gbr.LEVELS:
        o = R * pct / 100.0
        for idx, L, up in br.approaches(h, l, c, a, cmin, cmax, o, R, n):
            r = br.resolve_touch(h, l, idx, L, a[idx], up, n)
            keep = r != 0
            lv.append(L[keep])
            res.append(r[keep])
    L = np.concatenate(lv)
    res = np.concatenate(res)
    rej = (res == 1)
    print("%s resolved touches of an R=81 level, overall reject %.4f\n"
          % ("{:,}".format(len(L)), rej.mean()))

    b = bin_of(L)
    true_c = conf[b]

    rng = np.random.default_rng(11)
    shifts = rng.integers(1, NBIN, size=NNULL)

    rows = []
    print("  %-14s %10s %10s %10s %9s %7s"
          % ("confluence", "touches", "reject", "null same c", "edge", "z"))
    for j in range(0, len(OTHER) + 1):
        m = true_c == j
        if m.sum() < 500:
            continue
        p = float(rej[m].mean())
        nulls = []
        for s in shifts:
            sc = np.roll(conf, s)[b]
            mm = sc == j
            if mm.sum() >= 500:
                nulls.append(float(rej[mm].mean()))
        if len(nulls) < 20:
            continue
        nl = np.array(nulls)
        sd = nl.std(ddof=1)
        z = (p - nl.mean()) / sd if sd > 0 else 0.0
        rows.append({"confluence": j, "n": int(m.sum()), "reject": p,
                     "null_mean": float(nl.mean()), "z": float(z)})
        print("  c=%-12d %10s %10.4f %10.4f %+8.2fpp %+7.2f"
              % (j, "{:,}".format(int(m.sum())), p, nl.mean(),
                 (p - nl.mean()) * 100, z))

    # does reject rate RISE with confluence at all, true lattice only?
    if len(rows) >= 3:
        xs = np.array([r["confluence"] for r in rows], float)
        ys = np.array([r["reject"] for r in rows])
        w = np.array([r["n"] for r in rows], float)
        slope = np.polyfit(xs, ys, 1, w=np.sqrt(w))[0]
        print("\n  weighted trend across confluence: %+.4f reject per extra scale"
              % slope)
        print("  (spread from lowest to highest confluence: %+.2f pp)"
              % ((ys.max() - ys.min()) * 100))

    with open(os.path.join(HERE, "confluence.json"), "w") as fh:
        json.dump(rows, fh, indent=1)
    print("\nwrote confluence.json")


if __name__ == "__main__":
    main()
