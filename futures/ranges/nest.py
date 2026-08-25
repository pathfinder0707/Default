"""Does MULTI-SCALE ALIGNMENT separate the levels that work?

Every earlier test in this repo took one block size at a time. The trader's own
tool does not: it shows all eight PO3 scales simultaneously, and the intuition
being reported is that some levels "work wonder" and others do nothing. The
obvious candidate for what separates them is agreement across scales -- price
sitting in the same named zone of the 27, 81, 243, 729 ... blocks at once.

That is a real, computable structure rather than a vague confluence story,
because the blocks nest exactly: 729 = 3 x 243 = 9 x 81. A price at the low of
the 243 block is necessarily at the low of one of its three 81 sub-blocks. So
"how many scales agree here" is a deterministic function of price, and it is
exactly what the tool is displaying.

METHOD. Everything is periodic in price with period 6561 (every smaller block
size divides it), so the whole question can be answered on one 6561-point
window:

  * bin the window finely, and for each bin count how many of the six scales
    place it inside the named zone -- that count is k, the alignment depth
  * histogram the swing prices and the occupancy prices into the same bins
  * a lattice shift is then just a roll of the k array, which shifts ALL scales
    together and so preserves the nesting exactly

That last point is what makes the null honest. Shifting every scale by the same
absolute offset keeps the entire nested geometry intact and moves only WHERE it
sits, which is precisely the question: do the Goldbach percentages matter, or
would any nested PO3 lattice do?

Occupancy is subtracted throughout, because deep-alignment prices are not
visited uniformly and a zone can collect swings just by being where price is.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PERIOD = 6561.0
NBIN = 52488                 # 0.125 points per bin -- half a tick
SCALES = [27, 81, 243, 729, 2187, 6561]
NNULL = 400

ZONES = {
    "EXT_97_100": [(97.0, 100.0), (0.0, 3.0)],
    "EQ_47_53":   [(47.0, 53.0)],
    "FV_29_71":   [(27.5, 30.5), (69.5, 72.5)],
    "GIP_17_83":  [(15.5, 18.5), (81.5, 84.5)],
}


def depth_map(bands, scales=SCALES):
    """For each bin of the 6561 window, how many scales put it in the zone."""
    centre = (np.arange(NBIN) + 0.5) * (PERIOD / NBIN)
    k = np.zeros(NBIN, np.int8)
    per_scale = {}
    for R in scales:
        pct = np.mod(centre, R) / R * 100.0
        m = np.zeros(NBIN, bool)
        for lo, hi in bands:
            m |= (pct >= lo) & (pct < hi)
        per_scale[R] = m
        k += m
    return k, per_scale


def hist(px):
    idx = np.mod(px, PERIOD) * (NBIN / PERIOD)
    idx = np.clip(idx.astype(np.int64), 0, NBIN - 1)
    return np.bincount(idx, minlength=NBIN).astype(np.float64)


def rate_at_depth(h, k, j, shift):
    """Share of h sitting at alignment depth >= j, with the lattice rolled."""
    kk = np.roll(k, shift)
    return h[kk >= j].sum() / h.sum()


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    h, l = np.asarray(npz["h"]), np.asarray(npz["l"])

    zz = np.load(os.path.join(HERE, "zz_50.npz"))       # zigzag 0.5%, cached
    swing_px = zz["px"]
    print("swings: %s   bars: %s   bins: %s (%.3f pts each)"
          % ("{:,}".format(len(swing_px)), "{:,}".format(len(h)),
             "{:,}".format(NBIN), PERIOD / NBIN))

    occ = hist(np.concatenate([h, l]))
    swg = hist(swing_px)

    rng = np.random.default_rng(7)
    shifts = rng.integers(1, NBIN, size=NNULL)

    out = []
    for zname, bands in ZONES.items():
        k, per_scale = depth_map(bands)
        cover = np.bincount(k, minlength=len(SCALES) + 1) / NBIN
        print("\n=== %s ===" % zname)
        print("  alignment depth covers: %s"
              % "  ".join("k=%d %.3f" % (i, c) for i, c in enumerate(cover) if c > 0))
        print("  %-8s %10s %10s %10s %9s %8s %7s"
              % ("depth", "swings", "swing rate", "occupancy", "excess", "null", "z"))

        for j in range(1, len(SCALES) + 1):
            if (k >= j).sum() == 0:
                continue
            n_sw = float(swg[k >= j].sum())
            if n_sw < 100:
                continue
            sr = rate_at_depth(swg, k, j, 0)
            orr = rate_at_depth(occ, k, j, 0)
            true_ex = sr - orr
            nulls = np.array([rate_at_depth(swg, k, j, s) - rate_at_depth(occ, k, j, s)
                              for s in shifts])
            sd = nulls.std(ddof=1)
            z = (true_ex - nulls.mean()) / sd if sd > 0 else 0.0
            out.append({"zone": zname, "depth": j, "n_swings": n_sw,
                        "swing_rate": sr, "occ_rate": orr, "excess": true_ex,
                        "null_mean": float(nulls.mean()), "z": float(z)})
            print("  k>=%-6d %10s %10.4f %10.4f %+9.4f %+8.4f %+7.2f"
                  % (j, "{:,.0f}".format(n_sw), sr, orr, true_ex,
                     nulls.mean(), z))

    with open(os.path.join(HERE, "nest.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    zs = [r["z"] for r in out]
    print("\n%d cells   z from %+.2f to %+.2f   |z|>3: %d"
          % (len(out), min(zs), max(zs), sum(1 for z in zs if abs(z) > 3)))
    print("wrote nest.json")


if __name__ == "__main__":
    main()
