"""Does price RESPECT a Goldbach level? (as opposed to: does it predict direction)

Everything tested so far asked directional questions -- do swings land on levels,
does a touch predict a reject. Those all came back at chance. But that is not
what a discretionary trader means by "these levels are accurate". They mean
price arrives and *stops*: it does not slice through, it turns near the line.

That is a direction-agnostic claim about penetration depth, and it has not been
tested. It is also the strongest remaining version of the framework, because a
level can be worthless for prediction and still be real support/resistance.

Two measurements, each against the same 60-phase lattice null:

  1. PENETRATION  -- on first touch from above, how far below the line does
                     price trade over the next N bars? Real support penetrates
                     shallower than an arbitrary line.
  2. HOLD RATE    -- fraction of touches where penetration stays under a small
                     threshold before price returns to the line.
  (A third metric, time spent stalling near the line, was dropped: a positive
  control in which the levels were true reflecting barriers moved it the WRONG
  way -- price that genuinely bounces leaves the area rather than lingering, so
  it does not measure respect.)

A shallower median penetration or a higher hold rate at the true lattice than at
its 59 shifted twins would be the first positive result in this investigation.

Validated on a positive control before being run on real data: a synthetic
series in which the levels are true reflecting barriers gives median penetration
0.09% of R against 1.42% for the shifted lattices, a 15x gap the test resolves
clearly. So a null here means the effect is absent, not that the test is blind.
"""
import json
import os

import numpy as np

import gbr
import reaction as rx

HERE = os.path.dirname(os.path.abspath(__file__))
NPHASE = 60
HORIZON = 60          # bars to measure penetration over
APPROACH_W = 5        # bars back used to establish approach side
DEDUP = 60


def measure(bars, R, phase, horizon=HORIZON, stall_frac=0.02):
    """Penetration depth, hold rate and stall time at this lattice phase.

    Depth is expressed as a FRACTION OF R so it is comparable across block
    sizes and across the 18-fold price change in the sample.
    """
    h, l, c = bars["h"], bars["l"], bars["c"]
    n = len(h)
    fmin, fmax = bars["_fmin"], bars["_fmax"]

    depths, holds = [], []
    band = stall_frac * R

    for pct in gbr.LEVELS:
        t = rx.touches(l, h, R, pct, phase)
        idx = np.flatnonzero(t)
        idx = idx[(idx >= APPROACH_W) & (idx + horizon < n)]
        idx = rx.dedup(idx, DEDUP)
        if len(idx) == 0:
            continue
        L = rx.level_price(c[idx], R, pct, phase)
        from_above = c[idx - APPROACH_W] > L

        # penetration beyond the line, in the direction of travel
        below = L - fmin[idx]          # how far under the line price went
        above = fmax[idx] - L          # how far over
        pen = np.where(from_above, below, above)
        ok = np.isfinite(pen)
        pen = pen[ok]
        if len(pen) == 0:
            continue
        depths.append(pen / R)
        # "held" = penetrated less than 2% of the block before turning
        holds.append((pen < band).astype(np.float64))

    if not depths:
        return None
    d = np.concatenate(depths)
    hd = np.concatenate(holds)
    return {
        "n": int(len(d)),
        "median_pen": float(np.median(d)),
        "mean_pen": float(d.mean()),
        "hold_rate": float(hd.mean()),
    }


def run(bars, R):
    true = measure(bars, R, 0.0)
    keys = ("median_pen", "mean_pen", "hold_rate")
    nulls = {k: [] for k in keys}
    for j in range(1, NPHASE):
        m = measure(bars, R, j * 100.0 / NPHASE)
        if not m:
            continue
        for k in keys:
            nulls[k].append(m[k])

    print("\n=== respect  R=%d  (%s touches) ===" % (R, "{:,}".format(true["n"])))
    print("  %-14s %10s %10s %8s %8s   %s"
          % ("measure", "true", "null mean", "null sd", "z", "direction that would support the framework"))
    out = {"R": R, "n": true["n"]}
    for k, better in (("median_pen", "lower"), ("mean_pen", "lower"),
                      ("hold_rate", "higher")):
        a = np.array(nulls[k])
        z = gbr.zscore(true[k], a)
        # sign the z so positive always means "supports the framework"
        zs = -z if better == "lower" else z
        out[k] = {"true": true[k], "null_mean": float(a.mean()),
                  "null_sd": float(a.std(ddof=1)), "z": float(z), "z_signed": float(zs)}
        print("  %-14s %10.5f %10.5f %8.5f %+8.2f   %s -> signed z %+.2f"
              % (k, true[k], a.mean(), a.std(ddof=1), z, better, zs))
    return out


def main():
    raw = np.load(os.path.join(HERE, "bars.npz"))
    bars = {k: raw[k] for k in ("h", "l", "c")}
    fmax, fmin = rx.fwd_extremes_fast(bars["h"], bars["l"], HORIZON)
    bars["_fmax"], bars["_fmin"] = fmax, fmin

    res = [run(bars, R) for R in (729, 2187)]
    with open(os.path.join(HERE, "respect.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print("\nwrote respect.json")


if __name__ == "__main__":
    main()
