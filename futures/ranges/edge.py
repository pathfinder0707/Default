"""Conditional probabilities you can actually put in a playbook.

Everything else in this repo answers "is the Goldbach lattice special?". This
answers a different question: "given a setup I can identify in real time, what
happens next, and how often?"

The base event is the one mechanism that measured above chance anywhere in this
repo -- break, excursion, retest (polarity.py). Here every retest is kept as a
RECORD rather than a counter, so the sample can be cut by conditions a trader
knows at the moment of entry:

    zone of the level     EXT / EQ / FV / GIP / LLOD / other
    direction             long at broken resistance, short at broken support
    session               NY open hour / RTH / London / Asia / overnight
    excursion             how far price ran past the level before returning
    wait                  how many bars it took to come back
    volatility regime     ATR vs its trailing 5-day average
    liquidity sweep       was a prior-day high/low taken out first
    HTF confluence        is this R=81 level also a level on the R=729 lattice

and by outcome, on a grid of ATR-scaled targets and stops, so the answer is not
just a hit rate but an expectancy.

Two rules make the numbers honest:

  * NO LOOK-AHEAD. Entry is at the level on the retest bar; outcomes resolve
    from the NEXT bar onward. A bar that touches target and stop counts as a
    stop. This is the same fix that took an earlier version of the intraday
    study from a fake +0.305R to a true -0.015R.
  * EVERY SLICE GETS ITS OWN NULL. The identical procedure runs on 6 shifted
    lattices. If a conditional rate is high at the true lattice AND equally
    high at the shifted ones, the number is real but it is a property of
    price behaviour around any line, not of Goldbach. Both are useful and
    they are labelled differently.
"""
import json
import os
import sys

import numpy as np

import gbr

HERE = os.path.dirname(os.path.abspath(__file__))

BREAK_MIN = 1.0        # ATR beyond the level required to call it broken
RETEST_MAX = 240       # bars allowed for the return
HORIZON = 120          # bars to resolve the trade
DEDUP = 120
NPHASE = 7             # true lattice + 6 shifted nulls at j*100/7

FAV = np.array([0.25, 0.5, 0.75, 1.0, 1.5, 2.0])
ADV = np.array([0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0])

# One NQ round turn: commission ~$4 (0.2 index points on a $20 multiplier) plus
# a tick of slippage on the stop exit. Entries and targets are resting limits,
# which is what the event definition already assumes.
COST_PTS = 0.45
BIG = np.int32(10 ** 6)

ZONE_OF = {0: "EXT", 3: "EXT", 97: "EXT",
           47: "EQ", 50: "EQ", 53: "EQ",
           29: "FV", 71: "FV",
           17: "GIP", 83: "GIP",
           7: "LLOD", 93: "LLOD"}
ZONES = ["EXT", "EQ", "FV", "GIP", "LLOD", "other"]
SESSIONS = ["NYopen", "RTHrest", "London", "Asia", "other"]
EXC_BINS = ["exc_1_1.5", "exc_1.5_2.5", "exc_2.5+"]
WAIT_BINS = ["fast_<20", "mid_20_60", "slow_60_240"]
VOL_BINS = ["vol_low", "vol_mid", "vol_high"]
RMULTS = [1.0, 1.5, 2.0, 3.0]


def atr(h, l, c, n=14):
    pc = np.empty_like(c); pc[0] = c[0]; pc[1:] = c[:-1]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))
    out = np.empty_like(tr)
    a = tr[:n].mean()
    out[:n] = a
    for i in range(n, len(tr)):
        a = (a * (n - 1) + tr[i]) / n
        out[i] = a
    return out


def causal_mean(x, w):
    """Trailing mean over w bars, using only past data."""
    cs = np.concatenate([[0.0], np.cumsum(x)])
    out = np.empty_like(x)
    idx = np.arange(len(x))
    lo = np.maximum(idx - w, 0)
    out = (cs[idx + 1] - cs[lo]) / np.maximum(idx + 1 - lo, 1)
    return out


