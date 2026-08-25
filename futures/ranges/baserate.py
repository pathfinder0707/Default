"""Base rates: the two plainest questions you can ask about a level.

  A. TOUCH.  Price arrives at the level from at least 1 ATR away. Does it
     reject (turn and give back 0.5 ATR the way it came) or break (push 0.5 ATR
     through)? This is "is it support or resistance", with nothing else
     attached, and it is the number a trader is really claiming when they say
     the levels work.

  B. BREAK.  Price closes through the level and runs 1 ATR past it. Does it
     come back to touch the level again, and how fast? This is the base rate
     you need before you plan any retest entry at all -- an entry you only get
     filled on some fraction of the time.

Both are scored against 6 shifted lattices running the identical procedure, and
against a control set of ROUND-NUMBER lines (multiples of 25 points), which is
the one grid that has previously shown a real effect in this repo and so acts
as a positive control on the measurement rather than on the lattice.

Anti-straddle rule, the same one that invalidated the first version of edge.py:
the "came from 1 ATR away" condition must be satisfied on a bar strictly BEFORE
the touch bar, otherwise a single wide bar satisfies the setup and its outcome
by itself.
"""
import json
import os

import numpy as np

import gbr
from edge import atr, dedup

HERE = os.path.dirname(os.path.abspath(__file__))
NPHASE = 7
AWAY = 1.0            # ATR the approach must come from
DECIDE = 0.5          # ATR that settles reject vs break
HORIZON = 120
RETEST_WINDOWS = (60, 120, 240)
DEDUP = 120


def approaches(h, l, c, a, cmin, cmax, o, R, n):
    """Every qualifying arrival at a line of the family {o + kR}.

    An upward approach is a bar that reaches the first line above the PREVIOUS
    close, having spent the last 60 bars coming from at least AWAY x ATR below
    it. Both conditions use only bars before the touch, and the line is fixed
    before the bar opens, so a resting order at it is legitimate.
    """
    prev = np.empty_like(c); prev[0] = c[0]; prev[1:] = c[:-1]
    pa = np.empty_like(a); pa[0] = a[0]; pa[1:] = a[:-1]
    k = np.floor((prev - o) / R)
    lup = o + R * (k + 1)
    ldn = o + R * k
    out = []
    for L, up in ((lup, True), (ldn, False)):
        tch = (h >= L) if up else (l <= L)
        far = (cmin <= L - AWAY * pa) if up else (cmax >= L + AWAY * pa)
        idx = np.flatnonzero(tch & far)
        idx = idx[(idx > 80) & (idx + HORIZON < n)]
        if len(idx) == 0:
            continue
        idx = dedup(idx, DEDUP)
        out.append((idx, L[idx], up))
    return out


def resolve_touch(h, l, idx, L, at, up, n):
    """+1 reject, -1 break. Decided AT the line, not at the bar's close.

    The trade being scored is the fade: sell the line on an upward approach. So
    'break' is continuation through the line and 'reject' is the turn. The touch
    bar can only count AGAINST the fade -- its excursion past the line is real
    heat taken after the fill, while the part of its range on the near side
    happened on the way in, before the fill.
    """
    brk = L + DECIDE * at if up else L - DECIDE * at
    rej = L - DECIDE * at if up else L + DECIDE * at
    out = np.zeros(len(idx), np.int8)
    over = (h[idx] - L) if up else (L - l[idx])
    out[over >= DECIDE * at] = -1                  # broken on the touch bar
    live = out == 0
    for w in range(1, HORIZON + 1):
        j = np.clip(idx + w, 0, n - 1)
        hb = (h[j] >= brk) if up else (l[j] <= brk)
        hr = (l[j] <= rej) if up else (h[j] >= rej)
        b_now = live & hb                          # both in one bar -> break
        r_now = live & hr & ~hb
        out[b_now] = -1
        out[r_now] = 1
        live &= ~(b_now | r_now)
        if not live.any():
            break
    return out


def touch_rate(h, l, c, a, cmin, cmax, R, phase, n):
    off = R * phase / 100.0
    rej = brk = 0
    for pct in gbr.LEVELS:
        o = off + R * pct / 100.0
        for idx, L, up in approaches(h, l, c, a, cmin, cmax, o, R, n):
            res = resolve_touch(h, l, idx, L, a[idx], up, n)
            rej += int((res == 1).sum())
            brk += int((res == -1).sum())
    tot = rej + brk
    return (rej / tot if tot else np.nan), tot


