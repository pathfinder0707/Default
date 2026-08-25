"""Does VOLUME say when a level holds? The one input that is not price.

Every conditional test in this repo has asked the "when" question of price
alone -- zone, session, volatility, break depth, sweep, confluence. All of it
derived from OHLC, which means all of it is a rearrangement of the same
information. Volume was in the source data and was dropped when the working
dataset was built. That is a real gap and it is the obvious place for the
answer to be hiding: it is what separates a sweep that gets absorbed from one
that runs.

Conditions, all computable at the moment the touch bar closes:

  rvol        the touch bar's volume against the trailing 60-bar median
  approach    volume of the 15 bars into the level, same normalisation
  climax      is the touch bar the highest-volume bar of the last 60
  dryup       ... or one of the lowest
  expansion   is volume rising or falling into the level
  vwap_side   is the level above or below the session's volume-weighted price

Scored on the touch test from baserate.py: price arrives at a Goldbach level
from at least 1 ATR away, and either rejects or is pushed through. Split
discovery 2010-2018 / validation 2019-2026, because a condition search is how
false positives are manufactured and the only defence is data that had no vote
in the selection.
"""
import json
import os

import numpy as np

import gbr
import baserate as br
from edge import atr

HERE = os.path.dirname(os.path.abspath(__file__))
SPLIT = 2019
LOOK = 60


