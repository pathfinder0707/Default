"""The full fixed-clock cube: pick a level, a hold, a side -- get the stats.

partition.py answered the question for the block high and low only, at one
hold, and the report showed a single static slice of it. This computes the
whole cube so the reader can choose:

    block      R = 81, 243, 729
    level      any Goldbach level, or one of the named groups
    arrival    reached from below (a resistance test) or from above (support)
    hold       15, 30, 45 or 60 minutes
    side       fade the arrival, or follow it

Entry is filled at the level itself. Exit is the close N minutes later,
unconditionally -- no stop, no target, nothing to tune. Every cell carries the
full descriptive set: hit rate, mean, median, net of a round turn, best and
worst single trade, the average excursion each way before the clock ran out,
profit factor, a day-clustered interval, and the same statistic on shifted
lattices.

FADE and FOLLOW are exact mirrors trade by trade, so only the fade side is
stored and the follow side is derived in the page: mean and median negate,
best and worst swap, and the two excursions swap. Only the hit rate needs care,
because a trade that finishes exactly flat is neither -- so the loss rate is
stored alongside the win rate rather than assumed to be its complement.
"""
import json
import os

import numpy as np

import gbr
from edge import atr, COST_PTS

HERE = os.path.dirname(os.path.abspath(__file__))
HOLDS = [15, 30, 45, 60]
NPHASE = 8
AWAY = 1.0
LOOKBACK = 60
DEDUP = 60

GROUPS = {
    "any":      list(gbr.LEVELS),
    "boundary": [0.0],
    "eq":       [50.0],
    "ext":      [97.0, 3.0],
    "fv":       [29.0, 71.0],
    "gip":      [17.0, 83.0],
    "llod":     [7.0, 93.0],
}


def dedup(idx, gap):
    if len(idx) == 0:
        return idx
    keep = [idx[0]]
    for i in idx[1:]:
        if i - keep[-1] >= gap:
            keep.append(i)
    return np.asarray(keep)


def touches(h, l, c, a, cmin, cmax, R, phase, n):
    """Every qualifying arrival at every Goldbach level, tagged by level and side.

    `below` is True when price came up to the level, so the level is being
    tested as resistance; False when it came down onto it.
    """
    off = R * phase / 100.0
    prev = np.empty(n); prev[0] = c[0]; prev[1:] = c[:-1]
    pa = np.empty(n); pa[0] = a[0]; pa[1:] = a[:-1]
    I, L, B, P = [], [], [], []
    for pct in gbr.LEVELS:
        o = off + R * pct / 100.0
        k = np.floor((prev - o) / R)
        up_lv = o + R * (k + 1)          # nearest such level above the close
        dn_lv = o + R * k                # ... and below
        m_up = (h >= up_lv) & (cmin <= up_lv - AWAY * pa)
        m_dn = (l <= dn_lv) & (cmax >= dn_lv + AWAY * pa)
        for m, lv, below in ((m_up, up_lv, True), (m_dn, dn_lv, False)):
            idx = np.flatnonzero(m)
            idx = idx[(idx > LOOKBACK) & (idx + max(HOLDS) < n)]
            idx = dedup(idx, DEDUP)
            if len(idx) == 0:
                continue
            I.append(idx); L.append(lv[idx])
            B.append(np.full(len(idx), below))
            P.append(np.full(len(idx), pct))
    if not I:
        return None
    return (np.concatenate(I), np.concatenate(L),
            np.concatenate(B), np.concatenate(P))


def excursions(h, l, idx, entry, sgn, hold, n):
    """P&L at the bell, plus how far it went each way before then."""
    m = len(idx)
    hi = np.full(m, -np.inf); lo = np.full(m, np.inf)
    for w in range(1, hold + 1):
        j = np.clip(idx + w, 0, n - 1)
        hi = np.maximum(hi, h[j]); lo = np.minimum(lo, l[j])
    if sgn > 0:
        mfe, mae = hi - entry, entry - lo
    else:
        mfe, mae = entry - lo, hi - entry
    return np.maximum(mfe, 0.0), np.maximum(mae, 0.0)


