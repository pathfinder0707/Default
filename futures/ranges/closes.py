"""Does the HIGHER-TIMEFRAME CLOSE at the boundary decide which way price goes?

The rule as stated: price reaches the high (or low) of the block, and you wait
for the 3, 5, 15 or 30 minute candle to close.

    CLOSED BACK INSIDE   price goes back into the range -- to the EQ, or on to
                         the opposite boundary
    CLOSED THROUGH       price expands into the next block -- to the next EQ,
                         or on to the next boundary

This is the first rule tested here that uses a higher-timeframe close as the
decision, and it is well posed because the two destinations are SYMMETRIC about
the boundary B:

    back into range      B - R/2  (the EQ behind)      and  B - R  (the far side)
    expansion            B + R/2  (the EQ ahead)       and  B + R  (the next one)

Equal distances either way, so there is no bracket to tune and a coin flip is
close to the right intuition. The decision is known the instant the HTF candle
closes and the race starts on the NEXT one-minute bar, so nothing is scored
from information that was not on the screen.

The decisive number is not either rate on its own -- it is the SPREAD between
them. If a close back inside genuinely predicts a return and a close through
genuinely predicts expansion, the two conditions must separate, and that
separation must survive moving the lattice.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TFS = [3, 5, 15, 30]
NPHASE = 12
HORIZON = 1440           # one full day of one-minute bars to resolve the race
AWAY = 1.0               # the approach must come from this many ATR away
LOOKBACK = 60


def atr(h, l, c, n=14):
    pc = np.empty_like(c); pc[0] = c[0]; pc[1:] = c[:-1]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    out = np.empty_like(tr); a = tr[:n].mean(); out[:n] = a
    for i in range(n, len(tr)):
        a = (a * (n - 1) + tr[i]) / n
        out[i] = a
    return out


def htf(h, l, c, date, hh, mm, tf):
    """Aggregate one-minute bars into TF-minute candles.

    Returns each candle's high, low, close and the index of its LAST one-minute
    bar, which is where the decision becomes known and the race begins.
    """
    key = date.astype(np.int64) * 10000 + (hh * 60 + mm) // tf
    u, first = np.unique(key, return_index=True)
    order = np.argsort(first)
    first = first[order]
    last = np.append(first[1:], len(c)) - 1
    hi = np.maximum.reduceat(h, first)
    lo = np.minimum.reduceat(l, first)
    return hi, lo, c[last], last


def race(h, l, start, lo_tgt, hi_tgt, n):
    """+1 if the LOWER target is reached first, -1 if the upper, 0 unresolved."""
    out = np.zeros(len(start), np.int8)
    live = np.ones(len(start), bool)
    for w in range(1, HORIZON + 1):
        j = np.clip(start + w, 0, n - 1)
        dn = live & (l[j] <= lo_tgt)
        up = live & (h[j] >= hi_tgt)
        both = dn & up
        out[dn & ~both] = 1
        out[up & ~both] = -1
        live &= ~(dn | up)
        if not live.any():
            break
    return out


def measure(h, l, c, a, cmin, cmax, date, hh, mm, R, phase, tf, n):
    """Boundary tests on TF candles, split by where the candle closed."""
    off = R * phase / 100.0
    HI, LO, CL, LAST = htf(h, l, c, date, hh, mm, tf)
    m = len(CL)
    if m < 200:
        return None
    prev = np.empty(m); prev[0] = CL[0]; prev[1:] = CL[:-1]
    k = np.floor((prev - off) / R)
    b_up = off + R * (k + 1)
    b_dn = off + R * k
    # the approach must have come from at least AWAY x ATR inside the block
    at = a[LAST]
    pa = np.empty(m); pa[0] = at[0]; pa[1:] = at[:-1]

    res = {}
    for name, touched, B, inside_is_below in (
            ("high", HI >= b_up, b_up, True),
            ("low", LO <= b_dn, b_dn, False)):
        far = (cmin[LAST] <= B - AWAY * pa) if inside_is_below \
            else (cmax[LAST] >= B + AWAY * pa)
        sel = np.flatnonzero(touched & far & (LAST + 2 < n) & (np.arange(m) > 2))
        if len(sel) < 200:
            continue
        Bs = B[sel]
        start = LAST[sel]
        # did it close back inside, or through?
        closed_in = (CL[sel] < Bs) if inside_is_below else (CL[sel] > Bs)
        for tgt, half in (("eq", 0.5), ("boundary", 1.0)):
            r = race(h, l, start, Bs - half * R, Bs + half * R, n)
            dec = r != 0
            # "back into range" is DOWN at a high test, UP at a low test
            back = (r == 1) if inside_is_below else (r == -1)
            for lab, cond in (("closed_inside", closed_in),
                              ("closed_through", ~closed_in)):
                mm_ = dec & cond
                if mm_.sum() < 100:
                    continue
                res["%s|%s|%s" % (name, tgt, lab)] = {
                    "n": int(mm_.sum()),
                    "p_back": float(back[mm_].mean()),
                    "resolved": float(dec[cond].mean()),
                }
    return res


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    h, l, c = (np.asarray(npz[k]) for k in ("h", "l", "c"))
    date = np.asarray(npz["date"])
    hh, mm = np.asarray(npz["hh"]), np.asarray(npz["mm"])
    a = atr(h, l, c)
    n = len(c)
    cmin, cmax = c.copy(), c.copy()
    for o in range(1, LOOKBACK):
        cmin[o:] = np.minimum(cmin[o:], c[:-o])
        cmax[o:] = np.maximum(cmax[o:], c[:-o])
    cmin = np.concatenate([[c[0]], cmin[:-1]])
    cmax = np.concatenate([[c[0]], cmax[:-1]])

    out = {}
    for R in (243.0, 729.0):
        print("\n" + "=" * 92)
        print("R=%d   targets are the EQ and the far boundary, symmetric about the line"
              % R)
        print("=" * 92)
        out[str(int(R))] = {}
        for tf in TFS:
            true = measure(h, l, c, a, cmin, cmax, date, hh, mm, R, 0.0, tf, n)
            if not true:
                continue
            nulls = [measure(h, l, c, a, cmin, cmax, date, hh, mm, R,
                             j * 100.0 / NPHASE, tf, n) for j in range(1, NPHASE)]
            print("\n  %d-minute candles" % tf)
            print("    %-8s %-9s %-16s %8s %8s %10s %9s %8s"
                  % ("test", "target", "close", "n", "resolved",
                     "P(back in)", "shifted", "z"))
            for key in sorted(true):
                side, tgt, lab = key.split("|")
                t = true[key]
                arr = np.array([x[key]["p_back"] for x in nulls
                                if x and key in x])
                if len(arr) < 3:
                    continue
                sd = arr.std(ddof=1)
                z = (t["p_back"] - arr.mean()) / sd if sd > 0 else 0.0
                out[str(int(R))]["%d|%s" % (tf, key)] = {
                    "n": t["n"], "p_back": t["p_back"], "null": float(arr.mean()),
                    "z": float(z), "resolved": t["resolved"]}
                print("    %-8s %-9s %-16s %8s %8.3f %10.4f %9.4f %+8.2f"
                      % (side, tgt, lab.replace("closed_", ""),
                         "{:,}".format(t["n"]), t["resolved"], t["p_back"],
                         arr.mean(), z))
            # the decisive contrast
            for side in ("high", "low"):
                for tgt in ("eq", "boundary"):
                    ki = "%s|%s|closed_inside" % (side, tgt)
                    kt = "%s|%s|closed_through" % (side, tgt)
                    if ki in true and kt in true:
                        d = true[ki]["p_back"] - true[kt]["p_back"]
                        dn = np.array([x[ki]["p_back"] - x[kt]["p_back"]
                                       for x in nulls if x and ki in x and kt in x])
                        sd = dn.std(ddof=1)
                        print("      SPREAD %-4s %-9s inside minus through: "
                              "%+.4f   shifted %+.4f   z=%+.2f"
                              % (side, tgt, d, dn.mean(),
                                 (d - dn.mean()) / sd if sd > 0 else 0.0))
                        out[str(int(R))]["%d|spread|%s|%s" % (tf, side, tgt)] = {
                            "true": float(d), "null": float(dn.mean()),
                            "z": float((d - dn.mean()) / sd) if sd > 0 else 0.0}

    json.dump(out, open(os.path.join(HERE, "closes.json"), "w"), indent=1)
    print("\nwrote closes.json")


if __name__ == "__main__":
    main()
