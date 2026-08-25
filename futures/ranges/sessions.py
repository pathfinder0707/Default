"""Do SESSION HIGHS AND LOWS land on block boundaries?

Every test in this repo so far is about touches -- price arrives at a level,
what happens next. That is not what a trader sees when they pull up a chart and
say "look, the range held". What they see is the DAY: its high, its low, and
where those sit relative to the block.

That is a different claim and a cleanly falsifiable one. If the PO3 block is a
dealing range, then:

  1. the session high should sit near the block top and the session low near
     the block bottom, more often than an arbitrary lattice would give
  2. sessions should be CONTAINED inside a single block more often than chance
  3. and when they are not contained, the overshoot should be small

Each is measured against shifted lattices -- the identical geometry moved to a
different origin -- so the trivial fact that a 243-point block and a 250-point
day are similar sizes is differenced out. That similarity is the thing most
likely to make a chart look convincing, and it is exactly what the null
absorbs.

Sessions are the RTH cash session, 09:30 to 16:00 New York, and separately the
full 24-hour futures day, since the framework is applied to both.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NPHASE = 24
NBIN = 100


def session_extremes(h, l, date, tod, rth_only):
    """High, low and date for every session."""
    m = ((tod >= 930) & (tod < 1600)) if rth_only else np.ones(len(h), bool)
    d = date[m]
    hh, ll = h[m], l[m]
    u, inv = np.unique(d, return_inverse=True)
    hi = np.full(len(u), -np.inf)
    lo = np.full(len(u), np.inf)
    np.maximum.at(hi, inv, hh)
    np.minimum.at(lo, inv, ll)
    cnt = np.bincount(inv, minlength=len(u))
    ok = cnt >= 60
    return u[ok], hi[ok], lo[ok]


def block_pos(px, R, phase):
    return np.mod(px - R * phase / 100.0, R) / R * 100.0


def stats(hi, lo, R, phase):
    """Three numbers: edge clustering, containment, overshoot."""
    ph = block_pos(hi, R, phase)
    pl = block_pos(lo, R, phase)
    # 1. how near the top of a block is the session high, and the bottom the low?
    #    distance to the nearest boundary, as a percentage of the block
    d_hi = np.minimum(ph, 100.0 - ph)
    d_lo = np.minimum(pl, 100.0 - pl)
    # 2. contained: high and low fall in the same block
    k_hi = np.floor((hi - R * phase / 100.0) / R)
    k_lo = np.floor((lo - R * phase / 100.0) / R)
    contained = (k_hi == k_lo)
    # 3. for the contained ones, how much of the block did the day actually use
    used = (hi - lo) / R
    return {
        "near_edge_hi": float((d_hi <= 5.0).mean()),
        "near_edge_lo": float((d_lo <= 5.0).mean()),
        "med_dist_hi": float(np.median(d_hi)),
        "med_dist_lo": float(np.median(d_lo)),
        "contained": float(contained.mean()),
        "used_med": float(np.median(used)),
    }


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    h, l = np.asarray(npz["h"]), np.asarray(npz["l"])
    date = np.asarray(npz["date"])
    tod = np.asarray(npz["hh"]) * 100 + np.asarray(npz["mm"])

    out = {}
    for sess_name, rth in (("RTH 09:30-16:00", True), ("full 24h", False)):
        u, hi, lo = session_extremes(h, l, date, tod, rth)
        print("\n" + "=" * 78)
        print("%s   %s sessions" % (sess_name, "{:,}".format(len(u))))
        print("=" * 78)
        out[sess_name] = {}
        for R in (243.0, 729.0, 2187.0):
            t = stats(hi, lo, R, 0.0)
            nulls = [stats(hi, lo, R, j * 100.0 / NPHASE) for j in range(1, NPHASE)]

            def z(key):
                a = np.array([x[key] for x in nulls])
                s = a.std(ddof=1)
                return (t[key] - a.mean()) / s if s > 0 else 0.0, a.mean()

            print("\n  R=%d   (median day uses %.2f of a block)" % (R, t["used_med"]))
            print("    %-34s %9s %9s %8s"
                  % ("", "true", "shifted", "z"))
            rows = {}
            for key, lab in (("near_edge_hi", "session HIGH within 5% of an edge"),
                             ("near_edge_lo", "session LOW within 5% of an edge"),
                             ("contained", "whole session inside one block")):
                zz, nm = z(key)
                rows[key] = {"true": t[key], "null": nm, "z": zz}
                print("    %-34s %9.4f %9.4f %+8.2f" % (lab, t[key], nm, zz))
            for key, lab in (("med_dist_hi", "median distance, HIGH to edge (%)"),
                             ("med_dist_lo", "median distance, LOW to edge (%)")):
                zz, nm = z(key)
                rows[key] = {"true": t[key], "null": nm, "z": zz}
                print("    %-34s %9.2f %9.2f %+8.2f" % (lab, t[key], nm, zz))
            out[sess_name][str(int(R))] = rows

    json.dump(out, open(os.path.join(HERE, "sessions.json"), "w"), indent=1)
    print("\nwrote sessions.json")
    print("\nUnder a uniform null a session extreme lands within 5% of an edge")
    print("10% of the time, since 'within 5%' covers two 5-point strips of 100.")


if __name__ == "__main__":
    main()
