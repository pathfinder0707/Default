"""H1: do swing points cluster at GB levels?

Primary configuration, fixed in PREREG.md before running: R=2187, k=5,
tolerance +/-0.5pp. Tested against all three nulls (N1 occupancy, N2 phase,
N3 level-set), plus H1' (phase-agnostic best-of-60).

Everything is computed from histograms of block-position. Once prices are
binned, a phase shift is a circular roll of the level mask and a level-set
change is a different mask, so every null becomes a dot product. NBIN is a
multiple of NPHASE so the 60 phase shifts are exact bin rolls.
"""
import json
import os
import sys

import numpy as np

import gbr

HERE = os.path.dirname(os.path.abspath(__file__))
NBIN = 12000            # 0.00833pp resolution; 12000 / 60 = 200 bins per phase
NPHASE = 60
ROLL = NBIN // NPHASE
RNG = np.random.default_rng(20260824)
# bin CENTRES, so a level's mask width is exactly 2*tol and coverage matches
# the analytic value. Using left edges double-counts the endpoint and inflates
# GB coverage (which sits on integer percentages) relative to random sets.
GRID = (np.arange(NBIN) + 0.5) * (100.0 / NBIN)


def mask(levels, tol):
    """Boolean level mask over the NBIN block-position grid, circular."""
    d = np.abs(GRID[:, None] - np.asarray(levels)[None, :])
    d = np.minimum(d, 100.0 - d)
    return (d <= tol).any(axis=1)


def hist(price, R):
    """Histogram of block position over NBIN bins."""
    pct = np.mod(price, R) / R * 100.0
    idx = (pct * (NBIN / 100.0)).astype(np.int64)
    np.clip(idx, 0, NBIN - 1, out=idx)
    return np.bincount(idx, minlength=NBIN).astype(np.float64)


def rates_all_phases(h, m):
    """Hit rate of mask m against histogram h, for all 60 phase shifts.

    Phase j shifts the lattice origin up by j*R/60, which moves a price's
    block position DOWN by the same amount, i.e. rolls the mask up by j*ROLL.
    """
    n = h.sum()
    shifted = np.stack([np.roll(m, j * ROLL) for j in range(NPHASE)])
    return (shifted @ h) / n


def random_sets(n_sets, levels=gbr.LEVELS):
    """Random level sets matched to GB by construction.

    Takes GB's own multiset of circular gaps -- {3,4,4,6,6,...} -- permutes the
    order, and rotates to a random origin. This preserves the level count, the
    exact gap distribution and therefore the exact coverage, while changing
    which specific percentages are levels. That isolates "are these particular
    numbers special" from "would any twenty similarly-spaced lines do".

    A Dirichlet stick-breaking null was tried first and rejected: matching only
    the minimum gap leaves the null far more unevenly spaced than GB.
    """
    srt = np.sort(np.asarray(levels))
    gaps = np.diff(np.concatenate([srt, [srt[0] + 100.0]]))
    out = np.empty((n_sets, len(srt)))
    for i in range(n_sets):
        g = RNG.permutation(gaps)
        pos = np.concatenate([[0.0], np.cumsum(g)[:-1]])
        out[i] = np.mod(pos + RNG.uniform(0, 100), 100.0)
    return out


