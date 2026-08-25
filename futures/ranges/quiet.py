"""The quiet-arrival cell: is it Goldbach, does it stack, and does it pay?

One condition survived everything: price drifting into a level on a small bar
and low volume rejects 55.4% of the time measured purely forward, against a
47.1% baseline. It is the first thing in this study to clear a coin flip in
both halves of the sample. Three questions follow, and they are the only ones
that decide whether it means anything.

  1. IS IT THE LATTICE?  Shifted lattices get the identical treatment. Quiet
     arrival almost certainly works at any line -- price drifting somewhere
     tends to keep drifting -- but if the true lattice beats its shifted twins
     under this filter, that is the first real edge in the study.

  2. DOES IT STACK?  The block boundary and the midpoint reject 2.5pp more
     than the other eighteen levels. Quiet arrival adds 8.4pp. If they are
     independent, quiet arrival at a boundary should beat both.

  3. DOES IT PAY?  55.4% is measured with the touch bar excluded from both
     sides, which no fill can do -- you are in during that bar and its
     excursion is real risk. Scored here the way it would actually trade:
     filled at the level, the touch bar able to stop you but not pay you, a
     grid of ATR brackets, net of a round turn, split discovery/validation and
     bootstrapped over whole days.

Thresholds are FIXED numbers rather than in-sample percentiles, so nothing is
fitted: a bar no wider than 0.60 ATR arriving on no more than 0.75x its
trailing typical volume.
"""
import json
import os

import numpy as np

import gbr
import baserate as br
import volume as V
from edge import atr, COST_PTS

HERE = os.path.dirname(os.path.abspath(__file__))
NPHASE = 12
SPLIT = 2019
RANGE_MAX = 0.60          # touch bar no wider than this many ATR
RVOL_MAX = 0.75           # ... on no more than this multiple of typical volume
FAV = np.array([0.25, 0.5, 0.75, 1.0])
ADV = np.array([0.25, 0.5, 0.75, 1.0, 1.5])
BIG = 10 ** 6


def collect(h, l, c, a, cmin, cmax, rvol, R, phase, n):
    """Every touch at this lattice phase, with the quiet flag and the outcome."""
    off = R * phase / 100.0
    I, L, UP = [], [], []
    for pct in gbr.LEVELS:
        o = off + R * pct / 100.0
        for i2, Lk, up in br.approaches(h, l, c, a, cmin, cmax, o, R, n):
            I.append(i2); L.append(Lk); UP.append(np.full(len(i2), up))
    if not I:
        return None
    I = np.concatenate(I); L = np.concatenate(L); UP = np.concatenate(UP)
    quiet = (((h[I] - l[I]) / a[I]) <= RANGE_MAX) & (rvol[I] <= RVOL_MAX)
    return I, L, UP, quiet


def resolve_vec(h, l, I, L, at, UP, n, decide=br.DECIDE):
    """baserate.resolve_touch, but with a per-event direction.

    The shared version takes a scalar `up` because it is called once per
    direction; here the events from both directions are pooled so the quiet
    filter and the level identity can be applied across the whole set at once.
    Same conventions: the touch bar can break you but cannot reject for you.
    """
    brk = np.where(UP, L + decide * at, L - decide * at)
    rej = np.where(UP, L - decide * at, L + decide * at)
    out = np.zeros(len(I), np.int8)
    over = np.where(UP, h[I] - L, L - l[I])
    out[over >= decide * at] = -1
    live = out == 0
    for w in range(1, br.HORIZON + 1):
        j = np.clip(I + w, 0, n - 1)
        hb = np.where(UP, h[j] >= brk, l[j] <= brk)
        hr = np.where(UP, l[j] <= rej, h[j] >= rej)
        bn = live & hb
        rn = live & hr & ~hb
        out[bn] = -1
        out[rn] = 1
        live &= ~(bn | rn)
        if not live.any():
            break
    return out


