"""Boundary + entry module + take profit at equilibrium.

The full setup as traded: price reaches the high or low of the PO3 block, an
entry module confirms, and the target is an equilibrium. Two branches:

    REVERSAL      confirmation says the level held -> trade back into the
                  range, TP at the EQ of the current block (R/2 away)
    CONTINUATION  confirmation says the level broke -> trade with it, TP at
                  the EQ of the NEXT block (also R/2 away)

Both targets sit exactly half a block from the boundary, which is what makes
this testable: the two branches are mirror images at equal distance, so a coin
flip is the right intuition and a shifted lattice is a matched control.

ENTRY MODULES, each detectable at a bar close and nothing else:

    immediate   no confirmation -- fill at the level. The baseline.
    htf3/5/15/30  wait for the N-minute candle containing the touch to close.
                  Closed back inside -> reversal. Closed through ->
                  continuation. This module chooses its own branch.
    quiet       the touch bar is small (<=0.6 ATR) and on low volume (<=0.75x).
    cisd        change in state of delivery: price closes back through the
                  OPEN of the candle that made the extreme.
    mss         market structure shift: price closes beyond the last 20-bar
                  fractal swing on the other side.
    ifvg        a fair value gap forms on the push through the level and price
                  then closes back through it.

STOP is the structural one a trader would actually use: the extreme reached
between the touch and the entry, plus a small buffer. That makes R:R vary by
trade, so results are reported in R as well as points.

Nothing is fitted. Every threshold is a round number fixed in advance, and
every module is scored against the identical procedure on shifted lattices.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NPHASE = 8
CONFIRM_W = 30        # bars allowed for the module to confirm
HORIZON = 720         # bars to resolve the trade
AWAY = 1.0
LOOKBACK = 60
DEDUP = 120
BUF = 0.05            # stop buffer beyond the structural extreme, in ATR
MIN_RISK_ATR = 0.50   # ... and no stop tighter than this, because a two-tick
                      # stop is not a stop
COST = 0.45
SPLIT = 2019


def atr(h, l, c, n=14):
    pc = np.empty_like(c); pc[0] = c[0]; pc[1:] = c[:-1]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    out = np.empty_like(tr); a = tr[:n].mean(); out[:n] = a
    for i in range(n, len(tr)):
        a = (a * (n - 1) + tr[i]) / n
        out[i] = a
    return out


def dedup(idx, gap):
    if len(idx) == 0:
        return idx
    keep = [idx[0]]
    for i in idx[1:]:
        if i - keep[-1] >= gap:
            keep.append(i)
    return np.asarray(keep)


def fractal(h, l, k=20):
    """Swing highs and lows of strength k, as forward-filled last-known levels."""
    n = len(h)
    hi_nb = np.full(n, -np.inf); lo_nb = np.full(n, np.inf)
    for off in range(1, k + 1):
        hi_nb[off:] = np.maximum(hi_nb[off:], h[:-off])
        hi_nb[:-off] = np.maximum(hi_nb[:-off], h[off:])
        lo_nb[off:] = np.minimum(lo_nb[off:], l[:-off])
        lo_nb[:-off] = np.minimum(lo_nb[:-off], l[off:])
    is_hi = h > hi_nb
    is_lo = l < lo_nb
    last_hi = np.where(is_hi, h, np.nan)
    last_lo = np.where(is_lo, l, np.nan)
    # a swing is only known k bars later, so shift before forward filling
    last_hi = np.roll(last_hi, k); last_lo = np.roll(last_lo, k)
    last_hi[:k] = np.nan; last_lo[:k] = np.nan
    for arr in (last_hi, last_lo):
        m = np.isnan(arr)
        i = np.where(~m, np.arange(len(arr)), 0)
        np.maximum.accumulate(i, out=i)
        arr[:] = arr[i]
    return last_hi, last_lo


def touches(h, l, c, a, cmin, cmax, R, phase, n):
    """Qualifying arrivals at the block high and low."""
    off = R * phase / 100.0
    prev = np.empty(n); prev[0] = c[0]; prev[1:] = c[:-1]
    pa = np.empty(n); pa[0] = a[0]; pa[1:] = a[:-1]
    k = np.floor((prev - off) / R)
    hi_b = off + R * (k + 1)
    lo_b = off + R * k
    out = {}
    for name, m, B in (("high", (h >= hi_b) & (cmin <= hi_b - AWAY * pa), hi_b),
                       ("low", (l <= lo_b) & (cmax >= lo_b + AWAY * pa), lo_b)):
        idx = np.flatnonzero(m)
        idx = idx[(idx > LOOKBACK) & (idx + CONFIRM_W + HORIZON < n)]
        idx = dedup(idx, DEDUP)
        out[name] = (idx, B[idx])
    return out


def confirm(mod, o, h, l, c, v, a, rvol, fh, fl, idx, B, is_high, n):
    """Return entry bar, entry price, direction (+1 long/-1 short), stop price.

    Direction is chosen by the module where the module implies one; otherwise
    both branches are run separately by the caller.
    """
    m = len(idx)
    ent = np.full(m, -1, np.int64)
    side = np.zeros(m, np.int8)

    if mod == "immediate":
        ent = idx.copy()
        side = np.where(is_high, -1, 1).astype(np.int8) * np.ones(m, np.int8)
        return ent, B.copy(), side

    if mod == "quiet":
        ok = (((h[idx] - l[idx]) / a[idx]) <= 0.60) & (rvol[idx] <= 0.75)
        ent = np.where(ok, idx, -1)
        side = np.full(m, -1 if is_high else 1, np.int8)
        return ent, B.copy(), side

    if mod.startswith("htf"):
        tf = int(mod[3:])
        # the candle containing the touch ends at the next multiple of tf
        # (minute-of-day based, which is how the chart draws it)
        return None  # handled by caller, needs bar clock

    # --- confirmations that need a forward scan --------------------------
    ext = h[idx].copy() if is_high else l[idx].copy()
    # the reference open: the candle that made the extreme so far
    ref_open = o[idx].copy()
    fvg_edge = np.full(m, np.nan)
    got = np.zeros(m, bool)
    entry_px = B.copy()

    for w in range(0, CONFIRM_W + 1):
        j = np.clip(idx + w, 0, n - 1)
        newext = (h[j] > ext) if is_high else (l[j] < ext)
        ref_open = np.where(newext & ~got, o[j], ref_open)
        ext = np.where(newext & ~got, h[j] if is_high else l[j], ext)
        if w >= 2:
            jm2 = np.clip(idx + w - 2, 0, n - 1)
            gap = (l[j] > h[jm2]) if is_high else (h[j] < l[jm2])
            edge = np.where(is_high, l[j], h[j])
            fvg_edge = np.where(gap & ~got, edge, fvg_edge)
        if w == 0:
            continue
        if mod == "cisd":
            fire = (c[j] < ref_open) if is_high else (c[j] > ref_open)
        elif mod == "mss":
            ref = fl[idx] if is_high else fh[idx]
            fire = (c[j] < ref) if is_high else (c[j] > ref)
            fire &= ~np.isnan(ref)
        elif mod == "ifvg":
            fire = (c[j] < fvg_edge) if is_high else (c[j] > fvg_edge)
            fire &= ~np.isnan(fvg_edge)
        else:
            raise ValueError(mod)
        hit = fire & ~got
        ent = np.where(hit, j, ent)
        entry_px = np.where(hit, c[j], entry_px)
        got |= hit
        if got.all():
            break
    ent = np.where(got, ent, -1)
    side = np.full(m, -1 if is_high else 1, np.int8)
    return ent, entry_px, side


def htf_confirm(c, h, l, date, hh, mm, tf, idx, B, is_high, n):
    """Wait for the N-minute candle containing the touch to close.

    Closed back inside the block -> reversal. Closed through -> continuation.
    The module picks its own branch, which is the rule as stated.
    """
    key = date.astype(np.int64) * 10000 + (hh * 60 + mm) // tf
    # last bar of the candle each touch sits in
    last = np.empty(n, np.int64)
    u, first = np.unique(key, return_index=True)
    order = np.argsort(first); first = first[order]
    ends = np.append(first[1:], n) - 1
    which = np.searchsorted(first, idx, side="right") - 1
    ent = ends[which]
    ok = (ent > idx) & (ent + HORIZON < n)
    ent = np.where(ok, ent, -1)
    closed_through = (c[np.clip(ent, 0, n - 1)] > B) if is_high \
        else (c[np.clip(ent, 0, n - 1)] < B)
    # reversal when it closed back inside; continuation when it closed through
    side = np.where(closed_through, (1 if is_high else -1),
                    (-1 if is_high else 1)).astype(np.int8)
    return ent, c[np.clip(ent, 0, n - 1)].copy(), side, closed_through


def run_trades(h, l, c, a, ent, entry_px, side, B, R, idx, is_high, n):
    """TP at the EQ half a block away; stop beyond the extreme since the touch."""
    ok = ent >= 0
    if ok.sum() < 100:
        return None
    e, p, s, b, t0 = ent[ok], entry_px[ok], side[ok], B[ok], idx[ok]
    # target: the EQ in the direction of the trade, half a block from the line
    tgt = b + np.where(s > 0, 0.5 * R, -0.5 * R)
    # stop: the extreme reached between the touch and the entry, plus a buffer
    m = len(e)
    ext = np.empty(m)
    for i in range(m):
        lo_i, hi_i = t0[i], e[i]
        seg_h = h[lo_i:hi_i + 1]; seg_l = l[lo_i:hi_i + 1]
        ext[i] = seg_h.max() if s[i] < 0 else seg_l.min()
    stop = ext + np.where(s > 0, -BUF * a[e], BUF * a[e])
    # A structural stop with no floor is not a stop. Where the entry sits at
    # the level and the extreme is two ticks away, risk collapses toward zero,
    # R:R explodes into the hundreds, and those trades lose essentially always
    # because the stop is inside the spread's noise. Left unfloored it produced
    # average R:R of 635 with a 0.6% hit rate -- an artifact, not a strategy.
    # Nobody trades a two-tick stop, so the stop is widened to a realistic
    # minimum where structure alone would put it closer.
    risk = np.maximum(np.abs(p - stop), MIN_RISK_ATR * a[e])
    stop = p - s * risk
    good = risk > 1e-6
    e, p, s, tgt, stop, risk = (x[good] for x in (e, p, s, tgt, stop, risk))
    if len(e) < 100:
        return None

    res = np.zeros(len(e), np.int8)
    live = np.ones(len(e), bool)
    for w in range(1, HORIZON + 1):
        j = np.clip(e + w, 0, n - 1)
        ht = np.where(s > 0, h[j] >= tgt, l[j] <= tgt)
        hs = np.where(s > 0, l[j] <= stop, h[j] >= stop)
        sn = live & hs
        tn = live & ht & ~hs
        res[sn] = -1; res[tn] = 1
        live &= ~(sn | tn)
        if not live.any():
            break
    dec = res != 0
    if dec.sum() < 100:
        return None
    win = res[dec] == 1
    # every one of these must be masked by `dec`; tgt, p and risk are still
    # full length here and mixing masked with unmasked silently mis-pairs the
    # reward of one trade with the risk of another
    reward = np.abs(tgt - p)[dec]
    risk_d = risk[dec]
    rr = reward / risk_d
    pnl_pts = np.where(win, reward, -risk_d) - COST
    pnl_r = np.where(win, rr, -1.0)
    return {"e": e[dec], "win": win, "rr": rr, "pts": pnl_pts, "r": pnl_r}


MODULES = ["immediate", "quiet", "cisd", "mss", "ifvg",
           "htf3", "htf5", "htf15", "htf30"]


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    o, h, l, c, v = (np.asarray(npz[k]) for k in ("o", "h", "l", "c", "v"))
    date, hh, mm = (np.asarray(npz[k]) for k in ("date", "hh", "mm"))
    yr = np.asarray(npz["yr"])
    a = atr(h, l, c)
    n = len(c)
    cmin, cmax = c.copy(), c.copy()
    for off in range(1, LOOKBACK):
        cmin[off:] = np.minimum(cmin[off:], c[:-off])
        cmax[off:] = np.maximum(cmax[off:], c[:-off])
    cmin = np.concatenate([[c[0]], cmin[:-1]])
    cmax = np.concatenate([[c[0]], cmax[:-1]])
    import volume as V
    rvol = v / np.maximum(V.roll_med(v, 60), 1.0)
    fh, fl = fractal(h, l, 20)

    rng = np.random.default_rng(77)
    out = {}
    for R in (243.0, 729.0):
        print("\n" + "=" * 104)
        print("R=%d   boundary + entry module + TP at the EQ (half a block away)" % R)
        print("=" * 104)
        print("  %-11s %-6s %8s %7s %7s %9s %9s %8s %8s  %-20s"
              % ("module", "branch", "trades", "win", "med R", "EV in R",
                 "net pts", "shifted", "z", "95% CI on R (by day)"))
        out[str(int(R))] = {}

        def cell(phase):
            """All modules at one lattice phase."""
            tt = touches(h, l, c, a, cmin, cmax, R, phase, n)
            res = {}
            for side_name, (idx, B) in tt.items():
                is_high = side_name == "high"
                for mod in MODULES:
                    if mod.startswith("htf"):
                        e, p, s, thru = htf_confirm(c, h, l, date, hh, mm,
                                                    int(mod[3:]), idx, B,
                                                    is_high, n)
                        for br, mask in (("reversal", ~thru), ("continuation", thru)):
                            if mask.sum() < 100:
                                continue
                            r = run_trades(h, l, c, a, np.where(mask, e, -1),
                                           p, s, B, R, idx, is_high, n)
                            if r:
                                res["%s|%s|%s" % (mod, side_name, br)] = r
                    else:
                        got = confirm(mod, o, h, l, c, v, a, rvol, fh, fl,
                                      idx, B, is_high, n)
                        if got is None:
                            continue
                        e, p, s = got
                        for br, sgn in (("reversal", 1), ("continuation", -1)):
                            r = run_trades(h, l, c, a, e, p,
                                           (s * sgn).astype(np.int8), B, R,
                                           idx, is_high, n)
                            if r:
                                res["%s|%s|%s" % (mod, side_name, br)] = r
            return res

        true = cell(0.0)
        nulls = [cell(j * 100.0 / NPHASE) for j in range(1, NPHASE)]
        for key in sorted(true):
            r = true[key]
            mod, side_name, br = key.split("|")
            ev = float(r["r"].mean())
            dd = date[r["e"]]
            u, di = np.unique(dd, return_inverse=True)
            nd = len(u)
            s_ = np.bincount(di, weights=r["r"], minlength=nd)
            cnt = np.bincount(di, minlength=nd).astype(float)
            pick = rng.integers(0, nd, size=(1000, nd))
            bs = s_[pick].sum(1) / np.maximum(cnt[pick].sum(1), 1)
            lo, hi = np.percentile(bs, [2.5, 97.5])
            nv = [float(x[key]["r"].mean()) for x in nulls if key in x]
            nm = float(np.mean(nv)) if nv else float("nan")
            sd = float(np.std(nv, ddof=1)) if len(nv) > 2 else float("nan")
            z = (ev - nm) / sd if sd and sd > 0 else 0.0
            out[str(int(R))][key] = {
                "n": int(len(r["r"])), "win": float(r["win"].mean()),
                "avg_rr": float(np.median(r["rr"])), "ev_r": ev,
                "net_pts": float(r["pts"].mean()), "null": nm, "z": float(z),
                "lo": float(lo), "hi": float(hi)}
            print("  %-11s %-6s %8s %7.3f %7.2f %+9.3f %+9.2f %8.3f %+8.2f  [%+.3f, %+.3f]"
                  % (mod, br[:4], "{:,}".format(len(r["r"])),
                     r["win"].mean(), np.median(r["rr"]), ev, r["pts"].mean(),
                     nm, z, lo, hi))

    json.dump(out, open(os.path.join(HERE, "entry.json"), "w"), indent=1)
    print("\nwrote entry.json")


if __name__ == "__main__":
    main()
