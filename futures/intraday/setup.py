"""Conditional edge study for the specific setup actually traded.

Not "does the lattice work" -- that has been answered. This asks the narrower,
harder question: GIVEN a context and a confirmation, does one of these zones
give a positive-expectancy support/resistance decision?

Specification, as described by the trader:
  zones          0.97-1.00 (and its 0-0.03 mirror), EQ 0.47-0.53, and "FV"
                 (ambiguous -- both plausible readings are tested separately)
  block          R=81 primary, on a 1-5m chart; 243 and 729 also run
  context        price either sweeps liquidity OR taps an HTF FVG (neutral
                 between them, as requested -- both and either are reported)
  confirmation   CISD / MSS class trigger after the tap
  outcome        does price then travel +1 ATR in the expected direction before
                 -1 ATR against it

Every cell is scored against the SAME 20-phase lattice null. That is the whole
point: a zone can look good simply because "price bounces somewhere near here"
is true of any band in a mean-reverting market. The null asks whether THIS band,
at THIS lattice phase, beats an arbitrary band of identical width.

Bracket is ATR-normalised so results are comparable across the sample's 16-fold
change in volatility. Stop-first tie-breaking within a bar.
"""
import json
import os
import sys

import numpy as np

import core

HERE = os.path.dirname(os.path.abspath(__file__))
NPHASE = 20
HORIZON = 120          # bars to resolve the bracket
CONF_W = 20            # bars allowed for the confirmation to appear
SWEEP_W = 60           # lookback defining "took out recent liquidity"
DEDUP = 60
ATR_N = 14
HTF = 15               # minutes, for the FVG context

# zones as (name, list of (lo, hi) percentage bands). All are 6pp wide in total
# so the comparison between them is like-for-like.
ZONES = {
    "EXT_0_100": [(97.0, 100.0), (0.0, 3.0)],
    "EQ_50":     [(47.0, 53.0)],
    "FV_29_71":  [(27.5, 30.5), (69.5, 72.5)],
    "GIP_17_83": [(15.5, 18.5), (81.5, 84.5)],
}


# ------------------------------------------------------------ precomputation
def atr(h, l, c, n=ATR_N):
    pc = np.empty_like(c); pc[0] = c[0]; pc[1:] = c[:-1]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    out = np.empty_like(tr)
    a = tr[:n].mean()
    out[:n] = a
    for i in range(n, len(tr)):                      # Wilder smoothing
        a = (a * (n - 1) + tr[i]) / n
        out[i] = a
    return out


def roll_extreme(x, w, kind):
    """Rolling min/max over the PREVIOUS w bars (excluding the current one)."""
    n = len(x)
    out = np.full(n, np.nan)
    f = np.minimum if kind == "min" else np.maximum
    acc = x[:-1].copy()
    cur = np.full(n - 1, x[0])
    # sparse-table style doubling for O(n log w)
    tab = [x[:-1].copy()]
    j = 1
    while (1 << j) <= w:
        prev = tab[-1]; half = 1 << (j - 1)
        cur = prev.copy()
        cur[half:] = f(prev[half:], prev[:-half])
        tab.append(cur)
        j += 1
    k = max(0, j - 1)
    span = 1 << k
    a = tab[k]
    idx = np.arange(n - 1)
    lo = np.clip(idx, 0, len(a) - 1)
    hi = np.clip(idx - (w - span), 0, len(a) - 1)
    res = f(a[lo], a[hi])
    out[1:] = res
    return out


def run_starts(o, c):
    """Index of the first candle of the current same-direction candle run."""
    n = len(c)
    bear = c < o
    bull = c > o
    def starts(mask):
        s = np.where(mask & ~np.r_[False, mask[:-1]], np.arange(n), -1)
        return np.maximum.accumulate(s)
    return starts(bear), starts(bull)


