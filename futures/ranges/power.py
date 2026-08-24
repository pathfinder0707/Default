"""Power analysis: what size of effect would these tests have caught?

A null result only means something if the test could have seen a real effect.
This injects synthetic effects of known size into the real data and reports the
smallest one that clears the pre-registered 3 sigma bar.

Not a hypothesis test -- it adds no new claim about the framework, it
calibrates the ones already made.
"""
import json
import os

import numpy as np

import gbr
import h1 as H1
import reaction as rx

HERE = os.path.dirname(os.path.abspath(__file__))
RNG = np.random.default_rng(7)


def snap_fraction(px, R, frac):
    """Move a random `frac` of prices onto their nearest GB level."""
    px = px.copy()
    n = len(px)
    pick = RNG.random(n) < frac
    if not pick.any():
        return px
    p = px[pick]
    pct = np.mod(p, R) / R * 100.0
    d = pct[:, None] - gbr.LEVELS[None, :]
    d = np.where(np.abs(d) > 50, d - np.sign(d) * 100.0, d)
    j = np.argmin(np.abs(d), axis=1)
    px[pick] = p - d[np.arange(len(p)), j] / 100.0 * R
    return px


def power_h1(bars, R=2187, k=5, tol=0.5):
    h_, l_ = bars["h"], bars["l"]
    ih, il = gbr.swings(h_, l_, k)
    swing_px = np.concatenate([h_[ih], l_[il]])
    occ_px = np.concatenate([h_, l_])
    Ho = H1.hist(occ_px, R)
    m = H1.mask(gbr.LEVELS, tol)

    rows = []
    for frac in (0.0, 0.005, 0.01, 0.02, 0.03, 0.05):
        px = snap_fraction(swing_px, R, frac)
        Hs = H1.hist(px, R)
        sw = H1.rates_all_phases(Hs, m)
        z = gbr.zscore(sw[0], sw[1:])
        rows.append({"frac": frac, "rate": float(sw[0]), "z_phase": float(z)})
        print("    inject %5.1f%% of swings onto levels -> rate %.4f  z_phase %+7.2f"
              % (frac * 100, sw[0], z))
    return rows


def power_reaction(bars, R=2187, M=60):
    """Nudge the reject rate at true-lattice touches and re-score vs the null."""
    # reproduce the true-phase touch outcomes once
    h, l, c = bars["h"], bars["l"], bars["c"]
    fmax, fmin = bars["_fmax%d" % M], bars["_fmin%d" % M]
    n = len(h)
    outcomes = []
    for pct in gbr.LEVELS:
        t = rx.touches(l, h, R, pct, 0.0)
        idx = np.flatnonzero(t)
        idx = idx[(idx >= rx.APPROACH_W) & (idx + M < n)]
        idx = rx.dedup(idx, M)
        if len(idx) == 0:
            continue
        L = rx.level_price(c[idx], R, pct, 0.0)
        fb = c[idx - rx.APPROACH_W] < L
        up, dn = fmax[idx] - L, L - fmin[idx]
        ok = np.isfinite(up) & np.isfinite(dn)
        outcomes.append(np.where(fb, dn > up, up > dn)[ok])
    obs = np.concatenate(outcomes)

    null = np.array([rx.measure(bars, R, M, j * 100.0 / rx.NPHASE)["reject_rate"]
                     for j in range(1, rx.NPHASE)])
    sd = null.std(ddof=1)

    rows = []
    for lift in (0.0, 0.005, 0.01, 0.015, 0.02, 0.03):
        x = obs.copy()
        flip = (~x) & (RNG.random(len(x)) < lift / max(1e-9, (~x).mean()))
        x = x | flip
        rate = x.mean()
        z = (rate - null.mean()) / sd
        rows.append({"lift": lift, "rate": float(rate), "z_phase": float(z)})
        print("    reject rate +%.1fpp -> %.4f  z_phase %+7.2f" % (lift * 100, rate, z))
    return rows


def main():
    raw = np.load(os.path.join(HERE, "bars.npz"))
    bars = {k: raw[k] for k in ("h", "l", "c")}
    M = 60
    fmax, fmin = rx.fwd_extremes_fast(bars["h"], bars["l"], M)
    bars["_fmax%d" % M] = fmax
    bars["_fmin%d" % M] = fmin

    print("\n=== power: H1 swing clustering (R=2187, k=5, tol=0.5) ===")
    h1rows = power_h1(bars)
    print("\n=== power: level reaction (R=2187, M=60) ===")
    rxrows = power_reaction(bars)

    with open(os.path.join(HERE, "power.json"), "w") as fh:
        json.dump({"h1": h1rows, "reaction": rxrows}, fh, indent=1)
    print("\nwrote power.json")


if __name__ == "__main__":
    main()
