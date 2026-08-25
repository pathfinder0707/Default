"""Do Goldbach levels FLIP POLARITY? Broken resistance holding as support.

This is the mechanism the source document actually describes, and the one every
earlier test in this repo missed. The trade plans are explicit that the FIRST
touch is not the trade:

  FLOW CONTINUATION -- "When price touches the flow layer ... you don't buy at
  this level, but anticipate a rejection. When price indeed moves THROUGH the
  flow layer, you still don't buy ... They will first retrace price, BACK INTO
  the flow layer. When price retraces, THIS is where you buy."

  EINSTEIN -- price gaps up through [11-89] to [17-83], runs to the flow middle
  [29-71], "there price will retrace, back towards the zone between [11-89] and
  [17-83]. You enter the trade at level [17-83]."

And [17-83] is named the Goldbach INVERSION Point. So the claim is role
reversal: a level rejects price, price breaks it, and the retest from the other
side holds. Every previous test here measured first-touch rejection, which the
document says explicitly not to trade.

Event definition, deliberately strict so that "break and retest" cannot be
satisfied by ordinary oscillation around a line:

  1. BREAK      price crosses level L upward (level index increments)
  2. EXCURSION  price must then travel at least BREAK_MIN x ATR beyond L --
                a genuine displacement through the level, not a wobble
  3. RETEST     price returns to touch L, within the retest window
  4. HOLD       from the retest, does price reach L + X before L - X?

Mirrored for downward breaks (support becoming resistance). Barriers are
ATR-scaled so the sample's 18-fold volatility change does not distort anything.

Scored against 20 shifted lattice phases running the identical procedure, and
validated on a positive control in which polarity flip is injected.
"""
import json
import os
import sys

import numpy as np

import gbr

HERE = os.path.dirname(os.path.abspath(__file__))
NPHASE = 20
BREAK_MIN = 1.0        # ATR multiples price must travel beyond L to count as broken
RETEST_MAX = 240       # bars allowed for the retest to occur
OUT_HORIZON = 120      # bars to resolve the post-retest outcome
BARRIER = 0.5          # ATR multiples for the hold/fail barriers
DEDUP = 120


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


def dedup(idx, gap):
    if len(idx) == 0:
        return idx
    keep = [idx[0]]
    for i in idx[1:]:
        if i - keep[-1] >= gap:
            keep.append(i)
    return np.asarray(keep)


def find_retests(h, l, brk_idx, L, atr_at, up, n):
    """From each break, require an excursion then find the first return to L.

    Returns the retest bar index, or -1 where no qualifying retest occurred.
    """
    m = len(brk_idx)
    gone = np.zeros(m, bool)          # excursion achieved, on EARLIER bars only
    retest = np.full(m, -1, np.int64)
    thresh = L + BREAK_MIN * atr_at if up else L - BREAK_MIN * atr_at
    for w in range(1, RETEST_MAX + 1):
        j = np.clip(brk_idx + w, 0, n - 1)
        back = (l[j] <= L) if up else (h[j] >= L)
        hit = gone & back & (retest < 0)
        retest[hit] = j[hit]
        if (retest >= 0).all():
            break
        # update the excursion flag AFTER testing for the return. Updating it
        # first lets one wide bar be break, excursion and retest at once, which
        # is not a tradeable sequence: the excursion filter is only known once
        # that bar has closed, by which time no order could have been resting
        # at the level. See edge.py -- this artifact alone was worth +11 points
        # of hold rate.
        still = retest < 0
        gone |= still & ((h[j] >= thresh) if up else (l[j] <= thresh))
    return retest


