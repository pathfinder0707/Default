"""Reach the block high or low, trade it, hold for a fixed time. No stop, no target.

This is the cleanest formulation anyone has proposed in this study, and it is
worth saying why: with a fixed-time exit there is no bracket to tune, no
win-rate dial, and no entry-bar convention on the exit side. The result cannot
be manufactured by choosing where to put a stop, because there is no stop. What
comes out is the raw drift of price after it arrives at a partition.

  EVENT     price reaches the high partition of its block (the boundary above)
            or the low partition (the boundary below), having come from at
            least 1 ATR away so this is an arrival rather than chop on the line
  ENTRY     filled at the partition itself, with a resting limit
  TRADE     FADE  = against the arrival (short the high, long the low)
            FOLLOW = with it (long the high, short the low)
  EXIT      the close 15, 30, 45 or 60 minutes later, unconditionally

Reported per cell: hit rate, mean and median result, expectancy net of a round
turn, the best and worst single trade, and the excursions -- how far the trade
went your way and against you before the clock ran out, which is what tells you
what a stop would have cost.

FADE and FOLLOW are mirrors: gross they sum to zero, and after costs both lose
that much. Both are shown because seeing them side by side is the point.

Everything is scored against shifted lattices too, since NQ rose eighteen-fold
across the sample and any fixed-direction hold inherits that drift -- the null
carries the identical drift and differences it out.
"""
import json
import os

import numpy as np

import gbr
from edge import atr, COST_PTS

HERE = os.path.dirname(os.path.abspath(__file__))
HOLDS = [15, 30, 45, 60]
NPHASE = 12
AWAY = 1.0            # the arrival must come from this many ATR away
LOOKBACK = 60
DEDUP = 60


def dedup(idx, gap):
    if len(idx) == 0:
        return idx
    keep = [idx[0]]
    for i in idx[1:]:
        if i - keep[-1] >= gap:
            keep.append(i)
    return np.asarray(keep)


def arrivals(h, l, c, a, cmin, cmax, R, phase, n):
    """Touches of the block high and the block low, as separate event sets."""
    off = R * phase / 100.0
    prev = np.empty(n); prev[0] = c[0]; prev[1:] = c[:-1]
    pa = np.empty(n); pa[0] = a[0]; pa[1:] = a[:-1]
    k = np.floor((prev - off) / R)
    hi = off + R * (k + 1)          # partition above the previous close
    lo = off + R * k                # partition below it

    out = {}
    m_hi = (h >= hi) & (cmin <= hi - AWAY * pa)
    m_lo = (l <= lo) & (cmax >= lo + AWAY * pa)
    for name, m, lvl in (("high", m_hi, hi), ("low", m_lo, lo)):
        idx = np.flatnonzero(m)
        idx = idx[(idx > LOOKBACK) & (idx + max(HOLDS) < n)]
        idx = dedup(idx, DEDUP)
        out[name] = (idx, lvl[idx])
    return out


def stats(pnl, mfe, mae, at, day, nd, pick):
    """Everything worth knowing about a bag of fixed-time trades."""
    n = len(pnl)
    net = pnl - COST_PTS
    s = np.bincount(day, weights=net, minlength=nd)
    cnt = np.bincount(day, minlength=nd).astype(float)
    bs = s[pick].sum(1) / np.maximum(cnt[pick].sum(1), 1)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    gains = net[net > 0].sum()
    losses = -net[net < 0].sum()
    return {
        "n": int(n),
        "win": float((pnl > 0).mean()),
        "mean_pts": float(pnl.mean()),
        "med_pts": float(np.median(pnl)),
        "mean_atr": float((pnl / at).mean()),
        "net_pts": float(net.mean()),
        "ci_lo": float(lo), "ci_hi": float(hi),
        "sd_pts": float(pnl.std(ddof=1)),
        "best": float(pnl.max()), "worst": float(pnl.min()),
        "mfe_mean": float(mfe.mean()), "mfe_p90": float(np.percentile(mfe, 90)),
        "mae_mean": float(mae.mean()), "mae_p90": float(np.percentile(mae, 90)),
        "pf": float(gains / losses) if losses > 0 else float("inf"),
    }