def roll_extremes(h, l, w):
    """Trailing w-bar high and low, inclusive of the current bar."""
    rmax = h.copy()
    rmin = l.copy()
    for off in range(1, w):
        rmax[off:] = np.maximum(rmax[off:], h[:-off])
        rmin[off:] = np.minimum(rmin[off:], l[:-off])
    return rmax, rmin


def prior_day_levels(date, h, l):
    """For every bar, the previous calendar day's high and low."""
    u, first = np.unique(date, return_index=True)
    order = np.argsort(first)
    u, first = u[order], first[order]
    last = np.append(first[1:], len(date))
    dh = np.array([h[a:b].max() for a, b in zip(first, last)])
    dl = np.array([l[a:b].min() for a, b in zip(first, last)])
    pdh = np.concatenate([[np.nan], dh[:-1]])
    pdl = np.concatenate([[np.nan], dl[:-1]])
    day_of = np.searchsorted(u, date)
    return pdh[day_of], pdl[day_of]


def dedup(idx, gap):
    if len(idx) == 0:
        return idx
    keep = [idx[0]]
    for i in idx[1:]:
        if i - keep[-1] >= gap:
            keep.append(i)
    return np.asarray(keep)


def find_retests(h, l, brk, L, at, up, n):
    """First return to L after an excursion of BREAK_MIN ATR beyond it.

    The excursion must be COMPLETE ON AN EARLIER BAR than the retest. Updating
    `gone` before testing for the return lets one wide bar that straddles the
    level count as break, excursion and retest at once -- and 54% of events
    qualified that way, each already a full ATR in profit at the moment of the
    supposed entry. That is not a setup anyone could have traded: the filter
    that selects it is only known once the bar has closed, by which time the
    limit order could not have been resting.

    Also returns the peak excursion reached before the return, which is the
    'how hard did it break' condition.
    """
    m = len(brk)
    gone = np.zeros(m, bool)
    peak = np.zeros(m)
    retest = np.full(m, -1, np.int64)
    thresh = L + BREAK_MIN * at if up else L - BREAK_MIN * at
    for w in range(1, RETEST_MAX + 1):
        j = np.clip(brk + w, 0, n - 1)
        back = (l[j] <= L) if up else (h[j] >= L)
        hit = gone & back & (retest < 0)        # `gone` covers bars < j only
        retest[hit] = j[hit]
        if (retest >= 0).all():
            break
        still = retest < 0
        run = (h[j] - L) / at if up else (L - l[j]) / at
        peak = np.where(still, np.maximum(peak, run), peak)
        gone |= still & ((h[j] >= thresh) if up else (l[j] <= thresh))
    return retest, peak


def first_hits(h, l, idx, L, at, up, n):
    """Bar count to first touch of each favourable and adverse threshold.

    Favourable = further in the break direction (the level holding). Resolution
    starts at w=1: entry is at L on bar idx, and that bar's own range already
    happened, so using it would be look-ahead.
    """
    m = len(idx)
    tf = np.full((m, len(FAV)), BIG, np.int32)
    ta = np.full((m, len(ADV)), BIG, np.int32)

    # The entry bar is treated asymmetrically, and deliberately. A long fills at
    # L because that bar traded DOWN to L, so the bar's high almost always
    # happened before the fill -- counting it as profit would be look-ahead --
    # while its low is at or after the fill and is real risk. So the entry bar
    # can stop you out but cannot pay you.
    adv0 = (L - l[idx]) / at if up else (h[idx] - L) / at
    for k in range(len(ADV)):
        ta[adv0 >= ADV[k], k] = 0

    for w in range(1, HORIZON + 1):
        j = np.clip(idx + w, 0, n - 1)
        fav = (h[j] - L) / at if up else (L - l[j]) / at
        adv = (L - l[j]) / at if up else (h[j] - L) / at
        for k in range(len(FAV)):
            hit = (fav >= FAV[k]) & (tf[:, k] == BIG)
            tf[hit, k] = w
        for k in range(len(ADV)):
            hit = (adv >= ADV[k]) & (ta[:, k] == BIG)
            ta[hit, k] = w
        if (tf[:, -1] != BIG).all() and (ta[:, -1] != BIG).all():
            break
    return tf, ta


