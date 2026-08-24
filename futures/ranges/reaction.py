"""Level reaction test: does touching a GB level predict anything?

The swing-clustering test (H1) asks whether turning points sit on levels. This
asks the question a trader actually faces: price is arriving at a level -- does
it reject or go through, and does that beat the same measurement on a lattice
whose origin has been shifted?

Statistic: on a deduplicated first touch of level L approached from below,
"reject" means price travels further DOWN than UP over the next M bars. For an
approach from above, mirrored. With symmetric excursion this is equivalent to a
symmetric bracket around L -- which side would be hit first.

Null: the same measurement under 60 lattice phase offsets. The true lattice is
phase 0.
"""
import json
import os

import numpy as np

import gbr

HERE = os.path.dirname(os.path.abspath(__file__))
NPHASE = 60
HORIZONS = (15, 60, 240)     # minutes forward
APPROACH_W = 15              # bars back used to classify approach direction


def fwd_extremes(high, low, m):
    """max(high) and min(low) over bars (i, i+m], via a sliding window.

    Strided reduction, O(n log m) passes rather than a Python loop over bars.
    """
    n = len(high)
    fmax = np.full(n, -np.inf)
    fmin = np.full(n, np.inf)
    # running window built by doubling
    h = high.copy()
    l = low.copy()
    step = 1
    span = 0
    while span < m:
        take = min(step, m - span)
        # combine value at offset span+1 .. span+take
        idx = np.arange(n)
        src = idx + span + 1
        ok = src + take - 1 < n
        # block max over [src, src+take)
        blk_h = np.full(n, -np.inf)
        blk_l = np.full(n, np.inf)
        for t in range(take):
            s = idx + span + 1 + t
            v = s < n
            blk_h[v] = np.maximum(blk_h[v], high[s[v]])
            blk_l[v] = np.minimum(blk_l[v], low[s[v]])
        fmax = np.maximum(fmax, blk_h)
        fmin = np.minimum(fmin, blk_l)
        span += take
        step *= 2
    return fmax, fmin


def fwd_extremes_fast(high, low, m):
    """Same as fwd_extremes but O(n*log m) using sparse-table doubling."""
    n = len(high)
    # sparse table over forward windows
    logs = 1
    while (1 << logs) <= m:
        logs += 1
    tab_h = [high.copy()]
    tab_l = [low.copy()]
    for j in range(1, logs):
        prev_h, prev_l = tab_h[-1], tab_l[-1]
        half = 1 << (j - 1)
        cur_h = prev_h.copy()
        cur_l = prev_l.copy()
        cur_h[:n - half] = np.maximum(prev_h[:n - half], prev_h[half:])
        cur_l[:n - half] = np.minimum(prev_l[:n - half], prev_l[half:])
        tab_h.append(cur_h)
        tab_l.append(cur_l)
    # window [i+1, i+m] -> start s=i+1, length m
    j = (m).bit_length() - 1
    if (1 << j) > m:
        j -= 1
    span = 1 << j
    s = np.arange(n) + 1
    a = np.clip(s, 0, n - 1)
    b = np.clip(s + m - span, 0, n - 1)
    fmax = np.maximum(tab_h[j][a], tab_h[j][b])
    fmin = np.minimum(tab_l[j][a], tab_l[j][b])
    # bars whose full window runs past the end are invalid
    valid = (np.arange(n) + m) < n
    fmax[~valid] = np.nan
    fmin[~valid] = np.nan
    return fmax, fmin


def touches(low, high, R, pct, phase):
    """Boolean: does each bar span the level at this block percentage?

    Level prices are R*(k + p/100) for integer k, with the lattice origin
    shifted by `phase` percentage points. A bar [low, high] contains one iff
    floor(high/R - p) >= ceil(low/R - p).
    """
    p = (pct + phase) / 100.0
    a = low / R - p
    b = high / R - p
    return np.floor(b) >= np.ceil(a)


