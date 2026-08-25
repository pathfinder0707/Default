"""Is there a CONDITION under which major swings cluster at the range extreme?

Every earlier test asked the unconditional question and got chance. This asks
the harder one: does some regime switch the effect on -- "when X holds, major
swings form at the 0-3 / 97-100 partition Y% of the time".

Searching conditions is how false positives get manufactured, so the design is
built against that:

  * DISCOVERY on 2010-2018, VALIDATION on 2019-2026. A condition only counts if
    it survives on data it was never selected on. This is the real filter; the
    z-scores in discovery are treated as candidate generation, nothing more.
  * Every condition is LATTICE-INDEPENDENT (session, hour, weekday, volatility
    regime, trend regime, swing size). Shifting the lattice phase therefore
    leaves the swing subset identical and moves only the zone, so the 60-phase
    null stays exactly matched inside every condition.
  * Occupancy is conditioned the same way wherever the condition is defined per
    bar, so "swings cluster here" is never just "price is here".

The zone is EXT = 97-100 and 0-3, six percentage points, so 6.0% is the
uniform expectation. Also reported for EQ as a control zone.
"""
import json
import os

import numpy as np

import majorswing as ms

HERE = os.path.dirname(os.path.abspath(__file__))
NPHASE = 60
SPLIT_YEAR = 2019          # < SPLIT_YEAR discovers, >= validates


def zigzag_idx(h, l, pct_thresh):
    """Zigzag returning bar index, price and side for each confirmed swing."""
    n = len(h)
    up = True
    ext = h[0]
    ext_i = 0
    idx, px, is_high = [], [], []
    for i in range(1, n):
        if up:
            if h[i] > ext:
                ext, ext_i = h[i], i
            elif l[i] < ext * (1.0 - pct_thresh):
                idx.append(ext_i); px.append(ext); is_high.append(True)
                up = False; ext, ext_i = l[i], i
        else:
            if l[i] < ext:
                ext, ext_i = l[i], i
            elif h[i] > ext * (1.0 + pct_thresh):
                idx.append(ext_i); px.append(ext); is_high.append(False)
                up = True; ext, ext_i = h[i], i
    return (np.array(idx, np.int64), np.array(px, np.float64),
            np.array(is_high, bool))


def features(raw, idx, px):
    """Per-swing context. All lattice-independent by construction."""
    c, yr = np.asarray(raw["c"]), np.asarray(raw["yr"])
    tod = np.asarray(raw["hh"]) * 100 + np.asarray(raw["mm"])
    n = len(c)

    # trailing realised volatility: 1-day (1440 bar) range, as a fraction.
    # NOTE: bind h and l to locals first. `raw` is a lazy NpzFile, so indexing
    # raw["h"] inside the comprehension re-decompresses the whole 38MB array on
    # every iteration -- 22k swings turned a one-second loop into minutes.
    H, L = np.asarray(raw["h"]), np.asarray(raw["l"])
    look = 1440
    prev = np.maximum(idx - look, 0)
    vol = np.array([H[a:b].max() - L[a:b].min()
                    for a, b in zip(prev, idx + 1)]) / px

    # trend: net move over the prior day, relative to that day's range
    back = c[np.maximum(idx - look, 0)]
    trend = np.abs(c[np.minimum(idx, n - 1)] - back) / np.maximum(px * vol, 1e-9)

    # leg size: distance from the previous confirmed swing
    leg = np.abs(np.diff(px, prepend=px[0])) / px

    return {
        "tod": tod[idx], "yr": yr[idx], "vol": vol, "trend": trend, "leg": leg,
        "dow": (np.asarray(raw["date"])[idx] % 100) % 7,
    }


def conditions(f, is_high):
    """Named boolean masks over the swing set."""
    t, v, tr, lg = f["tod"], f["vol"], f["trend"], f["leg"]
    qv = np.nanpercentile(v, [33, 67])
    qt = np.nanpercentile(tr, [33, 67])
    ql = np.nanpercentile(lg, [50, 80, 95])
    return {
        "ALL": np.ones(len(t), bool),
        "RTH": (t >= 930) & (t < 1600),
        "NY_open_hr": (t >= 930) & (t < 1030),
        "London": (t >= 300) & (t < 530),
        "Asia": (t >= 2000) | (t < 200),
        "overnight": (t < 930) | (t >= 1600),
        "vol_low": v <= qv[0],
        "vol_mid": (v > qv[0]) & (v <= qv[1]),
        "vol_high": v > qv[1],
        "trend_low": tr <= qt[0],
        "trend_mid": (tr > qt[0]) & (tr <= qt[1]),
        "trend_high": tr > qt[1],
        "leg_small": lg <= ql[0],
        "leg_big": lg > ql[1],
        "leg_huge": lg > ql[2],
        "swing_high": is_high,
        "swing_low": ~is_high,
    }