def break_retest_rate(h, l, c, a, R, phase, n):
    """P(a 1-ATR break gets retested) within each window."""
    off = R * phase / 100.0
    got = np.zeros(len(RETEST_WINDOWS))
    tot = 0
    for pct in gbr.LEVELS:
        o = off + R * (pct / 100.0)
        k = np.floor((c - o) / R)
        d = np.diff(k)
        for up in (True, False):
            cr = np.flatnonzero(d > 0) + 1 if up else np.flatnonzero(d < 0) + 1
            cr = cr[(cr > 20) & (cr + max(RETEST_WINDOWS) < n)]
            cr = dedup(cr, DEDUP)
            if len(cr) == 0:
                continue
            L = o + R * (k[cr] if up else k[cr] + 1)
            at = a[cr]
            thr = L + AWAY * at if up else L - AWAY * at
            gone = np.zeros(len(cr), bool)
            back_at = np.full(len(cr), 10 ** 9, np.int64)
            for w in range(1, max(RETEST_WINDOWS) + 1):
                j = np.clip(cr + w, 0, n - 1)
                bk = (l[j] <= L) if up else (h[j] >= L)
                hit = gone & bk & (back_at == 10 ** 9)
                back_at[hit] = w
                still = back_at == 10 ** 9
                gone |= still & ((h[j] >= thr) if up else (l[j] <= thr))
            # only breaks that actually achieved the excursion are in the base
            base = gone | (back_at < 10 ** 9)
            tot += int(base.sum())
            for q, wdw in enumerate(RETEST_WINDOWS):
                got[q] += int((back_at[base] <= wdw).sum())
    return (got / tot if tot else got * np.nan), tot


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    h, l, c = (np.asarray(npz[k]) for k in ("h", "l", "c"))
    a = atr(h, l, c)
    n = len(c)
    # trailing 60-bar close extremes, excluding the current bar
    cmin, cmax = c.copy(), c.copy()
    for off in range(1, 60):
        cmin[off:] = np.minimum(cmin[off:], c[:-off])
        cmax[off:] = np.maximum(cmax[off:], c[:-off])
    cmin = np.concatenate([[c[0]], cmin[:-1]])
    cmax = np.concatenate([[c[0]], cmax[:-1]])
    res = {"touch": [], "retest": []}

    print("=== A. touch: does the level reject or break? ===")
    print("   reject = gives back %.1f ATR the way it came before pushing"
          " %.1f ATR through\n" % (DECIDE, DECIDE))
    print("  %-6s %10s %9s %9s %8s %8s"
          % ("R", "touches", "P(reject)", "null", "edge", "z"))
    for R in (81.0, 243.0, 729.0):
        t, cnt = touch_rate(h, l, c, a, cmin, cmax, R, 0.0, n)
        nl = np.array([touch_rate(h, l, c, a, cmin, cmax, R, j * 100.0 / NPHASE, n)[0]
                       for j in range(1, NPHASE)])
        sd = nl.std(ddof=1)
        z = (t - nl.mean()) / sd if sd > 0 else 0.0
        res["touch"].append({"R": R, "n": cnt, "p": float(t),
                             "null": float(nl.mean()), "z": float(z)})
        print("  %-6d %10s %9.4f %9.4f %+7.2fpp %+8.2f"
              % (R, "{:,}".format(cnt), t, nl.mean(), (t - nl.mean()) * 100, z))

    print("\n=== B. break: does it come back for a retest? ===")
    print("  %-6s %10s %10s %10s %10s"
          % ("R", "breaks", "<=60 bars", "<=120", "<=240"))
    for R in (81.0, 243.0, 729.0):
        r, cnt = break_retest_rate(h, l, c, a, R, 0.0, n)
        res["retest"].append({"R": R, "n": cnt,
                              "rates": {str(w): float(x)
                                        for w, x in zip(RETEST_WINDOWS, r)}})
        print("  %-6d %10s %10.4f %10.4f %10.4f"
              % (R, "{:,}".format(cnt), r[0], r[1], r[2]))

    with open(os.path.join(HERE, "baserate.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print("\nwrote baserate.json")


if __name__ == "__main__":
    main()