def htf_fvg_mask(ts, o, h, l, c, minutes=HTF):
    """Bars sitting inside an unfilled higher-timeframe fair value gap.

    A bullish HTF FVG is a 3-bar pattern where bar1.high < bar3.low; the gap is
    that interval. It stays live until price trades fully through it.
    """
    n = len(c)
    # build HTF bars by integer-dividing the minute index
    grp = np.arange(n) // minutes
    nb = grp[-1] + 1
    hh = np.full(nb, -np.inf); ll = np.full(nb, np.inf)
    np.maximum.at(hh, grp, h)
    np.minimum.at(ll, grp, l)
    first_idx = np.zeros(nb, np.int64)
    np.minimum.at(first_idx, grp, np.arange(n))
    # recompute first index per group properly
    first_idx = np.full(nb, n, np.int64)
    np.minimum.at(first_idx, grp, np.arange(n))

    inside = np.zeros(n, bool)
    for k in range(2, nb):
        for lo, hi in ((hh[k - 2], ll[k]), (hh[k], ll[k - 2])):
            if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
                continue
            start = int(first_idx[k])
            if start >= n:
                continue
            stop = min(n, start + minutes * 80)      # gap considered live ~20h
            seg = slice(start, stop)
            hit = (l[seg] <= hi) & (h[seg] >= lo)
            if not hit.any():
                continue
            # kill it once price fully traverses the gap
            through = np.flatnonzero((l[seg] <= lo) & (h[seg] >= hi))
            end = through[0] + 1 if len(through) else (stop - start)
            inside[start:start + end] |= hit[:end]
    return inside


# ------------------------------------------------------------------ the test
def zone_touches(c, R, bands, phase):
    """Bars whose close sits inside the zone at this lattice phase."""
    pct = np.mod(c - R * phase / 100.0, R) / R * 100.0
    m = np.zeros(len(c), bool)
    for lo, hi in bands:
        m |= (pct >= lo) & (pct < hi)
    return m


def first_entries(mask, rth, dedup=DEDUP):
    """First bar of each distinct visit to the zone, during RTH."""
    entry = mask & ~np.r_[False, mask[:-1]] & rth
    idx = np.flatnonzero(entry)
    if len(idx) == 0:
        return idx
    keep = [idx[0]]
    for i in idx[1:]:
        if i - keep[-1] >= dedup:
            keep.append(i)
    return np.asarray(keep)


def resolve(h, l, idx, entry_px, is_long, risk, horizon=HORIZON):
    """P(+1R before -1R), vectorised over trades by looping the horizon."""
    n = len(h)
    tgt = np.where(is_long, entry_px + risk, entry_px - risk)
    stp = np.where(is_long, entry_px - risk, entry_px + risk)
    out = np.zeros(len(idx), np.int8)
    live = np.ones(len(idx), bool)
    # Start at w=1. Entry is at the CLOSE of bar idx, so that bar's own high and
    # low already happened before the fill -- resolving against them is
    # look-ahead, and it biases the win rate upward because the entry bar of a
    # reversal tends to have its extreme on the profitable side of its close.
    for w in range(1, horizon + 1):
        j = np.clip(idx + w, 0, n - 1)
        hj, lj = h[j], l[j]
        ht = np.where(is_long, hj >= tgt, lj <= tgt)
        hs = np.where(is_long, lj <= stp, hj >= stp)
        s_now = live & hs
        t_now = live & ht & ~hs          # stop wins a tie inside one bar
        out[s_now] = -1
        out[t_now] = 1
        live &= ~(s_now | t_now)
        if not live.any():
            break
    return out