def structure_trade(h, l, c, idx, L, at, up, n, rmults):
    """The way a discretionary trader actually takes this: not a blind limit.

    Entry is the CLOSE of the retest bar, so the penetration through the level
    has already happened and is visible. The stop goes just beyond that bar's
    extreme -- the level's low for a long -- which is what defines risk, and the
    target is a multiple of it. This removes the objection that a fixed ATR stop
    is placed inside the level's normal noise.

    Returns, per R multiple, +1 win / -1 loss / 0 unresolved, plus the risk in
    ATR units so expectancy can still be quoted era-neutrally.
    """
    px = c[idx]
    ext = l[idx] if up else h[idx]
    buf = 0.05 * at
    risk = (px - ext + buf) if up else (ext - px + buf)
    risk = np.maximum(risk, 0.05 * at)          # degenerate bars
    stp = px - risk if up else px + risk
    out = {}
    for rm in rmults:
        tgt = px + rm * risk if up else px - rm * risk
        res = np.zeros(len(idx), np.int8)
        live = np.ones(len(idx), bool)
        for w in range(1, HORIZON + 1):
            j = np.clip(idx + w, 0, n - 1)
            ht = (h[j] >= tgt) if up else (l[j] <= tgt)
            hs = (l[j] <= stp) if up else (h[j] >= stp)
            s_now = live & hs
            t_now = live & ht & ~hs             # both in one bar counts as a loss
            res[s_now] = -1
            res[t_now] = 1
            live &= ~(s_now | t_now)
            if not live.any():
                break
        out[rm] = res
    return out, risk / at


def collect(ctx, R, phase):
    """Every qualifying retest at this lattice phase, with its conditions."""
    h, l, c, a = ctx["h"], ctx["l"], ctx["c"], ctx["atr"]
    n = len(c)
    rows = []
    for pct in gbr.LEVELS:
        off = R * (pct + phase) / 100.0
        li = np.floor((c - off) / R)
        d = np.diff(li)
        for up in (True, False):
            cross = np.flatnonzero(d > 0) + 1 if up else np.flatnonzero(d < 0) + 1
            cross = cross[(cross > 20) & (cross + RETEST_MAX + HORIZON < n)]
            cross = dedup(cross, DEDUP)
            if len(cross) == 0:
                continue
            L = off + R * (li[cross] if up else li[cross] + 1)
            rt, peak = find_retests(h, l, cross, L, a[cross], up, n)
            ok = rt >= 0
            if not ok.any():
                continue
            i = rt[ok]
            Lk, pk = L[ok], peak[ok]
            tf, ta = first_hits(h, l, i, Lk, a[i], up, n)
            st, rk = structure_trade(h, l, c, i, Lk, a[i], up, n, RMULTS)
            rows.append({"i": i, "L": Lk, "peak": pk, "up": up, "pct": pct,
                         "tf": tf, "ta": ta, "risk_atr": rk,
                         "st": np.stack([st[m] for m in RMULTS], axis=1)})
    if not rows:
        return None
    out = {
        "i": np.concatenate([r["i"] for r in rows]),
        "L": np.concatenate([r["L"] for r in rows]),
        "peak": np.concatenate([r["peak"] for r in rows]),
        "up": np.concatenate([np.full(len(r["i"]), r["up"]) for r in rows]),
        "pct": np.concatenate([np.full(len(r["i"]), r["pct"]) for r in rows]),
        "tf": np.concatenate([r["tf"] for r in rows]),
        "ta": np.concatenate([r["ta"] for r in rows]),
        "st": np.concatenate([r["st"] for r in rows]),
        "risk_atr": np.concatenate([r["risk_atr"] for r in rows]),
    }
    return out


