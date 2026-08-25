"""PO3 blocks as DEALING RANGES: breach one and price navigates to the next;
reject at one and price goes back into the range.

This is a claim about DESTINATION, which nothing else in this repo tests. Every
other test asks whether price stops at a line. This asks where price goes once
the line has been settled one way or the other.

Both halves of the claim reduce to the same race, which is what makes it clean.
Take the boundary B being contested. There are exactly two natural
destinations:

    B + R   the far side of the block above
    B - R   the far side of the block below

They are symmetric about B, so a driftless walk starting at B is a coin flip.
No ATR scaling is needed -- R is the natural unit of the claim -- and the
symmetry means there is no bracket to tune and no win-rate dial to hide behind.

    BREACH UP      price closes through B into the block above.
                   Claim: reaches B+R before B-R.
    BREACH DOWN    mirror. Claim: reaches B-R first.
    REJECT AT B    price trades up to B but closes back below it.
                   Claim: goes back into its own range, B-R, first.
    REJECT AT B    (from above) mirror. Claim: B+R first.

A random walk does NOT give 0.500 for these, because a breach leaves price just
above B and a rejection leaves it just below, so each starts marginally nearer
its own claimed destination. That bias is exactly why the shifted-lattice null
matters: shifted lattices generate the same event geometry with the same small
head start, so the comparison isolates the lattice.

The decisive number is the SPREAD between breach and reject at the same
boundary. If breaches genuinely continue and rejections genuinely revert, that
spread should be large and should not survive a lattice shift.

Everything runs on the compressed sequence of block-index changes, so a race to
a block boundary is a walk along that sequence rather than a scan over four
million bars.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NPHASE = 20
MAXSTEP = 400          # compressed block transitions to follow
MAXBARS = 14400        # ... and no more than ten sessions of real time
DEDUP = 240
BACKOFF = 0.25         # a rejection must have come from 0.25R inside the range
LOOKBACK = 60


def dedup(idx, gap):
    if len(idx) == 0:
        return idx
    keep = [idx[0]]
    for i in idx[1:]:
        if i - keep[-1] >= gap:
            keep.append(i)
    return np.asarray(keep)


def race(pos, bi, ks, ts):
    """+1 if price reaches B+R first, -1 if B-R first, 0 unresolved.

    B is the boundary with index bi, so B+R is block index bi+1 or higher and
    B-R is block index bi-2 or lower.
    """
    m = len(pos)
    out = np.zeros(m, np.int8)
    live = np.ones(m, bool)
    t0 = ts[pos]
    for w in range(1, MAXSTEP + 1):
        p = np.minimum(pos + w, len(ks) - 1)
        late = (ts[p] - t0) > MAXBARS
        v = ks[p]
        up = live & ~late & (v >= bi + 1)
        dn = live & ~late & (v <= bi - 2)
        out[up] = 1
        out[dn] = -1
        live &= ~(up | dn | late)
        if not live.any():
            break
    return out


def trail_closes(c, lookback):
    """Trailing min and max of the close, excluding the current bar.

    Hoisted out of the event builder because it does not depend on the lattice
    phase -- recomputing it inside cost 540 passes over four million bars on
    every one of twenty phases, which is what made the scaled run time out.
    """
    lo, hi = c.copy(), c.copy()
    for o in range(1, lookback):
        lo[o:] = np.minimum(lo[o:], c[:-o])
        hi[o:] = np.maximum(hi[o:], c[:-o])
    return (np.concatenate([[c[0]], lo[:-1]]),
            np.concatenate([[c[0]], hi[:-1]]))


def events(c, h, l, R, phase, trail=None):
    """Breaches and rejections at every block boundary, with the race set up."""
    off = R * phase / 100.0
    k = np.floor((c - off) / R).astype(np.int64)
    chg = np.flatnonzero(np.diff(k)) + 1
    if len(chg) < 50:
        return None
    ks = np.concatenate([[k[0]], k[chg]])          # compressed level sequence
    ts = np.concatenate([[0], chg])                # bar index of each change
    prev = ks[:-1]
    new = ks[1:]
    step = new - prev

    out = {}

    # ---- breaches: a clean one-block move of the close --------------------
    for name, sel, bi in (("breach_up", step == 1, new),
                          ("breach_dn", step == -1, prev)):
        p = np.flatnonzero(sel) + 1                # compressed position
        if len(p) == 0:
            continue
        keep = dedup(ts[p], DEDUP)
        p = p[np.searchsorted(ts[p], keep)]
        b = bi[p - 1] if name == "breach_up" else bi[p - 1]
        out[name] = (p, b)

    # ---- rejections: touched the boundary, closed back inside -------------
    lo_c, hi_c = trail if trail is not None else trail_closes(c, LOOKBACK)

    b_up = off + R * (k + 1)                        # boundary above the close
    b_dn = off + R * k                              # boundary below the close

    rj_up = np.flatnonzero((h >= b_up) & (c < b_up) &
                           (lo_c <= b_up - BACKOFF * R))
    rj_dn = np.flatnonzero((l <= b_dn) & (c > b_dn) &
                           (hi_c >= b_dn + BACKOFF * R))
    for name, ridx, bidx in (("reject_at_top", rj_up, k + 1),
                             ("reject_at_bottom", rj_dn, k)):
        ridx = ridx[(ridx > LOOKBACK) & (ridx < len(c) - 10)]
        ridx = dedup(ridx, DEDUP)
        if len(ridx) == 0:
            continue
        p = np.searchsorted(ts, ridx, side="right") - 1
        ok = p >= 0
        out[name] = (p[ok], bidx[ridx][ok])

    return out, ks, ts


def measure(c, h, l, R, phase, trail=None):
    got = events(c, h, l, R, phase, trail)
    if got is None:
        return None
    ev, ks, ts = got
    res = {}
    for name, (p, bi) in ev.items():
        r = race(p, bi, ks, ts)
        dec = r != 0
        if dec.sum() < 200:
            continue
        res[name] = {"n": int(dec.sum()),
                     "p_up": float((r[dec] == 1).mean()),
                     "resolved": float(dec.mean())}
    return res


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    c, h, l = (np.asarray(npz[k]) for k in ("c", "h", "l"))

    # what the framework predicts for P(reach B+R first) in each case
    CLAIM = {"breach_up": "high", "breach_dn": "low",
             "reject_at_top": "low", "reject_at_bottom": "high"}

    out = {}
    for R in (81.0, 243.0, 729.0, 2187.0):
        print("\n=== R=%d ===" % R)
        tr = trail_closes(c, LOOKBACK)
        true = measure(c, h, l, R, 0.0, tr)
        nulls = [measure(c, h, l, R, j * 100.0 / NPHASE, tr)
                 for j in range(1, NPHASE)]
        print("  %-18s %9s %9s %10s %10s %8s  %s"
              % ("event", "n", "resolved", "P(up first)", "shifted", "z", "claim"))
        row = {}
        for name in ("breach_up", "breach_dn", "reject_at_top", "reject_at_bottom"):
            if name not in true:
                continue
            arr = np.array([m[name]["p_up"] for m in nulls if m and name in m])
            sd = arr.std(ddof=1)
            z = (true[name]["p_up"] - arr.mean()) / sd if sd > 0 else 0.0
            row[name] = {"n": true[name]["n"], "p_up": true[name]["p_up"],
                         "resolved": true[name]["resolved"],
                         "null": float(arr.mean()), "sd": float(sd), "z": float(z)}
            print("  %-18s %9s %8.3f %10.4f %10.4f %+8.2f  %s"
                  % (name, "{:,}".format(true[name]["n"]),
                     true[name]["resolved"], true[name]["p_up"], arr.mean(), z,
                     CLAIM[name]))

        # the decisive contrast: breach against rejection at the same boundary
        for a, b, lab in (("breach_up", "reject_at_top", "up-side boundary"),
                          ("reject_at_bottom", "breach_dn", "down-side boundary")):
            if a in row and b in row:
                d = row[a]["p_up"] - row[b]["p_up"]
                dn = np.array([m[a]["p_up"] - m[b]["p_up"] for m in nulls
                               if m and a in m and b in m])
                sd = dn.std(ddof=1)
                print("     spread %-22s true %+.4f   shifted %+.4f   z = %+.2f"
                      % (lab, d, dn.mean(), (d - dn.mean()) / sd if sd > 0 else 0.0))
                row["spread_" + lab.split()[0]] = {
                    "true": float(d), "null": float(dn.mean()),
                    "z": float((d - dn.mean()) / sd) if sd > 0 else 0.0}
        out[str(int(R))] = row

    json.dump(out, open(os.path.join(HERE, "dealing.json"), "w"), indent=1)
    print("\nwrote dealing.json")


if __name__ == "__main__":
    main()