def race(h, l, I, L, UP, a, n, kf, ka, count_entry_bar=True):
    """Fade filled at the level. The touch bar can stop you but cannot pay you."""
    at = a[I]
    tgt = np.where(UP, L - FAV[kf] * at, L + FAV[kf] * at)   # fade direction
    stp = np.where(UP, L + ADV[ka] * at, L - ADV[ka] * at)
    out = np.zeros(len(I), np.int8)
    if count_entry_bar:
        over = np.where(UP, h[I] - L, L - l[I])
        out[over >= ADV[ka] * at] = -1
    live = out == 0
    for w in range(1, 121):
        j = np.clip(I + w, 0, n - 1)
        hs = np.where(UP, h[j] >= stp, l[j] <= stp)
        ht = np.where(UP, l[j] <= tgt, h[j] >= tgt)
        sn = live & hs
        tn = live & ht & ~hs
        out[sn] = -1
        out[tn] = 1
        live &= ~(sn | tn)
        if not live.any():
            break
    return out


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    h, l, c, v = (np.asarray(npz[k]) for k in ("h", "l", "c", "v"))
    yr, date = np.asarray(npz["yr"]), np.asarray(npz["date"])
    a = atr(h, l, c)
    n = len(c)
    cmin, cmax = c.copy(), c.copy()
    for o in range(1, 60):
        cmin[o:] = np.minimum(cmin[o:], c[:-o])
        cmax[o:] = np.maximum(cmax[o:], c[:-o])
    cmin = np.concatenate([[c[0]], cmin[:-1]])
    cmax = np.concatenate([[c[0]], cmax[:-1]])
    rvol = v / np.maximum(V.roll_med(v, 60), 1.0)

    R = 81.0
    out = {}

    # ---- 1. is it the lattice? ------------------------------------------
    print("=== 1. quiet arrival: lattice, or any line? ===")
    print("    quiet = bar <= %.2f ATR and volume <= %.2fx typical\n"
          % (RANGE_MAX, RVOL_MAX))

    def reject_rate(phase):
        got = collect(h, l, c, a, cmin, cmax, rvol, R, phase, n)
        I, L, UP, q = got
        r = resolve_vec(h, l, I, L, a[I], UP, n)
        d = r != 0
        rej = (r == 1)
        return (float(rej[d & q].mean()), int((d & q).sum()),
                float(rej[d & ~q].mean()), int((d & ~q).sum()))

    tq, nq, tl, nl = reject_rate(0.0)
    nulls = [reject_rate(j * 100.0 / NPHASE) for j in range(1, NPHASE)]
    arr = np.array([x[0] for x in nulls])
    sd = arr.std(ddof=1)
    print("  %-22s %10s %10s %10s %8s"
          % ("", "n", "rejects", "shifted", "z"))
    print("  %-22s %10s %10.4f %10.4f %+8.2f"
          % ("quiet arrival", "{:,}".format(nq), tq, arr.mean(),
             (tq - arr.mean()) / sd if sd > 0 else 0))
    arr2 = np.array([x[2] for x in nulls])
    sd2 = arr2.std(ddof=1)
    print("  %-22s %10s %10.4f %10.4f %+8.2f"
          % ("everything else", "{:,}".format(nl), tl, arr2.mean(),
             (tl - arr2.mean()) / sd2 if sd2 > 0 else 0))
    print("\n  the filter is worth %+.2fpp; the lattice inside it is worth %+.2fpp"
          % ((tq - tl) * 100, (tq - arr.mean()) * 100))
    out["lattice"] = {"quiet": tq, "quiet_null": float(arr.mean()),
                      "other": tl, "n_quiet": nq}

    # ---- 2. does it stack with the boundary? -----------------------------
    print("\n=== 2. does it stack with the block boundary and midpoint? ===")
    got = collect(h, l, c, a, cmin, cmax, rvol, R, 0.0, n)
    I, L, UP, q = got
    r = resolve_vec(h, l, I, L, a[I], UP, n)
    d = r != 0
    I, L, UP, q, rej = I[d], L[d], UP[d], q[d], (r[d] == 1)
    pct = np.round(np.mod(L, R) / R * 100.0).astype(int) % 100
    grid = np.isin(pct, [0, 50])
    print("  %-30s %10s %10s" % ("", "n", "rejects"))
    for nm, m in (("everything", np.ones(len(I), bool)),
                  ("boundary or midpoint", grid),
                  ("quiet arrival", q),
                  ("quiet AND boundary/midpoint", q & grid)):
        print("  %-30s %10s %10.4f"
              % (nm, "{:,}".format(int(m.sum())), float(rej[m].mean())))
    out["stack"] = {"quiet_grid": float(rej[q & grid].mean()),
                    "n": int((q & grid).sum())}

    # ---- 3. does it pay? -------------------------------------------------
    print("\n=== 3. does it pay? fade filled at the level, realistic entry bar ===")
    print("  %-14s %9s %8s %9s %10s %9s %-22s"
          % ("target/stop", "n", "win", "break-even", "EV/ATR",
             "net pts", "95% CI on EV (by day)"))
    day = date[I]
    u, di = np.unique(day, return_inverse=True)
    nd = len(u)
    rg = np.random.default_rng(11)
    pick = rg.integers(0, nd, size=(2000, nd))
    at26 = 16.99
    rows = []
    for kf in range(len(FAV)):
        for ka in range(len(ADV)):
            res = race(h, l, I[q], L[q], UP[q], a, n, kf, ka)
            live = res != 0
            if live.sum() < 500:
                continue
            win = (res[live] == 1).astype(float)
            p = float(win.mean())
            ev = p * FAV[kf] - (1 - p) * ADV[ka]
            dd = di[q][live]
            pnl = win * FAV[kf] - (1 - win) * ADV[ka]
            s = np.bincount(dd, weights=pnl, minlength=nd)
            cnt = np.bincount(dd, minlength=nd).astype(float)
            bs = s[pick].sum(1) / np.maximum(cnt[pick].sum(1), 1)
            lo, hi = np.percentile(bs, [2.5, 97.5])
            net = ev * at26 - COST_PTS
            rows.append({"tgt": float(FAV[kf]), "stop": float(ADV[ka]),
                         "n": int(live.sum()), "p": p, "ev_atr": ev,
                         "net_pts": net, "lo": float(lo), "hi": float(hi)})
            print("  %-14s %9s %8.4f %9.4f %+10.4f %+9.2f  [%+.4f, %+.4f]"
                  % ("%.2f/%.2f" % (FAV[kf], ADV[ka]), "{:,}".format(int(live.sum())),
                     p, ADV[ka] / (FAV[kf] + ADV[ka]), ev, net, lo, hi))
    out["trade"] = rows
    best = max(rows, key=lambda r: r["ev_atr"])
    print("\n  best bracket: %.2f/%.2f  EV %+.4f ATR  net %+.2f pts  CI [%+.4f, %+.4f]"
          % (best["tgt"], best["stop"], best["ev_atr"], best["net_pts"],
             best["lo"], best["hi"]))

    json.dump(out, open(os.path.join(HERE, "quiet.json"), "w"), indent=1)
    print("\nwrote quiet.json")


if __name__ == "__main__":
    main()