def annotate(ev, ctx, R):
    """Attach the conditions, all knowable at the moment of entry."""
    i, up = ev["i"], ev["up"]
    tod = ctx["tod"][i]
    z = np.array([ZONE_OF.get(int(p), "other") for p in ev["pct"]])

    sess = np.full(len(i), "other", dtype=object)
    sess[(tod >= 300) & (tod < 530)] = "London"
    sess[(tod >= 2000) | (tod < 200)] = "Asia"
    sess[(tod >= 930) & (tod < 1600)] = "RTHrest"
    sess[(tod >= 930) & (tod < 1030)] = "NYopen"

    excb = np.where(ev["peak"] < 1.5, "exc_1_1.5",
                    np.where(ev["peak"] < 2.5, "exc_1.5_2.5", "exc_2.5+"))

    volr = ctx["volr"][i]
    vb = np.where(volr < 0.85, "vol_low", np.where(volr < 1.2, "vol_mid", "vol_high"))

    # aligned liquidity sweep: for a long at broken resistance, the prior day's
    # low was taken out in the 120 bars up to entry (and price is back above it)
    sw_lo = (ctx["rmin"][i] < ctx["pdl"][i]) & (ctx["c"][i] > ctx["pdl"][i])
    sw_hi = (ctx["rmax"][i] > ctx["pdh"][i]) & (ctx["c"][i] < ctx["pdh"][i])
    sweep = np.where(up, sw_lo, sw_hi)
    sweep = np.where(np.isnan(ctx["pdh"][i]), False, sweep)

    # HTF confluence: is this same price also a Goldbach level of the 729 block?
    p729 = np.mod(ev["L"], 729.0) / 729.0 * 100.0
    dd = np.abs(p729[:, None] - gbr.LEVELS[None, :])
    dd = np.minimum(dd, 100.0 - dd)
    conf = dd.min(axis=1) <= 0.5

    ev.update({"zone": z, "sess": sess, "excb": excb, "volb": vb,
               "sweep": sweep, "conf": conf,
               "waitb": None, "dir": np.where(up, "long", "short")})
    return ev


def boot_day(ev, mask, kf, ka, day, reps=400, seed=0):
    """Expectancy CI resampling whole TRADING DAYS, not individual trades.

    The 20 levels and both directions overlap heavily -- one strong afternoon
    generates dozens of correlated retests. A per-trade standard error on
    467,000 events is therefore far too small to believe. Resampling days keeps
    the within-day correlation intact.
    """
    tf, ka_t = ev["tf"][mask, kf], ev["ta"][mask, ka]
    live = (tf != BIG) | (ka_t != BIG)
    if live.sum() < 200:
        return None
    pnl = np.where(tf[live] < ka_t[live], FAV[kf], -ADV[ka])
    d = day[mask][live]
    u, inv = np.unique(d, return_inverse=True)
    s = np.bincount(inv, weights=pnl, minlength=len(u))
    n = np.bincount(inv, minlength=len(u)).astype(np.float64)
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, len(u), size=(reps, len(u)))
    ev_b = s[pick].sum(axis=1) / np.maximum(n[pick].sum(axis=1), 1)
    lo, hi = np.percentile(ev_b, [2.5, 97.5])
    return {"days": int(len(u)), "ev": float(s.sum() / n.sum()),
            "lo": float(lo), "hi": float(hi),
            "p_pos": float((ev_b > 0).mean())}


def wr(ev, mask, kf, ka):
    """Win rate and expectancy for target FAV[kf] against stop ADV[ka]."""
    tf, ta = ev["tf"][mask, kf], ev["ta"][mask, ka]
    live = (tf != BIG) | (ta != BIG)
    n = int(live.sum())
    if n < 200:
        return None
    win = (tf < ta)[live]
    p = float(win.mean())
    ev_r = p * FAV[kf] - (1 - p) * ADV[ka]
    se = float(np.sqrt(p * (1 - p) / n))
    return {"n": n, "p": p, "se": se, "ev_atr": float(ev_r)}