def level_price(price, R, pct, phase):
    """The lattice level of this percentage nearest to `price`."""
    p = (pct + phase) / 100.0
    return R * (np.round(price / R - p) + p)


def dedup(idx, gap):
    """Keep touches at least `gap` bars apart (first-come)."""
    if len(idx) == 0:
        return idx
    keep = [idx[0]]
    last = idx[0]
    for i in idx[1:]:
        if i - last >= gap:
            keep.append(i)
            last = i
    return np.asarray(keep)


def measure(bars, R, M, phase, per_level=False):
    """Reject rate over all GB levels at this lattice phase."""
    h, l, c = bars["h"], bars["l"], bars["c"]
    fmax, fmin = bars["_fmax%d" % M], bars["_fmin%d" % M]
    n = len(h)

    tot = 0
    rej = 0
    by_level = {}
    for pct in gbr.LEVELS:
        t = touches(l, h, R, pct, phase)
        idx = np.flatnonzero(t)
        idx = idx[(idx >= APPROACH_W) & (idx + M < n)]
        idx = dedup(idx, M)
        if len(idx) == 0:
            continue
        L = level_price(c[idx], R, pct, phase)
        from_below = c[idx - APPROACH_W] < L
        up = fmax[idx] - L
        dn = L - fmin[idx]
        ok = np.isfinite(up) & np.isfinite(dn)
        # reject = price travels further against the approach
        r = np.where(from_below, dn > up, up > dn)
        r = r[ok]
        tot += len(r)
        rej += int(r.sum())
        if per_level:
            by_level[int(pct)] = {
                "n": int(len(r)),
                "reject_rate": float(r.mean()) if len(r) else float("nan"),
                "n_from_below": int(from_below[ok].sum()),
            }
    out = {"n": tot, "reject_rate": rej / tot if tot else float("nan")}
    if per_level:
        out["by_level"] = by_level
    return out


def run(bars, R, M):
    true = measure(bars, R, M, 0.0, per_level=True)
    null = np.empty(NPHASE - 1)
    for j in range(1, NPHASE):
        null[j - 1] = measure(bars, R, M, j * 100.0 / NPHASE)["reject_rate"]

    z = gbr.zscore(true["reject_rate"], null)
    rank = int((null >= true["reject_rate"]).sum() + 1)
    print("\n=== reaction  R=%d  horizon=%dmin ===" % (R, M))
    print("  touches (deduped)   %d" % true["n"])
    print("  reject rate         %.4f" % true["reject_rate"])
    print("  phase-null mean     %.4f  sd %.4f" % (null.mean(), null.std(ddof=1)))
    print("  z vs phase null     %+.2f      rank %d/60" % (z, rank))
    print("  %-6s %-20s %8s  %8s" % ("level", "name", "n", "reject"))
    for pct in gbr.LEVELS:
        d = true["by_level"].get(int(pct))
        if not d:
            continue
        print("  %-6d %-20s %8d  %7.4f" % (pct, gbr.LEVEL_NAME[int(pct)], d["n"], d["reject_rate"]))
    return {
        "R": R, "M": M,
        "n": true["n"], "reject_rate": true["reject_rate"],
        "null_mean": float(null.mean()), "null_sd": float(null.std(ddof=1)),
        "z_phase": float(z), "rank": rank,
        "by_level": true["by_level"],
        "null_rates": null.tolist(),
    }


def main():
    raw = np.load(os.path.join(HERE, "bars.npz"))
    bars = {k: raw[k] for k in ("h", "l", "c")}
    for M in HORIZONS:
        fmax, fmin = fwd_extremes_fast(bars["h"], bars["l"], M)
        bars["_fmax%d" % M] = fmax
        bars["_fmin%d" % M] = fmin

    res = []
    for R in (729, 2187):
        for M in HORIZONS:
            res.append(run(bars, R, M))
    with open(os.path.join(HERE, "reaction.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print("\nwrote reaction.json")


if __name__ == "__main__":
    main()