def evaluate(bars, R, bands, phase, ctx, conf):
    d = bars
    idx = first_entries(zone_touches(d["c"], R, bands, phase), d["rth"])
    idx = idx[(idx > SWEEP_W) & (idx + HORIZON < len(d["c"]))]
    if len(idx) == 0:
        return None

    # direction: arrived from above -> treat the zone as support -> long
    from_above = d["c"][idx - 5] > d["c"][idx]
    is_long = from_above

    # --- context filter -----------------------------------------------------
    swept = np.where(from_above,
                     d["l"][idx] < d["rmin"][idx],
                     d["h"][idx] > d["rmax"][idx])
    infvg = d["fvg"][idx]
    if ctx == "sweep":
        sel = swept
    elif ctx == "fvg":
        sel = infvg
    elif ctx == "either":
        sel = swept | infvg
    elif ctx == "both":
        sel = swept & infvg
    else:
        sel = np.ones(len(idx), bool)
    idx, is_long = idx[sel], is_long[sel]
    if len(idx) == 0:
        return None

    # --- confirmation -------------------------------------------------------
    if conf == "cisd":
        origin = np.where(is_long, d["bear_start"][idx], d["bull_start"][idx])
        ok = origin >= 0
        idx, is_long, origin = idx[ok], is_long[ok], origin[ok]
        if len(idx) == 0:
            return None
        lvl = d["o"][origin]
        trig = np.full(len(idx), -1, np.int64)
        for w in range(1, CONF_W + 1):
            j = np.clip(idx + w, 0, len(d["c"]) - 1)
            fire = (trig < 0) & np.where(is_long, d["c"][j] > lvl, d["c"][j] < lvl)
            trig[fire] = j[fire]
        got = trig >= 0
        idx, is_long, trig = idx[got], is_long[got], trig[got]
        if len(idx) == 0:
            return None
        entry_idx = trig
    else:
        entry_idx = idx

    entry_px = d["c"][entry_idx]
    risk = d["atr"][entry_idx]
    good = np.isfinite(risk) & (risk > 0)
    entry_idx, entry_px, risk, is_long = (entry_idx[good], entry_px[good],
                                          risk[good], is_long[good])
    if len(entry_idx) < 30:
        return None

    r = resolve(d["h"], d["l"], entry_idx, entry_px, is_long, risk)
    won, lost = (r == 1), (r == -1)
    dec = won.sum() + lost.sum()
    if dec < 30:
        return None
    return {
        "n": int(len(r)),
        "n_decided": int(dec),
        "win": float(won.sum() / dec),
        "ev_R": float((won.sum() - lost.sum()) / dec),
        "unresolved": float((r == 0).mean()),
        "pct_long": float(is_long.mean()),
    }


def main():
    raw = np.load(os.path.join(HERE, "bars.npz"))
    d = {k: raw[k] for k in ("o", "h", "l", "c", "yr", "hh", "mm")}
    tod = d["hh"] * 100 + d["mm"]
    d["rth"] = (tod >= 930) & (tod < 1600)
    print("precomputing ATR, rolling extremes, candle runs, HTF FVGs ...")
    d["atr"] = atr(d["h"], d["l"], d["c"])
    d["rmin"] = roll_extreme(d["l"], SWEEP_W, "min")
    d["rmax"] = roll_extreme(d["h"], SWEEP_W, "max")
    d["bear_start"], d["bull_start"] = run_starts(d["o"], d["c"])
    d["fvg"] = htf_fvg_mask(None, d["o"], d["h"], d["l"], d["c"])
    print("  HTF FVG coverage: %.1f%% of bars" % (d["fvg"].mean() * 100))
    print("  RTH bars: %s" % "{:,}".format(int(d["rth"].sum())))

    rows = []
    for R in (81, 243, 729):
        for zname, bands in ZONES.items():
            for ctx in ("any", "sweep", "fvg", "either"):
                for conf in ("none", "cisd"):
                    true = evaluate(d, R, bands, 0.0, ctx, conf)
                    if true is None:
                        continue
                    nulls = []
                    for j in range(1, NPHASE):
                        m = evaluate(d, R, bands, j * 100.0 / NPHASE, ctx, conf)
                        if m:
                            nulls.append(m["ev_R"])
                    if len(nulls) < 5:
                        continue
                    a = np.array(nulls)
                    z = (true["ev_R"] - a.mean()) / a.std(ddof=1) if a.std(ddof=1) > 0 else 0.0
                    row = dict(R=R, zone=zname, ctx=ctx, conf=conf,
                               null_mean=float(a.mean()), null_sd=float(a.std(ddof=1)),
                               z=float(z), **true)
                    rows.append(row)
                    print("  R=%-4d %-11s %-7s %-5s  n=%-6d win %.3f  EV %+.3fR  "
                          "null %+.3f  z=%+.2f"
                          % (R, zname, ctx, conf, row["n_decided"], row["win"],
                             row["ev_R"], row["null_mean"], row["z"]))

    with open(os.path.join(HERE, "setup.json"), "w") as fh:
        json.dump(rows, fh, indent=1)
    print("\n%d cells -> setup.json" % len(rows))


if __name__ == "__main__":
    main()