def main():
    R = float(sys.argv[1]) if len(sys.argv) > 1 else 81.0
    npz = np.load(os.path.join(HERE, "bars.npz"))
    raw = {k: np.asarray(npz[k]) for k in npz.files}
    h, l, c = raw["h"], raw["l"], raw["c"]
    a = atr(h, l, c)
    pdh, pdl = prior_day_levels(raw["date"], h, l)
    rmax, rmin = roll_extremes(h, l, 120)
    ctx = {"h": h, "l": l, "c": c, "atr": a, "yr": raw["yr"], "date": raw["date"],
           "tod": raw["hh"] * 100 + raw["mm"],
           "volr": a / np.maximum(causal_mean(a, 7200), 1e-9),
           "pdh": pdh, "pdl": pdl, "rmax": rmax, "rmin": rmin}

    print("R=%d  bars=%s" % (R, "{:,}".format(len(c))))
    print("collecting true lattice ...")
    true = annotate(collect(ctx, R, 0.0), ctx, R)
    print("  %s retests" % "{:,}".format(len(true["i"])))

    nulls = []
    for j in range(1, NPHASE):
        e = collect(ctx, R, j * 100.0 / NPHASE)
        if e is None:
            continue
        nulls.append(annotate(e, ctx, R))
        print("  null phase %d: %s retests" % (j, "{:,}".format(len(e["i"]))))

    # ---- the conditional table -------------------------------------------
    cuts = [("ALL", lambda e: np.ones(len(e["i"]), bool))]
    for zname in ZONES:
        cuts.append(("zone=" + zname, lambda e, z=zname: e["zone"] == z))
    for s in SESSIONS:
        cuts.append(("sess=" + s, lambda e, s=s: e["sess"] == s))
    for b in EXC_BINS:
        cuts.append((b, lambda e, b=b: e["excb"] == b))
    for b in VOL_BINS:
        cuts.append((b, lambda e, b=b: e["volb"] == b))
    cuts.append(("dir=long", lambda e: e["up"]))
    cuts.append(("dir=short", lambda e: ~e["up"]))
    cuts.append(("sweep=yes", lambda e: e["sweep"]))
    cuts.append(("sweep=no", lambda e: ~e["sweep"]))
    cuts.append(("htf_conf=yes", lambda e: e["conf"]))
    cuts.append(("htf_conf=no", lambda e: ~e["conf"]))
    # the two combinations worth pre-computing: the user's actual context
    cuts.append(("EXT+sweep", lambda e: (e["zone"] == "EXT") & e["sweep"]))
    cuts.append(("EXT+sweep+RTH",
                 lambda e: (e["zone"] == "EXT") & e["sweep"]
                 & np.isin(e["sess"], ["NYopen", "RTHrest"])))
    cuts.append(("EQ+sweep", lambda e: (e["zone"] == "EQ") & e["sweep"]))
    cuts.append(("FV+sweep", lambda e: (e["zone"] == "FV") & e["sweep"]))
    cuts.append(("sweep+exc2.5+",
                 lambda e: e["sweep"] & (e["excb"] == "exc_2.5+")))
    cuts.append(("sweep+vol_high",
                 lambda e: e["sweep"] & (e["volb"] == "vol_high")))
    shallow = lambda e: e["excb"] != "exc_2.5+"
    cuts.append(("shallow", shallow))
    cuts.append(("shallow+sweep", lambda e: shallow(e) & e["sweep"]))
    cuts.append(("shallow+sweep+RTH",
                 lambda e: shallow(e) & e["sweep"]
                 & np.isin(e["sess"], ["NYopen", "RTHrest"])))
    cuts.append(("shallow+EXT", lambda e: shallow(e) & (e["zone"] == "EXT")))
    cuts.append(("shallow+EXT+sweep",
                 lambda e: shallow(e) & (e["zone"] == "EXT") & e["sweep"]))
    cuts.append(("shallow+FVEXT+sweep",
                 lambda e: shallow(e) & np.isin(e["zone"], ["EXT", "FV"])
                 & e["sweep"]))
    cuts.append(("v_shallow", lambda e: e["excb"] == "exc_1_1.5"))
    cuts.append(("v_shallow+sweep",
                 lambda e: (e["excb"] == "exc_1_1.5") & e["sweep"]))

    # (target index, stop index). The wide-stop corners are where the hit rate
    # gets high; the EV columns are what say whether that is worth anything.
    grid = [(0, 3), (0, 4), (0, 5), (1, 1), (1, 3), (1, 4), (1, 5), (1, 6),
            (3, 1), (3, 3), (3, 4), (5, 3), (5, 4)]
    rows = []
    print("\n=== conditional hold rates, target vs stop in ATR ===")
    print("  %-18s %-11s %8s %7s %7s %8s %7s"
          % ("condition", "tgt/stop", "n", "P(win)", "null", "edge", "EV/ATR"))
    for cname, fn in cuts:
        m = fn(true)
        for kf, ka in grid:
            r = wr(true, m, kf, ka)
            if r is None:
                continue
            nps = []
            for e in nulls:
                q = wr(e, fn(e), kf, ka)
                if q:
                    nps.append(q["p"])
            nm = float(np.mean(nps)) if nps else float("nan")
            nsd = float(np.std(nps, ddof=1)) if len(nps) > 1 else float("nan")
            rows.append({"cond": cname, "tgt": float(FAV[kf]), "stop": float(ADV[ka]),
                         "n": r["n"], "p": r["p"], "se": r["se"],
                         "ev_atr": r["ev_atr"], "null_p": nm, "null_sd": nsd,
                         "edge_pp": (r["p"] - nm) * 100.0,
                         "z_vs_null": (r["p"] - nm) / nsd if nsd and nsd > 0 else 0.0})
            print("  %-18s %4.2f/%-5.2f %8s %7.3f %7.3f %+7.2fpp %+7.3f"
                  % (cname, FAV[kf], ADV[ka], "{:,}".format(r["n"]),
                     r["p"], nm, (r["p"] - nm) * 100.0, r["ev_atr"]))

    # ---- entry model B: close of the retest bar, stop beyond its wick ------
    print("\n=== structure entry: close of retest bar, stop beyond the wick ===")
    print("  %-20s %-5s %8s %7s %7s %8s %9s"
          % ("condition", "R:R", "n", "P(win)", "null", "EV in R", "risk/ATR"))
    srows = []
    for cname, fn in cuts:
        m = fn(true)
        if m.sum() < 500:
            continue
        for q, rm in enumerate(RMULTS):
            res = true["st"][m, q]
            live = res != 0
            n = int(live.sum())
            if n < 200:
                continue
            p = float((res[live] == 1).mean())
            evr = p * rm - (1 - p)
            nps = []
            for e in nulls:
                r2 = e["st"][fn(e), q]
                lv = r2 != 0
                if lv.sum() >= 200:
                    nps.append(float((r2[lv] == 1).mean()))
            nm = float(np.mean(nps)) if nps else float("nan")
            rk = float(np.median(true["risk_atr"][m]))
            srows.append({"cond": cname, "rr": rm, "n": n, "p": p,
                          "ev_r": evr, "null_p": nm, "risk_atr": rk,
                          "edge_pp": (p - nm) * 100.0})
            print("  %-20s %-5.1f %8s %7.3f %7.3f %+8.3f %9.2f"
                  % (cname, rm, "{:,}".format(n), p, nm, evr, rk))

    # ---- unconditional geometry: how far does a retest entry run? ---------
    print("\n=== from a retest entry, how far does price go? (all events) ===")
    geo = []
    for k in range(len(FAV)):
        reach = float((true["tf"][:, k] != BIG).mean())
        adv = float((true["ta"][:, k] != BIG).mean())
        geo.append({"x": float(FAV[k]), "p_fav": reach, "p_adv": adv})
        print("  reaches %+.2f ATR in favour: %5.1f%%     against: %5.1f%%"
              % (FAV[k], reach * 100, adv * 100))

    # ---- year by year: does the rule survive out of its own sample? -------
    # A rule that only works in a few years is a rule that was fitted to them.
    RULES = [
        ("baseline: any retest",       lambda e: np.ones(len(e["i"]), bool), 3, 3),
        ("shallow break",              shallow,                              3, 3),
        ("shallow + sweep",            lambda e: shallow(e) & e["sweep"],    3, 3),
        ("shallow + sweep, 0.5/1.0",   lambda e: shallow(e) & e["sweep"],    1, 3),
        ("shallow + sweep, 0.25/2.0",  lambda e: shallow(e) & e["sweep"],    0, 5),
        ("shallow, 2.0/1.0",           shallow,                              5, 3),
    ]
    yrs = sorted(set(int(y) for y in ctx["yr"]))
    yr_at = ctx["yr"][true["i"]]
    atr_at = ctx["atr"][true["i"]]
    day_at = ctx["date"][true["i"]]
    stab = []
    print("\n=== per-year stability (win rate / net points per trade) ===")
    print("  %-26s %6s %7s %8s %9s %8s  %-22s" % ("rule", "yrs+", "n", "P(win)",
                                                  "EV/ATR", "net pts",
                                                  "95% CI on EV/ATR (by day)"))
    for rname, fn, kf, ka in RULES:
        m = fn(true)
        per = []
        for y in yrs:
            mm = m & (yr_at == y)
            r = wr(true, mm, kf, ka)
            if not r:
                continue
            med_atr = float(np.median(atr_at[mm]))
            net = r["ev_atr"] * med_atr - COST_PTS
            per.append({"yr": y, "n": r["n"], "p": r["p"],
                        "ev_atr": r["ev_atr"], "med_atr": med_atr, "net_pts": net})
        if not per:
            continue
        tot = wr(true, m, kf, ka)
        med_all = float(np.median(atr_at[m]))
        pos = sum(1 for p in per if p["net_pts"] > 0)
        bs = boot_day(true, m, kf, ka, day_at)
        stab.append({"rule": rname, "tgt": float(FAV[kf]), "stop": float(ADV[ka]),
                     "n": tot["n"], "p": tot["p"], "ev_atr": tot["ev_atr"],
                     "net_pts_all": tot["ev_atr"] * med_all - COST_PTS,
                     "years_positive": pos, "years": len(per),
                     "boot": bs, "per_year": per})
        print("  %-26s %3d/%-2d %7s %8.3f %+9.3f %+8.2f   [%+.3f, %+.3f] %d days"
              % (rname + " %.2f/%.2f" % (FAV[kf], ADV[ka]), pos, len(per),
                 "{:,}".format(tot["n"]), tot["p"], tot["ev_atr"],
                 tot["ev_atr"] * med_all - COST_PTS,
                 bs["lo"], bs["hi"], bs["days"]))
        print("       net pts ", "  ".join("%d:%+.1f" % (p["yr"], p["net_pts"]) for p in per))
        print("       EV/ATR  ", "  ".join("%d:%+.2f" % (p["yr"], p["ev_atr"]) for p in per))

    out = {"R": R, "n_true": int(len(true["i"])), "rows": rows, "geometry": geo,
           "structure": srows, "stability": stab, "cost_pts": COST_PTS}
    with open(os.path.join(HERE, "edge_%d.json" % int(R)), "w") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote edge_%d.json" % int(R))


if __name__ == "__main__":
    main()
