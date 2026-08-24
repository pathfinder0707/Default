"""Structural tests of the trade plans (H2, H4, H5) plus the round-number check.

H2  rebalance dwell        -- does price linger in [41-59]?
H4  GIP invalidation       -- does passing [17-83] predict reaching the flow layer?
H5  boundary sweep/reverse -- the framework's core claim: PO3 block boundaries
                              get swept for liquidity and then reject.

Every test is scored against the same 60-phase lattice null used elsewhere, and
H5 additionally against a round-decimal lattice, which is the price analogue of
the round-clock artifact that produced a spurious +4.86 sigma in the GB-time run.
"""
import json
import os

import numpy as np

import gbr
import reaction as rx

HERE = os.path.dirname(os.path.abspath(__file__))
NPHASE = 60
M_DEFAULT = 60


# ---------------------------------------------------------------- H2 dwell
def dwell(close, R, phase, lo, hi):
    """Fraction of bar closes inside a [lo,hi] percentage band of the block."""
    pct = np.mod(close - R * phase / 100.0, R) / R * 100.0
    return float(((pct >= lo) & (pct < hi)).mean())


def run_dwell(bars):
    close = bars["c"]
    out = []
    for R in (729, 2187):
        for name, (lo, hi) in gbr.LAYERS.items():
            true = dwell(close, R, 0.0, lo, hi)
            null = np.array([dwell(close, R, j * 100.0 / NPHASE, lo, hi)
                             for j in range(1, NPHASE)])
            width = (hi - lo) / 100.0
            z = gbr.zscore(true, null)
            out.append({
                "R": R, "layer": name, "lo": lo, "hi": hi, "width": width,
                "dwell": true, "null_mean": float(null.mean()),
                "z_phase": float(z),
                "rank": int((null >= true).sum() + 1),
            })
            print("  R=%-5d %-14s width %.2f  dwell %.4f  null %.4f  z=%+6.2f  rank %2d/60"
                  % (R, name, width, true, null.mean(), z, out[-1]["rank"]))
    return out


# ------------------------------------------------------------ H5 sweep/reverse
def sweep_reverse(bars, R, phase, M):
    """P(price returns above a lattice boundary it just crossed downward).

    Mirrored for upward crossings. This is the framework's liquidity mechanic:
    the block edge is swept, then rejects back into the range.
    """
    c = bars["c"]
    fmax = bars["_fmax%d" % M]
    fmin = bars["_fmin%d" % M]
    n = len(c)

    off = R * phase / 100.0
    idx = np.floor((c - off) / R).astype(np.int64)

    down = np.flatnonzero((idx[1:] < idx[:-1])) + 1
    up = np.flatnonzero((idx[1:] > idx[:-1])) + 1
    down = rx.dedup(down[down + M < n], M)
    up = rx.dedup(up[up + M < n], M)

    # boundary that was crossed
    b_dn = R * idx[down - 1] + off
    b_up = R * idx[up] + off

    rev_dn = fmax[down] > b_dn
    rev_up = fmin[up] < b_up
    ok_dn = np.isfinite(fmax[down])
    ok_up = np.isfinite(fmin[up])

    nn = int(ok_dn.sum() + ok_up.sum())
    rr = int(rev_dn[ok_dn].sum() + rev_up[ok_up].sum())
    return {"n": nn, "rate": rr / nn if nn else float("nan")}


def run_sweep(bars, M=M_DEFAULT):
    out = []
    for R in (729, 2187):
        true = sweep_reverse(bars, R, 0.0, M)
        null = np.array([sweep_reverse(bars, R, j * 100.0 / NPHASE, M)["rate"]
                         for j in range(1, NPHASE)])
        z = gbr.zscore(true["rate"], null)
        rank = int((null >= true["rate"]).sum() + 1)
        print("  R=%-5d crossings %6d  reverse %.4f  null %.4f  z=%+6.2f  rank %2d/60"
              % (R, true["n"], true["rate"], null.mean(), z, rank))
        out.append({"R": R, "M": M, "n": true["n"], "rate": true["rate"],
                    "null_mean": float(null.mean()), "z_phase": float(z),
                    "rank": rank, "null_rates": null.tolist()})
    return out


def run_round_check(bars, M=M_DEFAULT):
    """The round-decimal control.

    If the lattice result is null but round decimal levels show the same
    measurement clearly, that tells us the test has power and the lattice
    specifically lacks the effect. If round decimals are null too, the
    statistic simply may not discriminate.
    """
    out = []
    for R in (100, 250, 500, 1000):
        true = sweep_reverse(bars, R, 0.0, M)
        null = np.array([sweep_reverse(bars, R, j * 100.0 / NPHASE, M)["rate"]
                         for j in range(1, NPHASE)])
        z = gbr.zscore(true["rate"], null)
        print("  round %-5d crossings %6d  reverse %.4f  null %.4f  z=%+6.2f"
              % (R, true["n"], true["rate"], null.mean(), z))
        out.append({"R": R, "n": true["n"], "rate": true["rate"],
                    "null_mean": float(null.mean()), "z_phase": float(z)})
    return out


# ------------------------------------------------------------------- H4 GIP
def gip(bars, R, phase, M):
    """P(reach flow layer | passed the GIP) vs P(reach flow layer | held it).

    Restricted to the lower half of the block: touch [11-] moving down, then
    ask whether price passed 17 downward, and whether it later reached the flow
    layer (35 down to 23).
    """
    c = bars["c"]
    fmin = bars["_fmin%d" % M]
    n = len(c)
    off = R * phase / 100.0
    pct = np.mod(c - off, R) / R * 100.0
    blk = np.floor((c - off) / R).astype(np.int64)

    # events: close crosses below 11% within a block
    ev = np.flatnonzero((pct[1:] < 11) & (pct[:-1] >= 11) & (blk[1:] == blk[:-1])) + 1
    ev = rx.dedup(ev[ev + M < n], M)
    if len(ev) == 0:
        return {"n": 0}

    base = R * blk[ev] + off
    gip_px = base + R * 0.17
    flow_px = base + R * 0.35
    lo_reach = fmin[ev]
    ok = np.isfinite(lo_reach)

    passed = lo_reach < gip_px            # went below the GIP
    reached = lo_reach < flow_px          # reached the flow layer

    # NB reached implies passed here (35 < 17 is false -- flow is BELOW gip on
    # the downside only if 35 > 17, which it is, so flow_px > gip_px).
    # Downside order from 11: 7, 3, 0 ... the flow layer at 23-35 is ABOVE 11.
    return {"n": int(ok.sum()), "passed": float(passed[ok].mean()),
            "reached": float(reached[ok].mean())}


def main():
    raw = np.load(os.path.join(HERE, "bars.npz"))
    bars = {k: raw[k] for k in ("h", "l", "c")}
    for M in (M_DEFAULT,):
        fmax, fmin = rx.fwd_extremes_fast(bars["h"], bars["l"], M)
        bars["_fmax%d" % M] = fmax
        bars["_fmin%d" % M] = fmin

    res = {}
    print("\n=== H2  layer dwell ===")
    res["dwell"] = run_dwell(bars)
    print("\n=== H5  block boundary sweep-and-reverse (M=%d) ===" % M_DEFAULT)
    res["sweep"] = run_sweep(bars)
    print("\n=== round-decimal control ===")
    res["round"] = run_round_check(bars)

    with open(os.path.join(HERE, "structure.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print("\nwrote structure.json")


if __name__ == "__main__":
    main()