def roll_med(x, w):
    """Trailing median, approximated by a trailing mean of ranks-free values.

    A true rolling median over 4.8M bars is slow and the normalisation only
    needs to be monotone and causal, so a trailing mean of log volume is used
    and exponentiated back -- a geometric mean, which is far more robust to
    volume's heavy right tail than an arithmetic one.
    """
    lg = np.log(np.maximum(x, 1.0))
    cs = np.concatenate([[0.0], np.cumsum(lg)])
    idx = np.arange(len(x))
    lo = np.maximum(idx - w, 0)
    mean = (cs[idx] - cs[lo]) / np.maximum(idx - lo, 1)
    return np.exp(mean)


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    h, l, c, v = (np.asarray(npz[k]) for k in ("h", "l", "c", "v"))
    yr, date = np.asarray(npz["yr"]), np.asarray(npz["date"])
    a = atr(h, l, c)
    n = len(c)

    cmin, cmax = c.copy(), c.copy()
    for off in range(1, LOOK):
        cmin[off:] = np.minimum(cmin[off:], c[:-off])
        cmax[off:] = np.maximum(cmax[off:], c[:-off])
    cmin = np.concatenate([[c[0]], cmin[:-1]])
    cmax = np.concatenate([[c[0]], cmax[:-1]])

    # ---- volume features, all causal ------------------------------------
    base = roll_med(v, LOOK)                       # trailing geometric mean
    rvol = v / np.maximum(base, 1.0)
    cs = np.concatenate([[0.0], np.cumsum(v)])
    idx = np.arange(n)
    lo15 = np.maximum(idx - 15, 0)
    appr = (cs[idx + 1] - cs[lo15]) / np.maximum((idx + 1 - lo15), 1)
    appr = appr / np.maximum(base, 1.0)
    rmax = v.copy()
    for off in range(1, LOOK):
        rmax[off:] = np.maximum(rmax[off:], v[:-off])
    climax = v >= rmax                              # highest of the last 60
    prev15 = roll_med(v, 15)
    expansion = prev15 / np.maximum(base, 1.0)

    # session VWAP, reset at 18:00 New York
    sess = np.asarray(npz["sess"])
    tp = (h + l + c) / 3.0
    order = np.argsort(sess, kind="stable")
    _, first = np.unique(sess[order], return_index=True)
    vw = np.empty(n)
    starts = np.append(first, len(order))
    for i in range(len(first)):
        s = order[starts[i]:starts[i + 1]]
        pv = np.cumsum(tp[s] * v[s])
        vv = np.cumsum(v[s])
        vw[s] = pv / np.maximum(vv, 1.0)

    # ---- collect touches -------------------------------------------------
    R = 81.0
    I, L, RES = [], [], []
    for pct in gbr.LEVELS:
        o = R * pct / 100.0
        for i2, Lk, up in br.approaches(h, l, c, a, cmin, cmax, o, R, n):
            r = br.resolve_touch(h, l, i2, Lk, a[i2], up, n)
            k = r != 0
            I.append(i2[k]); L.append(Lk[k]); RES.append(r[k])
    I = np.concatenate(I); L = np.concatenate(L); RES = np.concatenate(RES)
    rej = (RES == 1)
    print("%s resolved touches, overall reject %.4f\n"
          % ("{:,}".format(len(I)), rej.mean()))

    rv, ap, cx, ex = rvol[I], appr[I], climax[I], expansion[I]
    above_vwap = L > vw[I]
    y = yr[I]
    disc, val = y < SPLIT, y >= SPLIT

    qr = np.percentile(rv, [20, 40, 60, 80])
    qa = np.percentile(ap, [25, 50, 75])
    qe = np.percentile(ex, [25, 50, 75])

    CUTS = {
        "rvol very low (<p20)": rv <= qr[0],
        "rvol low (p20-40)": (rv > qr[0]) & (rv <= qr[1]),
        "rvol mid (p40-60)": (rv > qr[1]) & (rv <= qr[2]),
        "rvol high (p60-80)": (rv > qr[2]) & (rv <= qr[3]),
        "rvol very high (>p80)": rv > qr[3],
        "approach quiet (<p25)": ap <= qa[0],
        "approach heavy (>p75)": ap > qa[2],
        "climax bar": cx,
        "no climax": ~cx,
        "volume contracting": ex <= qe[0],
        "volume expanding": ex > qe[2],
        "level above VWAP": above_vwap,
        "level below VWAP": ~above_vwap,
        "climax + heavy approach": cx & (ap > qa[2]),
        "dryup + quiet approach": (rv <= qr[0]) & (ap <= qa[0]),
        "expanding + high rvol": (ex > qe[2]) & (rv > qr[3]),
    }

    print("=== does volume say when a level holds? ===")
    print("  %-26s %9s %8s   %9s %8s %8s"
          % ("condition", "n disc", "reject", "n val", "reject", "delta"))
    base_d = float(rej[disc].mean())
    base_v = float(rej[val].mean())
    print("  %-26s %9s %8.4f   %9s %8.4f %8s"
          % ("ALL", "{:,}".format(int(disc.sum())), base_d,
             "{:,}".format(int(val.sum())), base_v, ""))
    rows = []
    for nm, m in CUTS.items():
        md, mv = m & disc, m & val
        if md.sum() < 500 or mv.sum() < 500:
            continue
        pd_, pv_ = float(rej[md].mean()), float(rej[mv].mean())
        rows.append({"cond": nm, "n_disc": int(md.sum()), "disc": pd_,
                     "n_val": int(mv.sum()), "val": pv_,
                     "lift_disc": pd_ - base_d, "lift_val": pv_ - base_v})
        print("  %-26s %9s %8.4f   %9s %8.4f %+7.2fpp"
              % (nm, "{:,}".format(int(md.sum())), pd_,
                 "{:,}".format(int(mv.sum())), pv_, (pv_ - base_v) * 100))

    print("\n=== does the discovery lift survive? ===")
    ld = np.array([r["lift_disc"] for r in rows])
    lv_ = np.array([r["lift_val"] for r in rows])
    print("  best lift in discovery: %+.2fpp (%s)"
          % (ld.max() * 100, rows[int(ld.argmax())]["cond"]))
    print("  ... its validation lift: %+.2fpp"
          % (rows[int(ld.argmax())]["lift_val"] * 100))
    print("  correlation, discovery lift vs validation lift: %+.3f"
          % np.corrcoef(ld, lv_)[0, 1])
    print("  conditions lifting >2pp in BOTH halves: %d of %d"
          % (int(((ld > 0.02) & (lv_ > 0.02)).sum()), len(rows)))

    json.dump(rows, open(os.path.join(HERE, "volume.json"), "w"), indent=1)
    print("\nwrote volume.json")


if __name__ == "__main__":
    main()
