"""Which level does price reach FIRST? The actual path question.

The reach map in paths.py shows that after an upward break price touches the
next level up 92.5% of the time -- and the next level DOWN 86.8% of the time.
Over any horizon long enough to be useful it does both. So an unconditional
reach probability cannot answer "if this breaks, price goes there": the honest
version is which destination arrives first.

That is what this measures. From each state, first-passage times are computed
to every level in both directions, and the reported quantity is

    P(reach k levels in the direction of travel  BEFORE  k levels against)

counted in LEVELS rather than points, so the two destinations are the same
number of steps away on the lattice's own terms. This is not a stop and a
target dressed up -- nothing is risked and nothing is exited. It is an ordering
statistic over destinations, which is the thing the framework actually claims.

A coin flip is roughly the right null intuition, but only roughly: the levels
are unevenly spaced, so k levels up and k levels down are not equidistant in
points from a given start, and the break itself leaves price slightly past the
level. Both are why the shifted-lattice column is the one that matters.
"""
import json
import os

import numpy as np

import paths as P

HERE = os.path.dirname(os.path.abspath(__file__))
NPHASE = 8
KMAX = 6
BIG = np.int32(10 ** 6)


def first_touch(h, l, idx, lv, off, R, up, horizon, n):
    """First bar at which each +/- k level is touched. BIG if never."""
    m = len(idx)
    tu = np.full((m, KMAX + 1), BIG, np.int32)   # k levels along the travel
    td = np.full((m, KMAX + 1), BIG, np.int32)   # k levels against it
    pu = [P.level_price(R, off, lv + (k if up else -k)) for k in range(KMAX + 1)]
    pd = [P.level_price(R, off, lv - (k if up else -k)) for k in range(KMAX + 1)]
    for w in range(1, horizon + 1):
        j = np.clip(idx + w, 0, n - 1)
        hi, lo = h[j], l[j]
        for k in range(1, KMAX + 1):
            a = (hi >= pu[k]) if up else (lo <= pu[k])
            b = (lo <= pd[k]) if up else (hi >= pd[k])
            tu[a & (tu[:, k] == BIG), k] = w
            td[b & (td[:, k] == BIG), k] = w
        if (tu[:, KMAX] != BIG).all() and (td[:, KMAX] != BIG).all():
            break
    return tu, td


def measure(c, h, l, R, H, phase, trail):
    n = len(c)
    st, off = P.states(c, h, l, R, phase, trail[0], trail[1])
    out = {}
    for name, (idx, lv) in st.items():
        if len(idx) < 500:
            continue
        up = name.endswith("_up")
        travel_up = up if name.startswith("break") else not up
        keep = idx + 1 < n
        tu, td = first_touch(h, l, idx[keep], lv[keep], off, R, travel_up, H, n)
        row = {}
        for k in range(1, KMAX + 1):
            a, b = tu[:, k], td[:, k]
            live = (a != BIG) | (b != BIG)
            if live.sum() < 300:
                continue
            row[k] = {"n": int(live.sum()),
                      "p_first": float((a[live] < b[live]).mean()),
                      "resolved": float(live.mean())}
        out[name] = {"n": int(keep.sum()), "k": row}
    return out


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    c, h, l = (np.asarray(npz[k]) for k in ("c", "h", "l"))
    trail = P.trail_closes(c, 60)

    out = {}
    for R, H in ((81.0, 480), (243.0, 1440)):
        print("\n" + "=" * 78)
        print("R=%d   horizon %d bars" % (R, H))
        print("=" * 78)
        true = measure(c, h, l, R, H, 0.0, trail)
        nulls = [measure(c, h, l, R, H, j * 100.0 / NPHASE, trail)
                 for j in range(1, NPHASE)]
        out[str(int(R))] = {}
        for name in ("break_up", "break_dn", "reject_up", "reject_dn"):
            if name not in true:
                continue
            print("\n  %s  (%s events)"
                  % (P.LABEL[name], "{:,}".format(true[name]["n"])))
            print("     %-22s %9s %9s %9s %8s"
                  % ("k levels on vs back", "n", "P(on first)", "shifted", "z"))
            rows = {}
            for k in sorted(true[name]["k"]):
                p = true[name]["k"][k]["p_first"]
                arr = np.array([m[name]["k"][k]["p_first"] for m in nulls
                                if name in m and k in m[name]["k"]])
                sd = arr.std(ddof=1) if len(arr) > 1 else 0.0
                z = (p - arr.mean()) / sd if sd > 0 else 0.0
                rows[k] = {"n": true[name]["k"][k]["n"], "p": p,
                           "resolved": true[name]["k"][k]["resolved"],
                           "null": float(arr.mean()), "z": float(z)}
                print("     %-22s %9s %11.4f %9.4f %+8.2f"
                      % ("k = %d" % k, "{:,}".format(rows[k]["n"]), p,
                         arr.mean(), z))
            out[str(int(R))][name] = rows

    json.dump(out, open(os.path.join(HERE, "firsttouch.json"), "w"), indent=1)
    print("\nwrote firsttouch.json")


if __name__ == "__main__":
    main()
