"""Everything at R=81 specifically, split by era.

R=81 is the block actually used on a 1-5 minute chart, and two of the tests in
this repo were never run at it -- the respect test and the boundary
sweep-and-reverse test both ran only at 729 and 2187.

The era split matters more here than anywhere else. A block is only usable if
it is large relative to a bar: when NQ traded at 3,000 with 1-point minute bars,
an 81-point block was ~80 bars wide and its 2.43-point zones were resolvable. At
30,000 with 16-point minute bars the same block is ~5 bars wide and its zones
sit below a single candle. If R=81 ever worked, it worked early, and this is the
test that would show it.

Same 60-phase lattice null throughout, and the same positive controls that
validated these measurements at the larger block sizes apply unchanged.
"""
import json
import os

import numpy as np

import gbr
import reaction as rx
import respect
import majorswing as ms

HERE = os.path.dirname(os.path.abspath(__file__))
R = 81.0
NPHASE = 60

ERAS = [("2010-2014", 2010, 2014), ("2015-2019", 2015, 2019),
        ("2020-2022", 2020, 2022), ("2023-2026", 2023, 2026)]


def resolution_table(raw):
    """Is an 81-point block even resolvable in each era?"""
    h, l, yr = raw["h"], raw["l"], raw["yr"]
    tod = raw["hh"] * 100 + raw["mm"]
    rth = (tod >= 930) & (tod < 1600)
    print("=== can R=81 even be resolved? ===")
    print("  %-11s %10s %10s %11s %13s %12s"
          % ("era", "med close", "med bar", "bar as %% of R", "bars per block", "zone / bar"))
    rows = []
    for lab, a, b in ERAS:
        s = (yr >= a) & (yr <= b) & rth
        bar = float(np.median((h - l)[s]))
        px = float(np.median(h[s]))
        rows.append({"era": lab, "med_close": px, "med_bar": bar,
                     "bar_pct_of_R": bar / R * 100, "bars_per_block": R / bar,
                     "zone_per_bar": (0.03 * R) / bar})
        print("  %-11s %10.0f %9.1fp %10.1f%% %13.1f %12.2f"
              % (lab, px, bar, bar / R * 100, R / bar, (0.03 * R) / bar))
    return rows


def respect_by_era(raw):
    """Penetration depth and hold rate at R=81, per era, vs 60 shifted phases."""
    print("\n=== respect: does price stop at an R=81 level? ===")
    print("  %-11s %9s %10s %10s %9s %9s"
          % ("era", "touches", "median pen", "null", "in points", "signed z"))
    out = []
    for lab, a, b in ERAS:
        sel = (raw["yr"] >= a) & (raw["yr"] <= b)
        bars = {k: raw[k][sel] for k in ("h", "l", "c")}
        fmax, fmin = rx.fwd_extremes_fast(bars["h"], bars["l"], respect.HORIZON)
        bars["_fmax"], bars["_fmin"] = fmax, fmin
        true = respect.measure(bars, R, 0.0)
        if not true:
            continue
        nulls = [respect.measure(bars, R, j * 100.0 / NPHASE) for j in range(1, NPHASE)]
        arr = np.array([m["median_pen"] for m in nulls if m])
        z = gbr.zscore(true["median_pen"], arr)
        row = {"era": lab, "n": true["n"], "median_pen": true["median_pen"],
               "null_mean": float(arr.mean()), "z_signed": float(-z),
               "pen_points": true["median_pen"] * R,
               "hold_rate": true["hold_rate"]}
        out.append(row)
        print("  %-11s %9s %10.4f %10.4f %8.1fp %+9.2f"
              % (lab, "{:,}".format(true["n"]), true["median_pen"],
                 arr.mean(), true["median_pen"] * R, -z))
    return out


def swings_by_era(raw):
    """Do major swings cluster in the named zones at R=81, per era?"""
    print("\n=== major swings in the named zones, R=81 ===")
    print("  %-11s %-12s %8s %8s %8s %8s %8s"
          % ("era", "zone", "n", "rate", "null", "z", "z_occ_adj"))
    masks = {z: ms.zone_mask(b) for z, b in ms.ZONES.items()}
    out = []
    for lab, a, b in ERAS:
        sel = (raw["yr"] >= a) & (raw["yr"] <= b)
        h, l = raw["h"][sel], raw["l"][sel]
        sh, sl = ms.zigzag(h, l, 0.005)          # ~0.5% legs, a real swing
        px = np.concatenate([sh, sl])
        if len(px) < 200:
            continue
        occ = np.concatenate([h, l])
        oh = ms.occ_hist(occ, R)
        shist = ms.occ_hist(px, R)
        for zname in ms.ZONES:
            st = ms.score(shist, oh, masks[zname])
            out.append(dict(era=lab, zone=zname, **st))
            print("  %-11s %-12s %8d %8.4f %8.4f %+8.2f %+8.2f"
                  % (lab, zname, st["n"], st["rate"], st["null_mean"],
                     st["z"], st["z_occ_adj"]))
    return out


def boundary_by_era(raw):
    """Sweep-and-reverse at R=81 block edges, per era."""
    print("\n=== block-boundary sweep and reverse, R=81 ===")
    print("  %-11s %10s %10s %10s %9s" % ("era", "crossings", "reverse", "null", "z"))
    out = []
    for lab, a, b in ERAS:
        sel = (raw["yr"] >= a) & (raw["yr"] <= b)
        h, l, c = raw["h"][sel], raw["l"][sel], raw["c"][sel]
        fmax, fmin = rx.fwd_extremes_fast(h, l, 60)

        def rate(phase):
            off = R * phase / 100.0
            k = np.floor((c - off) / R).astype(np.int64)
            dn = np.flatnonzero(k[1:] < k[:-1]) + 1
            up = np.flatnonzero(k[1:] > k[:-1]) + 1
            dn = rx.dedup(dn[dn + 60 < len(c)], 60)
            up = rx.dedup(up[up + 60 < len(c)], 60)
            b_dn = R * k[dn - 1] + off
            b_up = R * k[up] + off
            ok_d, ok_u = np.isfinite(fmax[dn]), np.isfinite(fmin[up])
            n = int(ok_d.sum() + ok_u.sum())
            r = int((fmax[dn] > b_dn)[ok_d].sum() + (fmin[up] < b_up)[ok_u].sum())
            return (r / n if n else np.nan), n

        t, n = rate(0.0)
        arr = np.array([rate(j * 100.0 / NPHASE)[0] for j in range(1, NPHASE)])
        z = gbr.zscore(t, arr)
        out.append({"era": lab, "n": n, "rate": float(t),
                    "null_mean": float(arr.mean()), "z": float(z)})
        print("  %-11s %10s %10.4f %10.4f %+9.2f"
              % (lab, "{:,}".format(n), t, arr.mean(), z))
    return out


def main():
    raw = np.load(os.path.join(HERE, "bars.npz"))
    res = {"resolution": resolution_table(raw),
           "respect": respect_by_era(raw),
           "swings": swings_by_era(raw),
           "boundary": boundary_by_era(raw)}
    with open(os.path.join(HERE, "po3_81.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print("\nwrote po3_81.json")


if __name__ == "__main__":
    main()