def score_subset(px_sub, oh, R, mask):
    """Zone rate at the true phase vs 59 shifted, for this swing subset.

    `oh` is the prebuilt occupancy histogram for this block size -- rebuilding
    it from the 9.5M-element price array on each of 400+ calls is the same
    redundant work that made the first major-swing run unusably slow.
    """
    if len(px_sub) < 150:
        return None
    sh = ms.occ_hist(px_sub, R)
    rates = ms.rates_all_phases(sh, mask)
    occ = ms.rates_all_phases(oh, mask)
    adj = rates - occ
    sd, sda = rates[1:].std(ddof=1), adj[1:].std(ddof=1)
    return {
        "n": int(len(px_sub)),
        "rate": float(rates[0]),
        "null_mean": float(rates[1:].mean()),
        "z": float((rates[0] - rates[1:].mean()) / sd) if sd > 0 else 0.0,
        "occ_rate": float(occ[0]),
        "z_occ_adj": float((adj[0] - adj[1:].mean()) / sda) if sda > 0 else 0.0,
    }


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    raw = {k: npz[k] for k in npz.files}      # materialise once, not per access
    h, l = raw["h"], raw["l"]
    masks = {"EXT": ms.zone_mask(ms.ZONES["EXT_97_100"]),
             "EQ": ms.zone_mask(ms.ZONES["EQ_47_53"])}

    results = []
    # one threshold: 22,336 confirmed swings is an ample sample, and this
    # container recycles faster than a second 4.8M-bar zigzag pass completes
    for thr in (0.005,):
        # cache the zigzag: it is a pure-Python pass over 4.8M bars and this
        # container recycles, which otherwise restarts the whole job from zero
        cache = os.path.join(HERE, "zz_%d.npz" % round(thr * 10000))
        if os.path.exists(cache):
            z = np.load(cache)
            idx, px, is_high = z["idx"], z["px"], z["is_high"]
            print("loaded cached zigzag %.2f%%" % (thr * 100))
        else:
            idx, px, is_high = zigzag_idx(h, l, thr)
            np.savez_compressed(cache, idx=idx, px=px, is_high=is_high)
        f = features(raw, idx, px)
        conds = conditions(f, is_high)
        print("\nzigzag %.2f%%: %s swings, %d conditions"
              % (thr * 100, "{:,}".format(len(px)), len(conds)))

        disc = f["yr"] < SPLIT_YEAR
        val = ~disc
        occ_all = np.concatenate([h, l])
        occ_hists = {R: ms.occ_hist(occ_all, R) for R in (81, 243, 729)}

        for R in (81, 243, 729):
            oh = occ_hists[R]
            for cname, cm in conds.items():
                for zname, zmask in masks.items():
                    a = score_subset(px[cm & disc], oh, R, zmask)
                    b = score_subset(px[cm & val], oh, R, zmask)
                    if not a or not b:
                        continue
                    results.append({
                        "thr": thr, "R": R, "cond": cname, "zone": zname,
                        "disc_n": a["n"], "disc_rate": a["rate"], "disc_z": a["z"],
                        "val_n": b["n"], "val_rate": b["rate"], "val_z": b["z"],
                        "disc_occadj": a["z_occ_adj"], "val_occadj": b["z_occ_adj"],
                    })

    print("\n%d condition cells searched" % len(results))
    print("\n=== strongest in DISCOVERY (2010-2018), with their VALIDATION result ===")
    print("  %-6s %-5s %-12s %-4s %7s %7s %8s   %7s %7s %8s"
          % ("thr", "R", "condition", "zone", "n", "rate", "z", "n", "rate", "z"))
    for r in sorted(results, key=lambda x: -x["disc_z"])[:15]:
        print("  %-6.3f %-5d %-12s %-4s %7d %7.4f %+8.2f   %7d %7.4f %+8.2f"
              % (r["thr"], r["R"], r["cond"], r["zone"],
                 r["disc_n"], r["disc_rate"], r["disc_z"],
                 r["val_n"], r["val_rate"], r["val_z"]))

    surv = [r for r in results if r["disc_z"] > 2 and r["val_z"] > 2]
    print("\ncells with z>2 in BOTH halves: %d of %d" % (len(surv), len(results)))
    for r in surv:
        print("  SURVIVES: thr=%.3f R=%d %s %s  disc z %+.2f  val z %+.2f"
              % (r["thr"], r["R"], r["cond"], r["zone"], r["disc_z"], r["val_z"]))

    dz = [r["disc_z"] for r in results]
    vz = [r["val_z"] for r in results]
    print("\ndiscovery z: %+.2f to %+.2f    validation z: %+.2f to %+.2f"
          % (min(dz), max(dz), min(vz), max(vz)))
    print("correlation between discovery z and validation z: %+.3f"
          % np.corrcoef(dz, vz)[0, 1])

    with open(os.path.join(HERE, "conditional.json"), "w") as fh:
        json.dump(results, fh, indent=1)
    print("wrote conditional.json")


if __name__ == "__main__":
    main()
