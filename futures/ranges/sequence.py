"""The framework is a SEQUENCE model. Every test here has treated it as a
level model.

Re-reading the source with that in mind, almost nothing in it is a claim about
a single price. The claims are about order:

  "price sweeps the liquidity ... then delivers to the flow layer"
  "when price moves THROUGH the flow layer ... they will first retrace price,
   BACK INTO the flow layer. When price retraces, THIS is where you buy"
  "price gaps up through [11-89] to [17-83], runs to the flow middle [29-71],
   there price will retrace back towards the zone between [11-89] and [17-83]"

Those are transition statements. Whether price STOPS at a level -- the question
every other test in this repo asks -- is not actually what the document claims.
It claims price is DELIVERED between layers in a particular order.

So: partition the block into its seven named layers, reduce price to the
sequence of layers it visits, and ask whether the transition structure differs
from what shifted lattices produce. The lattice shift is the same matched null
used throughout: it moves where the partition sits without changing that it is
a partition of a block into contiguous layers, so the trivial fact that price
moves continuously through adjacent zones is differenced out.

Three questions, in increasing strength:

  1. TRANSITIONS   is any layer-to-layer transition more likely at the true
                   lattice than at shifted ones?
  2. TRAVERSAL     having reached a liquidity extreme, does price cross to the
                   opposite extreme -- the "delivery" -- more often than chance?
  3. ORDER         does price step through the layers in sequence more often,
                   rather than skipping? A real delivery algorithm should walk.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NPHASE = 20

# a contiguous partition of the block into the document's named layers
ZONES = [
    ("liq_lo",  0.0, 11.0),
    ("gip_lo", 11.0, 23.0),
    ("flow_lo", 23.0, 41.0),
    ("reb",    41.0, 59.0),
    ("flow_hi", 59.0, 77.0),
    ("gip_hi", 77.0, 89.0),
    ("liq_hi", 89.0, 100.0),
]
NAMES = [z[0] for z in ZONES]
NZ = len(ZONES)
EDGES = np.array([z[1] for z in ZONES] + [100.0])


def zone_seq(c, R, phase):
    """The sequence of distinct layers price visits, and where each began."""
    pct = np.mod(c - R * phase / 100.0, R) / R * 100.0
    z = np.clip(np.searchsorted(EDGES, pct, side="right") - 1, 0, NZ - 1)
    keep = np.empty(len(z), bool)
    keep[0] = True
    np.not_equal(z[1:], z[:-1], out=keep[1:])
    idx = np.flatnonzero(keep)
    return z[idx], idx


def transitions(seq):
    """Row-normalised transition matrix over distinct-layer visits."""
    if len(seq) < 3:
        return np.full((NZ, NZ), np.nan)
    m = np.zeros((NZ, NZ))
    np.add.at(m, (seq[:-1], seq[1:]), 1.0)
    tot = m.sum(axis=1, keepdims=True)
    return m / np.maximum(tot, 1)


def traversal(seq):
    """From a liquidity extreme, does price reach the OPPOSITE extreme next?

    'Next' means before returning to the extreme it started from. This is the
    delivery claim in its cleanest form.
    """
    lo, hi = 0, NZ - 1
    got = tot = 0
    cur = None
    for z in seq:
        if z in (lo, hi):
            if cur is None:
                cur = z
            elif z != cur:
                got += 1; tot += 1; cur = z
            else:
                tot += 1
    return got, tot


def step_rate(seq):
    """Share of transitions that move exactly one layer -- walking, not jumping."""
    if len(seq) < 2:
        return np.nan
    d = np.abs(np.diff(seq.astype(np.int64)))
    return float((d == 1).mean())


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    c = np.asarray(npz["c"])
    out = {}

    for R in (243.0, 729.0, 2187.0):
        print("\n=== R=%d ===" % R)
        seq0, _ = zone_seq(c, R, 0.0)
        t0 = transitions(seq0)
        g0, n0 = traversal(seq0)
        s0 = step_rate(seq0)
        print("  %s layer visits" % "{:,}".format(len(seq0)))

        tn, gn, sn = [], [], []
        for j in range(1, NPHASE):
            s, _ = zone_seq(c, R, j * 100.0 / NPHASE)
            tn.append(transitions(s))
            g, n = traversal(s)
            gn.append(g / n if n else np.nan)
            sn.append(step_rate(s))
        tn = np.array(tn)
        mu, sd = tn.mean(axis=0), tn.std(axis=0, ddof=1)
        z = np.where(sd > 0, (t0 - mu) / np.maximum(sd, 1e-12), 0.0)

        print("\n  1. transition matrix, z against %d shifted lattices" % (NPHASE - 1))
        print("     %-9s %s" % ("from \\ to", " ".join("%8s" % n[:8] for n in NAMES)))
        for a in range(NZ):
            print("     %-9s %s" % (NAMES[a],
                                    " ".join("%+8.2f" % z[a, b] for b in range(NZ))))
        print("     largest |z| in the matrix: %.2f   cells past |3|: %d of %d"
              % (np.abs(z).max(), int((np.abs(z) > 3).sum()), NZ * NZ))

        gr = g0 / n0 if n0 else np.nan
        gnm = np.nanmean(gn); gsd = np.nanstd(gn, ddof=1)
        print("\n  2. traversal: from one liquidity extreme to the other")
        print("     true %.4f on %s   shifted %.4f (sd %.4f)   z = %+.2f"
              % (gr, "{:,}".format(n0), gnm, gsd,
                 (gr - gnm) / gsd if gsd > 0 else 0.0))

        snm = np.nanmean(sn); ssd = np.nanstd(sn, ddof=1)
        print("\n  3. order: share of moves that step exactly one layer")
        print("     true %.4f   shifted %.4f (sd %.4f)   z = %+.2f"
              % (s0, snm, ssd, (s0 - snm) / ssd if ssd > 0 else 0.0))

        out[str(int(R))] = {
            "visits": int(len(seq0)),
            "z_max": float(np.abs(z).max()),
            "z_over3": int((np.abs(z) > 3).sum()),
            "z_matrix": z.tolist(),
            "traversal": {"true": float(gr), "n": int(n0),
                          "null": float(gnm), "sd": float(gsd),
                          "z": float((gr - gnm) / gsd) if gsd > 0 else 0.0},
            "step": {"true": float(s0), "null": float(snm), "sd": float(ssd),
                     "z": float((s0 - snm) / ssd) if ssd > 0 else 0.0},
        }

    json.dump(out, open(os.path.join(HERE, "sequence.json"), "w"), indent=1)
    print("\nwrote sequence.json")


if __name__ == "__main__":
    main()
