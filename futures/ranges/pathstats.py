"""Day-clustered intervals for the path numbers, and the per-year breakdown.

The path events overlap heavily -- one trending afternoon produces dozens of
correlated breaks -- so a binomial interval on 68,000 events would be far too
tight to believe. Everything here resamples whole trading days instead, which
keeps the within-day correlation intact.

Also emits the per-year series, because a base rate a trader is going to plan
around should be shown to be stable rather than asserted to be.
"""
import json
import os

import numpy as np

import paths as P
import firsttouch as FT

HERE = os.path.dirname(os.path.abspath(__file__))
NBOOT = 2000


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    c, h, l = (np.asarray(npz[k]) for k in ("c", "h", "l"))
    date, yr = np.asarray(npz["date"]), np.asarray(npz["yr"])
    trail = P.trail_closes(c, 60)
    n = len(c)
    rng = np.random.default_rng(23)

    out = {}
    for R, H in ((81.0, 480), (243.0, 1440), (729.0, 2880)):
        st, off = P.states(c, h, l, R, 0.0, trail[0], trail[1])
        out[str(int(R))] = {}
        for name, (idx, lv) in st.items():
            if len(idx) < 500:
                continue
            up = name.endswith("_up")
            travel = up if name.startswith("break") else not up
            keep = idx + 1 < n
            i2, lv2 = idx[keep], lv[keep]
            tu, td = FT.first_touch(h, l, i2, lv2, off, R, travel, H, n)

            d = date[i2]
            u, day = np.unique(d, return_inverse=True)
            nd = len(u)
            pick = rng.integers(0, nd, size=(NBOOT, nd))
            yy = yr[i2]

            ks = {}
            for k in range(1, FT.KMAX + 1):
                a, b = tu[:, k], td[:, k]
                live = (a != FT.BIG) | (b != FT.BIG)
                if live.sum() < 300:
                    continue
                win = (a[live] < b[live]).astype(float)
                dd = day[live]
                s = np.bincount(dd, weights=win, minlength=nd)
                cnt = np.bincount(dd, minlength=nd).astype(float)
                bs = s[pick].sum(1) / np.maximum(cnt[pick].sum(1), 1)
                lo, hi = np.percentile(bs, [2.5, 97.5])
                per_year = {}
                for y in np.unique(yy[live]):
                    m = yy[live] == y
                    if m.sum() >= 200:
                        per_year[int(y)] = float(win[m].mean())
                ks[str(k)] = {"n": int(live.sum()), "days": int(nd),
                              "p": float(win.mean()),
                              "lo": float(lo), "hi": float(hi),
                              "per_year": per_year}
            out[str(int(R))][name] = ks
            print("R=%-5d %-12s k=1 %.4f  [%.4f, %.4f]  %s days, %s events"
                  % (R, name, ks["1"]["p"], ks["1"]["lo"], ks["1"]["hi"],
                     "{:,}".format(ks["1"]["days"]), "{:,}".format(ks["1"]["n"])))

    json.dump(out, open(os.path.join(HERE, "pathstats.json"), "w"), indent=1)
    print("\nwrote pathstats.json")


if __name__ == "__main__":
    main()