def run(R, k, tol, bars, n_sets=4000, verbose=True):
    h_, l_ = bars["h"], bars["l"]
    ih, il = gbr.swings(h_, l_, k)
    swing_px = np.concatenate([h_[ih], l_[il]])
    occ_px = np.concatenate([h_, l_])

    Hs = hist(swing_px, R)
    Ho = hist(occ_px, R)
    n = int(Hs.sum())

    m = mask(gbr.LEVELS, tol)
    cov = m.mean()

    sw_ph = rates_all_phases(Hs, m)     # 60 phases, swings
    oc_ph = rates_all_phases(Ho, m)     # 60 phases, occupancy
    adj_ph = sw_ph - oc_ph

    rate, occ_rate = float(sw_ph[0]), float(oc_ph[0])
    nh = int(round(rate * n))

    out = {
        "R": R, "k": k, "tol": tol,
        "n_swings": n, "n_highs": int(len(ih)), "n_lows": int(len(il)),
        "n_hits": nh, "coverage": float(cov),
        "rate": rate, "occ_rate": occ_rate,
        "lift_vs_uniform": rate / cov - 1.0,
        "lift_vs_occ": rate / occ_rate - 1.0,
        "z_uniform": float(gbr.binom_z(nh, n, cov)),
        "z_occ": float(gbr.binom_z(nh, n, occ_rate)),
        # --- N2 phase null ---
        "z_phase": float(gbr.zscore(sw_ph[0], sw_ph[1:])),
        "z_phase_adj": float(gbr.zscore(adj_ph[0], adj_ph[1:])),
        "phase_rank": int((sw_ph >= sw_ph[0]).sum()),
        "phase_rank_adj": int((adj_ph >= adj_ph[0]).sum()),
        "phase_best_j": int(sw_ph.argmax()),
        "phase_best": float(sw_ph.max()),
        "phase_rates": sw_ph.tolist(),
        "phase_adj": adj_ph.tolist(),
    }

    # ---- N3: level-set null, and H1' best-of-60 -------------------------
    srt = np.sort(gbr.LEVELS)
    min_gap = float(np.diff(np.concatenate([srt, [srt[0] + 100]])).min())
    sets = random_sets(n_sets)

    set_rate = np.empty(n_sets)          # true phase only  -> N3
    set_adjmax = np.empty(n_sets)        # best-of-60 adj   -> H1'
    for i in range(n_sets):
        mi = mask(sets[i], tol)
        s = rates_all_phases(Hs, mi)
        o = rates_all_phases(Ho, mi)
        set_rate[i] = s[0]
        set_adjmax[i] = (s - o).max()

    out["n_level_sets"] = n_sets
    out["levelset_min_gap"] = min_gap
    out["levelset_mean"] = float(set_rate.mean())
    out["z_levelset"] = float(gbr.zscore(rate, set_rate))
    out["levelset_rank"] = int((set_rate >= rate).sum() + 1)
    # H1': GB's best phase (occupancy-adjusted) vs random sets' best phase
    out["adjmax_gb"] = float(adj_ph.max())
    out["adjmax_null_mean"] = float(set_adjmax.mean())
    out["z_adjmax"] = float(gbr.zscore(adj_ph.max(), set_adjmax))
    out["adjmax_rank"] = int((set_adjmax >= adj_ph.max()).sum() + 1)

    if verbose:
        print("\n=== H1   R=%d  k=%d  tol=%.2fpp ===" % (R, k, tol))
        print("  swings               %d  (%d highs, %d lows)" % (n, len(ih), len(il)))
        print("  level coverage       %.4f of block" % cov)
        print("  swing hit rate       %.4f   (%d hits)" % (rate, nh))
        print("  occupancy hit rate   %.4f            <- N1 reference" % occ_rate)
        print("  lift vs uniform      %+6.2f%%   z = %+6.2f" % (out["lift_vs_uniform"] * 100, out["z_uniform"]))
        print("  lift vs occupancy    %+6.2f%%   z = %+6.2f   <- N1" % (out["lift_vs_occ"] * 100, out["z_occ"]))
        print("  N2 phase       true %.4f  shifted mean %.4f  z = %+6.2f  rank %2d/60"
              % (sw_ph[0], sw_ph[1:].mean(), out["z_phase"], out["phase_rank"]))
        print("     occ-adjusted                              z = %+6.2f  rank %2d/60"
              % (out["z_phase_adj"], out["phase_rank_adj"]))
        print("  N3 level-set   GB %.4f  random mean %.4f  z = %+6.2f  rank %d/%d"
              % (rate, set_rate.mean(), out["z_levelset"], out["levelset_rank"], n_sets))
        print("  H1' best-of-60 GB %+.5f  random mean %+.5f  z = %+6.2f  rank %d/%d"
              % (out["adjmax_gb"], out["adjmax_null_mean"], out["z_adjmax"],
                 out["adjmax_rank"], n_sets))
    return out


def main():
    bars = np.load(os.path.join(HERE, "bars.npz"))
    res = {"primary": run(2187, 5, 0.5, bars)}

    if "--grid" in sys.argv:
        grid = []
        for R in (81, 243, 729, 2187):
            for k in (3, 5, 10, 20):
                for tol in (0.25, 0.5, 1.0):
                    grid.append(run(R, k, tol, bars, n_sets=600, verbose=False))
                    g = grid[-1]
                    print("  R=%-5d k=%-3d tol=%.2f  n=%-7d rate=%.4f  "
                          "z_occ=%+6.2f  z_phase=%+6.2f  z_lset=%+6.2f"
                          % (R, k, tol, g["n_swings"], g["rate"],
                             g["z_occ"], g["z_phase"], g["z_levelset"]))
        res["grid"] = grid

    with open(os.path.join(HERE, "h1.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print("\nwrote h1.json")


if __name__ == "__main__":
    main()
