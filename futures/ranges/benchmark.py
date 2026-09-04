"""Can this framework find an edge at all? A control on every null in the repo.

Every Goldbach test here has come back flat. There are two possible reasons
and they demand opposite responses:

  1. the lattice carries no edge, or
  2. the measurement is too harsh -- the cost model, the entry-bar convention,
     the day-clustered intervals -- and would report ANY strategy as flat.

The way to tell is to point the same machinery at effects that are documented,
well known, and have nothing to do with Goldbach. If the framework finds them,
the nulls mean what they say. If it finds nothing anywhere, the framework is
the problem and every conclusion in this repo needs revisiting.

Six candidates, all classic, none involving a level:

  overnight       long the close-to-open session. The best documented anomaly
                  in equity index futures -- essentially all of the index's
                  return has historically accrued outside RTH.
  rth_long        the mirror: long 09:30 to 16:00.
  gap_fade        fade the opening gap, exit at the close.
  gap_follow      the opposite.
  orb             opening-range breakout: first 30 minutes, trade the break,
                  exit at the close.
  pdh_pdl         break of the prior day's high or low, follow, exit at close.

Same cost, same day-clustered bootstrap, same discovery/validation split as
everything else, so the comparison is like for like.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
COST = 0.45
SPLIT = 2019
NBOOT = 2000


def sessions(date, tod):
    """Index of the RTH open, the RTH close, and the prior close, per day."""
    rth = (tod >= 930) & (tod < 1600)
    u = np.unique(date[rth])
    idx_open = np.zeros(len(u), np.int64)
    idx_close = np.zeros(len(u), np.int64)
    for i, d in enumerate(u):
        m = np.flatnonzero(rth & (date == d))
        idx_open[i] = m[0]
        idx_close[i] = m[-1]
    return u, idx_open, idx_close


def report(name, pnl, days, out):
    """Same statistics used everywhere else in this repo."""
    n = len(pnl)
    if n < 200:
        return
    net = pnl - COST
    u, inv = np.unique(days, return_inverse=True)
    nd = len(u)
    s = np.bincount(inv, weights=net, minlength=nd)
    cnt = np.bincount(inv, minlength=nd).astype(float)
    rng = np.random.default_rng(5)
    pick = rng.integers(0, nd, size=(NBOOT, nd))
    bs = s[pick].sum(1) / np.maximum(cnt[pick].sum(1), 1)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    g = net[net > 0].sum(); b = -net[net < 0].sum()
    out[name] = {"n": int(n), "win": float((pnl > 0).mean()),
                 "mean": float(pnl.mean()), "net": float(net.mean()),
                 "med": float(np.median(pnl)), "lo": float(lo), "hi": float(hi),
                 "pf": float(g / b) if b > 0 else None,
                 "total": float(net.sum())}
    star = "  <<<" if lo > 0 else ""
    print("  %-12s %7s %7.3f %+9.3f %+9.3f %+11.1f %7.2f  [%+.3f, %+.3f]%s"
          % (name, "{:,}".format(n), out[name]["win"], pnl.mean(),
             out[name]["net"], out[name]["total"], out[name]["pf"] or 0,
             lo, hi, star))


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    o, h, l, c = (np.asarray(npz[k]) for k in ("o", "h", "l", "c"))
    date = np.asarray(npz["date"])
    yr = np.asarray(npz["yr"])
    tod = np.asarray(npz["hh"]) * 100 + np.asarray(npz["mm"])
    u, io, ic = sessions(date, tod)
    print("%s RTH sessions, %s -> %s\n" % ("{:,}".format(len(u)), u[0], u[-1]))

    print("  %-12s %7s %7s %9s %9s %11s %7s  %s"
          % ("strategy", "n", "win", "mean", "net", "total pts", "PF",
             "95% CI on net (by day)"))
    out = {}

    # 1. overnight: prior RTH close -> this RTH open
    pnl = c[io[1:]] - c[ic[:-1]]
    report("overnight", pnl, u[1:], out)

    # 2. RTH: open -> close, long
    report("rth_long", c[ic] - c[io], u, out)

    # 3/4. gap fade and follow, held to the close
    gap = c[io[1:]] - c[ic[:-1]]
    move = c[ic[1:]] - c[io[1:]]
    report("gap_fade", -np.sign(gap) * move, u[1:], out)
    report("gap_follow", np.sign(gap) * move, u[1:], out)

    # 5. opening range breakout: first 30 minutes, follow the break
    orb = []
    odays = []
    for i in range(len(u)):
        a, b = io[i], ic[i]
        if b - a < 60:
            continue
        rh = h[a:a + 30].max(); rl = l[a:a + 30].min()
        seg_h, seg_l, seg_c = h[a + 30:b + 1], l[a + 30:b + 1], c[a + 30:b + 1]
        up = np.flatnonzero(seg_h >= rh)
        dn = np.flatnonzero(seg_l <= rl)
        fu = up[0] if len(up) else 10 ** 9
        fd = dn[0] if len(dn) else 10 ** 9
        if fu == fd == 10 ** 9:
            continue
        # fill at the level only if price actually traded through it; if the
        # bar that triggers opened beyond it, you fill at the open
        if fu < fd:
            j = a + 30 + fu
            orb.append(c[b] - max(rh, o[j]))
        else:
            j = a + 30 + fd
            orb.append(min(rl, o[j]) - c[b])
        odays.append(u[i])
    report("orb", np.array(orb), np.array(odays), out)

    # 6. prior-day high/low break, follow, exit at the close
    pdh = np.array([h[io[i]:ic[i] + 1].max() for i in range(len(u))])
    pdl = np.array([l[io[i]:ic[i] + 1].min() for i in range(len(u))])
    pb, pdays = [], []
    for i in range(1, len(u)):
        a, b = io[i], ic[i]
        seg_h, seg_l = h[a:b + 1], l[a:b + 1]
        up = np.flatnonzero(seg_h >= pdh[i - 1])
        dn = np.flatnonzero(seg_l <= pdl[i - 1])
        fu = up[0] if len(up) else 10 ** 9
        fd = dn[0] if len(dn) else 10 ** 9
        if fu == fd == 10 ** 9:
            continue
        # 42% of sessions OPEN already beyond the prior day's level, by a
        # median of 26 points. A fill at the level on those days is impossible
        # -- price was never there during RTH -- and crediting it books the
        # overnight gap as instant profit, which is what turned this into a
        # 27-points-a-day "strategy" on the first run.
        if fu < fd:
            pb.append(c[b] - max(pdh[i - 1], o[a + fu]))
        else:
            pb.append(min(pdl[i - 1], o[a + fd]) - c[b])
        pdays.append(u[i])
    report("pdh_pdl", np.array(pb), np.array(pdays), out)

    # ---- the one that matters: does it hold out of sample? ---------------
    print("\n=== discovery / validation on whatever cleared zero ===")
    yr_of = (u // 10000)
    for name in out:
        if out[name]["lo"] <= 0:
            continue
        if name == "overnight":
            pnl = c[io[1:]] - c[ic[:-1]]; dd = u[1:]
        elif name == "rth_long":
            pnl = c[ic] - c[io]; dd = u
        else:
            continue
        y = dd // 10000
        d_, v_ = y < SPLIT, y >= SPLIT
        print("  %-12s discovery %+.3f net (n=%s)   validation %+.3f net (n=%s)"
              % (name, (pnl[d_] - COST).mean(), "{:,}".format(int(d_.sum())),
                 (pnl[v_] - COST).mean(), "{:,}".format(int(v_.sum()))))
        out[name]["disc"] = float((pnl[d_] - COST).mean())
        out[name]["val"] = float((pnl[v_] - COST).mean())

    json.dump(out, open(os.path.join(HERE, "benchmark.json"), "w"), indent=1)
    print("\nwrote benchmark.json")


if __name__ == "__main__":
    main()