def resolve_hold(h, l, idx, L, atr_at, up, n):
    """After the retest: does the level hold? +1 hold, -1 fail, 0 unresolved.

    'Hold' means price moves BACK in the break direction -- broken resistance
    pushing price up again -- before giving up an equal distance the other way.
    """
    tgt = L + BARRIER * atr_at if up else L - BARRIER * atr_at
    stp = L - BARRIER * atr_at if up else L + BARRIER * atr_at
    out = np.zeros(len(idx), np.int8)

    # The retest bar itself is scored asymmetrically, on purpose. The position
    # is taken at L because that bar traded back to L, so the part of the bar
    # on the far side of L happened before the entry and cannot be counted as
    # profit, while the part beyond L is heat taken after it.
    over = (L - l[idx]) if up else (h[idx] - L)
    out[over >= BARRIER * atr_at] = -1
    live = out == 0

    for w in range(1, OUT_HORIZON + 1):
        j = np.clip(idx + w, 0, n - 1)
        ht = (h[j] >= tgt) if up else (l[j] <= tgt)
        hs = (l[j] <= stp) if up else (h[j] >= stp)
        s_now = live & hs
        t_now = live & ht & ~hs        # a bar containing both counts as a fail
        out[s_now] = -1
        out[t_now] = 1
        live &= ~(s_now | t_now)
        if not live.any():
            break
    return out


def measure(bars, R, phase):
    """Polarity-flip hold rate across all 20 levels at this lattice phase."""
    h, l, c, a = bars["h"], bars["l"], bars["c"], bars["atr"]
    n = len(c)
    held = fails = 0
    for pct in gbr.LEVELS:
        off = R * (pct + phase) / 100.0
        li = np.floor((c - off) / R)
        d = np.diff(li)
        for up in (True, False):
            cross = np.flatnonzero(d > 0) + 1 if up else np.flatnonzero(d < 0) + 1
            cross = cross[(cross > 20) & (cross + RETEST_MAX + OUT_HORIZON < n)]
            cross = dedup(cross, DEDUP)
            if len(cross) == 0:
                continue
            L = off + R * (li[cross] if up else li[cross] + 1)
            at = a[cross]
            rt = find_retests(h, l, cross, L, at, up, n)
            ok = rt >= 0
            if not ok.any():
                continue
            res = resolve_hold(h, l, rt[ok], L[ok], a[rt[ok]], up, n)
            held += int((res == 1).sum())
            fails += int((res == -1).sum())
    tot = held + fails
    return {"n": tot, "hold_rate": held / tot if tot else float("nan")}


def run(bars, R, label=""):
    true = measure(bars, R, 0.0)
    nulls = np.array([measure(bars, R, j * 100.0 / NPHASE)["hold_rate"]
                      for j in range(1, NPHASE)])
    nulls = nulls[np.isfinite(nulls)]
    sd = nulls.std(ddof=1)
    z = (true["hold_rate"] - nulls.mean()) / sd if sd > 0 else 0.0
    rank = int((nulls >= true["hold_rate"]).sum() + 1)
    print("  %-10s R=%-5d  retests %7s  hold %.4f   null %.4f  sd %.4f   z=%+.2f  rank %d/%d"
          % (label, R, "{:,}".format(true["n"]), true["hold_rate"],
             nulls.mean(), sd, z, rank, len(nulls) + 1))
    return {"R": R, "label": label, "n": true["n"], "hold_rate": true["hold_rate"],
            "null_mean": float(nulls.mean()), "null_sd": float(sd),
            "z": float(z), "rank": rank}


def load(path=None):
    npz = np.load(path or os.path.join(HERE, "bars.npz"))
    b = {k: np.asarray(npz[k]) for k in ("h", "l", "c", "yr")}
    b["atr"] = atr(b["h"], b["l"], b["c"])
    return b


def main():
    bars = load()
    print("=== polarity flip: does broken resistance hold as support? ===")
    print("    hold means price resumes the break direction by %.1f ATR before"
          % BARRIER)
    print("    losing the same the other way. 0.500 is no polarity effect.\n")
    out_path = os.path.join(HERE, "polarity.json")
    res = []

    def save():
        with open(out_path, "w") as fh:
            json.dump(res, fh, indent=1)

    for R in (81, 243, 729, 2187):
        res.append(run(bars, R, "all"))
        save()                     # incremental: this container recycles

    print("\n=== by era ===")
    for lab, lo, hi in (("2010-2014", 2010, 2014), ("2015-2019", 2015, 2019),
                        ("2020-2026", 2020, 2026)):
        sel = (bars["yr"] >= lo) & (bars["yr"] <= hi)
        sub = {k: bars[k][sel] for k in ("h", "l", "c", "atr", "yr")}
        for R in (243, 729):
            res.append(run(sub, R, lab))
            save()

    save()
    print("\nwrote polarity.json")


if __name__ == "__main__":
    main()
