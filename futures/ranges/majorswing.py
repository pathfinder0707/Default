"""Do MAJOR swing highs and lows form in the named zones?

This is a narrower and fairer test than H1, which used fractal pivots of at most
20 bars' strength -- a 40-minute local pivot on 1-minute data, 122,652 of them.
Those are not major swings. It also pooled all 20 Goldbach levels, which dilutes
a claim made about three specific zones.

Here:
  * swings are defined two ways, both era-neutral
      ZIGZAG   a leg that ran at least X% of price and then retraced X% -- the
               closest formal analogue to a swing a trader would actually mark
      FRACTAL  pivots of strength 60 / 120 / 240 / 480 bars (1h to 8h a side)
  * only the named zones are scored, each 6 percentage points wide so the
    comparison between them is like-for-like:
      EXT   97-100 and 0-3      (the range extreme, both sides)
      EQ    47-53               (equilibrium)
      FV29  27.5-30.5, 69.5-72.5
      GIP17 15.5-18.5, 81.5-84.5
  * scored against 60 shifted lattice phases, and against the occupancy of the
    same zone (where price actually spends its time), because a zone can collect
    swings simply by being where price hangs around.

Under a uniform null each zone should collect 6.0% of swings. The question is
whether the TRUE lattice phase collects more than its 59 shifted twins.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NPHASE = 60

ZONES = {
    "EXT_97_100": [(97.0, 100.0), (0.0, 3.0)],
    "EQ_47_53":   [(47.0, 53.0)],
    "FV_29_71":   [(27.5, 30.5), (69.5, 72.5)],
    "GIP_17_83":  [(15.5, 18.5), (81.5, 84.5)],
}


def zigzag(h, l, pct_thresh):
    """Confirmed swing highs and lows from a percentage-reversal zigzag.

    Walks forward holding the running extreme of the current leg. When price
    retraces `pct_thresh` (as a fraction of price) away from that extreme, the
    extreme is confirmed as a swing and the direction flips. Returns the prices
    of confirmed swing highs and lows -- no look-ahead beyond the confirmation
    itself, which is inherent to the definition.
    """
    n = len(h)
    up = True
    ext = h[0]
    swings_h, swings_l = [], []
    for i in range(1, n):
        if up:
            if h[i] > ext:
                ext = h[i]
            elif l[i] < ext * (1.0 - pct_thresh):
                swings_h.append(ext)
                up = False
                ext = l[i]
        else:
            if l[i] < ext:
                ext = l[i]
            elif h[i] > ext * (1.0 + pct_thresh):
                swings_l.append(ext)
                up = True
                ext = h[i]
    return np.array(swings_h), np.array(swings_l)


def fractal(h, l, k):
    """Pivots whose extreme beats the k bars on each side."""
    n = len(h)
    hi_nb = np.full(n, -np.inf)
    lo_nb = np.full(n, np.inf)
    for off in range(1, k + 1):
        hi_nb[off:] = np.maximum(hi_nb[off:], h[:-off])
        hi_nb[:-off] = np.maximum(hi_nb[:-off], h[off:])
        lo_nb[off:] = np.minimum(lo_nb[off:], l[:-off])
        lo_nb[:-off] = np.minimum(lo_nb[:-off], l[off:])
    valid = np.zeros(n, bool)
    valid[k:n - k] = True
    return h[valid & (h > hi_nb)], l[valid & (l < lo_nb)]


def in_zone(px, R, bands, phase):
    pct = np.mod(px - R * phase / 100.0, R) / R * 100.0
    m = np.zeros(len(px), bool)
    for lo, hi in bands:
        m |= (pct >= lo) & (pct < hi)
    return m


def occ_hist(px, R, nbin=6000):
    """Histogram of block position -- lets every phase and zone be a bin sum.

    Recomputing the 9.5M-element occupancy array for each of 60 phases and each
    swing definition is the same redundant work the H1 run avoided; binning once
    per block size makes the whole scoring instant. nbin is a multiple of 60 so
    the phase shifts are exact bin rolls, and of 200 so every zone edge used
    here (97, 3, 47, 53, 27.5, 30.5, 15.5, 18.5 ...) lands on a bin boundary.
    """
    pct = np.mod(px, R) / R * 100.0
    idx = np.clip((pct * (nbin / 100.0)).astype(np.int64), 0, nbin - 1)
    return np.bincount(idx, minlength=nbin).astype(np.float64)


def zone_mask(bands, nbin=6000):
    grid = (np.arange(nbin) + 0.5) * (100.0 / nbin)
    m = np.zeros(nbin, bool)
    for lo, hi in bands:
        m |= (grid >= lo) & (grid < hi)
    return m


def rates_all_phases(hist, mask, nbin=6000, nphase=NPHASE):
    roll = nbin // nphase
    tot = hist.sum()
    return np.array([np.dot(np.roll(mask, j * roll), hist) / tot
                     for j in range(nphase)])


def score(swing_hist, occ_hist_, mask):
    """Zone hit rate at the true phase, against 59 shifted phases."""
    rates = rates_all_phases(swing_hist, mask)
    occ = rates_all_phases(occ_hist_, mask)
    adj = rates - occ                      # excess over where price simply is
    sd = rates[1:].std(ddof=1)
    sda = adj[1:].std(ddof=1)
    return {
        "n": int(swing_hist.sum()),
        "rate": float(rates[0]),
        "null_mean": float(rates[1:].mean()),
        "z": float((rates[0] - rates[1:].mean()) / sd) if sd > 0 else 0.0,
        "rank": int((rates >= rates[0]).sum()),
        "occ_rate": float(occ[0]),
        "excess": float(adj[0]),
        "z_occ_adj": float((adj[0] - adj[1:].mean()) / sda) if sda > 0 else 0.0,
        "rank_adj": int((adj >= adj[0]).sum()),
    }


def main():
    raw = np.load(os.path.join(HERE, "bars.npz"))
    h, l, c = raw["h"], raw["l"], raw["c"]
    occ = np.concatenate([h, l])

    defs = []
    for t in (0.0025, 0.005, 0.01, 0.02):
        sh, sl = zigzag(h, l, t)
        defs.append(("zigzag %.2f%%" % (t * 100), np.concatenate([sh, sl])))
        print("zigzag %.2f%%  ->  %s major swings" % (t * 100, "{:,}".format(len(sh) + len(sl))))
    for k in (60, 120, 240, 480):
        sh, sl = fractal(h, l, k)
        defs.append(("fractal k=%d" % k, np.concatenate([sh, sl])))
        print("fractal k=%-4d ->  %s swings" % (k, "{:,}".format(len(sh) + len(sl))))

    masks = {z: zone_mask(b) for z, b in ZONES.items()}
    rows = []
    for R in (81, 243, 729, 2187):
        oh = occ_hist(occ, R)                      # built once per block size
        for dname, px in defs:
            if len(px) < 100:
                continue
            sh_ = occ_hist(px, R)
            for zname in ZONES:
                st = score(sh_, oh, masks[zname])
                rows.append(dict(swing=dname, R=R, zone=zname, **st))

    print("\n%-14s %-6s %-11s %7s %8s %8s %7s %7s %9s"
          % ("swing def", "R", "zone", "n", "rate", "null", "z", "rank", "z_occ_adj"))
    for r in sorted(rows, key=lambda x: -x["z"])[:14]:
        print("%-14s %-6d %-11s %7d %7.4f %8.4f %+7.2f %4d/60 %+9.2f"
              % (r["swing"], r["R"], r["zone"], r["n"], r["rate"],
                 r["null_mean"], r["z"], r["rank"], r["z_occ_adj"]))

    allz = [r["z"] for r in rows]
    print("\n%d cells   z from %+.2f to %+.2f   |z|>3: %d"
          % (len(rows), min(allz), max(allz), sum(1 for z in allz if abs(z) > 3)))

    with open(os.path.join(HERE, "majorswing.json"), "w") as fh:
        json.dump(rows, fh, indent=1)
    print("wrote majorswing.json")


if __name__ == "__main__":
    main()
