"""The path map: given a state at one level, where does price go next?

No stop, no target, no expectancy. Just reach probabilities -- if this breaks,
how often does price get to the next level, the one after, the one after that.
This is the question a trader actually asks first, and it is worth answering
carefully because the answer is useful for planning whether or not the lattice
turns out to be special.

Two states, both identifiable the moment the bar closes:

    BREAK    the close crosses level i in the direction of travel
    REJECT   price trades up to level i but the close stays below it, having
             come from at least a quarter of the block below

and then, over a fixed horizon, whether price touches level i+k for a range of
k -- forward for continuation targets, backward for retracement targets.

"k levels away" is a variable distance, because the Goldbach levels are not
evenly spaced: the gaps run 3, 4, 4, 6, 6, 6, 6, 6, 6, 3, 3, 6 ... That is the
claim as stated, though -- price travels to the NEXT LEVEL, not to a fixed
distance -- so the uneven spacing is part of what is being tested rather than a
nuisance.

Read the output two ways. The reach column is a base rate you can plan around
whatever its origin. The null column is the same construction on shifted
lattices, and the gap between them is the only part that belongs to Goldbach.
"""
import json
import os

import numpy as np

import gbr
import reaction as rx

HERE = os.path.dirname(os.path.abspath(__file__))
NPHASE = 12
KS = list(range(-5, 13))          # levels back through levels ahead
DEDUP = 60
BACKOFF = 0.25                    # a rejection came from 0.25R inside


def level_price(R, off, j):
    """Price of ABSOLUTE level index j: block j//20, level j%20 within it."""
    return (off + R * np.floor_divide(j, 20)
            + R * gbr.LEVELS[np.mod(j, 20)] / 100.0)


def dedup(idx, gap):
    if len(idx) == 0:
        return idx
    keep = [idx[0]]
    for i in idx[1:]:
        if i - keep[-1] >= gap:
            keep.append(i)
    return np.asarray(keep)


def states(c, h, l, R, phase, trail_lo, trail_hi):
    """Break and reject events, tagged with block and level index."""
    off = R * phase / 100.0
    pos = (c - off) / R
    blk = np.floor(pos).astype(np.int64)
    pct = (pos - blk) * 100.0
    # index of the highest level at or below the close
    li = np.searchsorted(gbr.LEVELS, pct, side="right") - 1
    prev_abs = np.empty(len(c), np.int64)
    cur_abs = blk * 20 + li
    prev_abs[0] = cur_abs[0]
    prev_abs[1:] = cur_abs[:-1]

    # every level array below is PER BAR, so each event's level is read with
    # its own final bar index. Carrying a separately-filtered copy alongside
    # and re-indexing it is how these two lists silently drift apart.
    up_lv = cur_abs + 1                       # level just above the close
    up_px = level_price(R, off, up_lv)
    dn_px = level_price(R, off, cur_abs)      # level just below the close

    out = {}
    # ---- breaks: the close moves up (or down) through at least one level ---
    for name, raw, lv_arr in (
            ("break_up", np.flatnonzero(cur_abs > prev_abs), cur_abs),
            ("break_dn", np.flatnonzero(cur_abs < prev_abs), prev_abs)):
        idx = dedup(raw[raw > 80], DEDUP)
        out[name] = (idx, lv_arr[idx])

    # ---- rejects: touched the level, closed back inside --------------------
    for name, raw, lv_arr in (
            ("reject_up", np.flatnonzero((h >= up_px) & (c < up_px) &
                                         (trail_lo <= up_px - BACKOFF * R)),
             up_lv),
            ("reject_dn", np.flatnonzero((l <= dn_px) & (c > dn_px) &
                                         (trail_hi >= dn_px + BACKOFF * R)),
             cur_abs)):
        idx = dedup(raw[raw > 80], DEDUP)
        out[name] = (idx, lv_arr[idx])
    return out, off


def reach(idx, lv, off, R, fmax, fmin, up, n):
    """P(price touches level lv+k) within the horizon, for each k."""
    ok = (idx + 1 < n)
    idx, lv = idx[ok], lv[ok]
    res = {}
    for k in KS:
        # k>0 means further in the direction of travel; for a downward move
        # that is a LOWER price, so both the target and the comparison flip.
        tgt = level_price(R, off, lv + (k if up else -k))
        if up:
            hit = fmax[idx] >= tgt if k > 0 else fmin[idx] <= tgt
        else:
            hit = fmin[idx] <= tgt if k > 0 else fmax[idx] >= tgt
        res[k] = float(np.mean(hit))
    return res, len(idx)


def run(c, h, l, R, H, phase, trail):
    n = len(c)
    fmax, fmin = rx.fwd_extremes_fast(h, l, H)
    st, off = states(c, h, l, R, phase, trail[0], trail[1])
    out = {}
    for name, (idx, lv) in st.items():
        up = name.endswith("_up")
        # a rejection at a level above reverses DOWN, so travel is downward
        travel_up = up if name.startswith("break") else not up
        r, cnt = reach(idx, lv, off, R, fmax, fmin, travel_up, n)
        if cnt >= 300:
            out[name] = {"n": cnt, "reach": r}
    return out


def trail_closes(c, lookback):
    lo, hi = c.copy(), c.copy()
    for o in range(1, lookback):
        lo[o:] = np.minimum(lo[o:], c[:-o])
        hi[o:] = np.maximum(hi[o:], c[:-o])
    return (np.concatenate([[c[0]], lo[:-1]]),
            np.concatenate([[c[0]], hi[:-1]]))


LABEL = {"break_up": "break upward", "break_dn": "break downward",
         "reject_up": "reject at level above", "reject_dn": "reject at level below"}


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    c, h, l = (np.asarray(npz[k]) for k in ("c", "h", "l"))
    trail = trail_closes(c, 60)

    out = {}
    for R, H in ((81.0, 480), (243.0, 1440), (729.0, 2880)):
        print("\n" + "=" * 74)
        print("R=%d   horizon %d bars (%.1f hours)" % (R, H, H / 60.0))
        print("=" * 74)
        true = run(c, h, l, R, H, 0.0, trail)
        nulls = [run(c, h, l, R, H, j * 100.0 / NPHASE, trail)
                 for j in range(1, NPHASE)]
        out[str(int(R))] = {}
        for name in ("break_up", "break_dn", "reject_up", "reject_dn"):
            if name not in true:
                continue
            print("\n  %s  (%s events)"
                  % (LABEL[name], "{:,}".format(true[name]["n"])))
            print("     %-16s %9s %9s %8s" % ("target", "reaches", "shifted", "edge"))
            rows = {}
            for k in KS:
                if k == 0:
                    continue
                p = true[name]["reach"][k]
                arr = np.array([m[name]["reach"][k] for m in nulls
                                if name in m])
                nm = float(arr.mean())
                sd = float(arr.std(ddof=1))
                tag = ("%+d levels on" % k) if k > 0 else ("%+d levels back" % k)
                rows[k] = {"p": p, "null": nm, "sd": sd,
                           "z": (p - nm) / sd if sd > 0 else 0.0}
                print("     %-16s %9.4f %9.4f %+7.2fpp"
                      % (tag, p, nm, (p - nm) * 100))
            out[str(int(R))][name] = {"n": true[name]["n"], "rows":
                                      {str(k): v for k, v in rows.items()}}

    json.dump(out, open(os.path.join(HERE, "paths.json"), "w"), indent=1)
    print("\nwrote paths.json")


if __name__ == "__main__":
    main()