def cell(pnl, mfe, mae, day, nd, pick):
    net = pnl - COST_PTS
    s = np.bincount(day, weights=net, minlength=nd)
    cnt = np.bincount(day, minlength=nd).astype(float)
    bs = s[pick].sum(1) / np.maximum(cnt[pick].sum(1), 1)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    g = net[net > 0].sum(); b = -net[net < 0].sum()
    gf = (-net)[(-net) > 0].sum(); bf = -(-net)[(-net) < 0].sum()
    return {
        "n": int(len(pnl)),
        "win": round(float((pnl > 0).mean()), 4),
        "loss": round(float((pnl < 0).mean()), 4),
        "mean": round(float(pnl.mean()), 3),
        "med": round(float(np.median(pnl)), 3),
        "best": round(float(pnl.max()), 1),
        "worst": round(float(pnl.min()), 1),
        "mfe": round(float(mfe.mean()), 2),
        "mae": round(float(mae.mean()), 2),
        "pf": round(float(g / b), 3) if b > 0 else None,
        "pf_follow": round(float(gf / bf), 3) if bf > 0 else None,
        "lo": round(float(lo), 3), "hi": round(float(hi), 3),
    }


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    h, l, c = (np.asarray(npz[k]) for k in ("h", "l", "c"))
    date = np.asarray(npz["date"])
    a = atr(h, l, c)
    n = len(c)
    cmin, cmax = c.copy(), c.copy()
    for o in range(1, LOOKBACK):
        cmin[o:] = np.minimum(cmin[o:], c[:-o])
        cmax[o:] = np.maximum(cmax[o:], c[:-o])
    cmin = np.concatenate([[c[0]], cmin[:-1]])
    cmax = np.concatenate([[c[0]], cmax[:-1]])

    rng = np.random.default_rng(41)
    out = {}
    for R in (81.0, 243.0, 729.0):
        got = touches(h, l, c, a, cmin, cmax, R, 0.0, n)
        I, L, B, P = got
        print("R=%-5d %s qualifying arrivals" % (R, "{:,}".format(len(I))))

        # shifted lattices: mean P&L only, which is all the null needs
        nullp = {}
        for j in range(1, NPHASE):
            g2 = touches(h, l, c, a, cmin, cmax, R, j * 100.0 / NPHASE, n)
            if g2 is None:
                continue
            I2, L2, B2, P2 = g2
            for gname, pcts in GROUPS.items():
                gm = np.isin(P2, pcts)
                for side, bm in (("below", B2), ("above", ~B2)):
                    m = gm & bm
                    if m.sum() < 200:
                        continue
                    for hold in HOLDS:
                        ex = c[np.minimum(I2[m] + hold, n - 1)]
                        # fade: short a level reached from below, long from above
                        sgn = -1 if side == "below" else 1
                        p = sgn * (ex - L2[m])
                        nullp.setdefault((gname, side, hold), []).append(float(p.mean()))

        out[str(int(R))] = {}
        for gname, pcts in GROUPS.items():
            gm = np.isin(P, pcts)
            out[str(int(R))][gname] = {}
            for side, bm in (("below", B), ("above", ~B)):
                m = gm & bm
                if m.sum() < 200:
                    continue
                idx, lv = I[m], L[m]
                u, day = np.unique(date[idx], return_inverse=True)
                nd = len(u)
                pick = rng.integers(0, nd, size=(1200, nd))
                sgn = -1 if side == "below" else 1     # fade direction
                cells = {}
                for hold in HOLDS:
                    ex = c[np.minimum(idx + hold, n - 1)]
                    pnl = sgn * (ex - lv)
                    mfe, mae = excursions(h, l, idx, lv, sgn, hold, n)
                    st = cell(pnl, mfe, mae, day, nd, pick)
                    nv = nullp.get((gname, side, hold))
                    st["null"] = round(float(np.mean(nv)), 3) if nv else None
                    st["days"] = int(nd)
                    cells[str(hold)] = st
                out[str(int(R))][gname][side] = cells
        done = sum(len(v) for v in out[str(int(R))].values())
        print("   %d level-group x side combinations" % done)

    json.dump(out, open(os.path.join(HERE, "clock.json"), "w"),
              separators=(",", ":"))
    sz = os.path.getsize(os.path.join(HERE, "clock.json")) / 1024
    print("\nwrote clock.json (%.0f KB)" % sz)

    # a readable sanity slice
    print("\nsample: R=243, boundary, reached from below, fade")
    for hold in HOLDS:
        s = out["243"]["boundary"]["below"][str(hold)]
        print("  %2dm  n=%5d  win %.3f  mean %+.2f  med %+.2f  MFE %.1f  MAE %.1f  null %+.2f"
              % (hold, s["n"], s["win"], s["mean"], s["med"], s["mfe"],
                 s["mae"], s["null"]))


if __name__ == "__main__":
    main()