def run_cell(h, l, c, a, idx, lvl, side, hold, n):
    """P&L, and the excursions, for one (partition, direction, hold) cell."""
    entry = lvl
    exit_ = c[np.minimum(idx + hold, n - 1)]
    # sign: +1 means we are long. Fading a HIGH means short; fading a LOW long.
    sgn = side
    pnl = sgn * (exit_ - entry)
    # excursions over the holding window
    m = len(idx)
    hi = np.full(m, -np.inf)
    lo = np.full(m, np.inf)
    for w in range(1, hold + 1):
        j = np.clip(idx + w, 0, n - 1)
        hi = np.maximum(hi, h[j])
        lo = np.minimum(lo, l[j])
    if sgn > 0:
        mfe, mae = hi - entry, entry - lo
    else:
        mfe, mae = entry - lo, hi - entry
    return pnl, np.maximum(mfe, 0.0), np.maximum(mae, 0.0)


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    h, l, c = (np.asarray(npz[k]) for k in ("h", "l", "c"))
    date, yr = np.asarray(npz["date"]), np.asarray(npz["yr"])
    a = atr(h, l, c)
    n = len(c)
    cmin, cmax = c.copy(), c.copy()
    for o in range(1, LOOKBACK):
        cmin[o:] = np.minimum(cmin[o:], c[:-o])
        cmax[o:] = np.maximum(cmax[o:], c[:-o])
    cmin = np.concatenate([[c[0]], cmin[:-1]])
    cmax = np.concatenate([[c[0]], cmax[:-1]])

    rng = np.random.default_rng(29)
    out = {}
    for R in (81.0, 243.0, 729.0):
        ev = arrivals(h, l, c, a, cmin, cmax, R, 0.0, n)
        nulls = [arrivals(h, l, c, a, cmin, cmax, R, j * 100.0 / NPHASE, n)
                 for j in range(1, NPHASE)]
        print("\n" + "=" * 96)
        print("R=%d   arrivals: %s at the high partition, %s at the low"
              % (R, "{:,}".format(len(ev["high"][0])),
                 "{:,}".format(len(ev["low"][0]))))
        print("=" * 96)
        out[str(int(R))] = {}
        for part in ("high", "low"):
            idx, lvl = ev[part]
            u, day = np.unique(date[idx], return_inverse=True)
            nd = len(u)
            pick = rng.integers(0, nd, size=(1500, nd))
            at = a[idx]
            print("\n  reached the %s partition  (%s arrivals, %s days)"
                  % (part.upper(), "{:,}".format(len(idx)), "{:,}".format(nd)))
            print("    %-8s %-5s %8s %7s %9s %9s %9s %8s %8s %9s %9s %8s"
                  % ("trade", "hold", "n", "win", "mean pt", "net pt",
                     "med pt", "best", "worst", "MFE avg", "MAE avg", "PF"))
            for label, sgn in (("fade", -1 if part == "high" else +1),
                               ("follow", +1 if part == "high" else -1)):
                for hold in HOLDS:
                    pnl, mfe, mae = run_cell(h, l, c, a, idx, lvl, sgn, hold, n)
                    st = stats(pnl, mfe, mae, at, day, nd, pick)
                    # shifted-lattice null on the same statistic
                    nv = []
                    for nl in nulls:
                        i2, l2 = nl[part]
                        if len(i2) < 200:
                            continue
                        p2, _, _ = run_cell(h, l, c, a, i2, l2, sgn, hold, n)
                        nv.append(float(p2.mean()))
                    st["null_mean_pts"] = float(np.mean(nv)) if nv else float("nan")
                    st["hold"] = hold
                    st["trade"] = label
                    out[str(int(R))].setdefault(part, []).append(st)
                    print("    %-8s %-5d %8s %7.4f %+9.2f %+9.2f %+9.2f %8.0f %8.0f %9.1f %9.1f %8.2f"
                          % (label, hold, "{:,}".format(st["n"]), st["win"],
                             st["mean_pts"], st["net_pts"], st["med_pts"],
                             st["best"], st["worst"], st["mfe_mean"],
                             st["mae_mean"], st["pf"]))

        # the honest summary line for this block size
        rows = [r for p in out[str(int(R))] for r in out[str(int(R))][p]]
        pos = [r for r in rows if r["ci_lo"] > 0]
        print("\n  cells whose day-clustered 95%% CI on net points excludes zero: %d of %d"
              % (len(pos), len(rows)))
        for r in pos:
            print("     %s partition, %s, %dm: net %+.2f pts  CI [%+.2f, %+.2f]"
                  % (r.get("part", ""), r["trade"], r["hold"], r["net_pts"],
                     r["ci_lo"], r["ci_hi"]))

    json.dump(out, open(os.path.join(HERE, "partition.json"), "w"), indent=1)
    print("\nwrote partition.json")


if __name__ == "__main__":
    main()
