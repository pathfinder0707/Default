"""Session slicing and shared helpers for the intraday PO3 study."""
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BARS = os.path.join(HERE, "..", "ranges", "bars.npz")

PO3 = [27, 81, 243, 729, 2187, 6561]

# NY local clock. The feed is America/New_York with DST (verified in prep.py).
WINDOWS = {
    "RTH":      (930, 1600),    # 09:30-16:00 regular trading hours
    "NYAM":     (930, 1130),    # the AM killzone
    "NYPM":     (1330, 1600),
    "LONDON":   (300, 530),
    "ASIA":     (2000, 2359),
}


def load():
    b = np.load(BARS)
    d = {k: b[k] for k in ("ts", "o", "h", "l", "c", "date", "yr", "hh", "mm")}
    d["tod"] = d["hh"] * 100 + d["mm"]
    return d


def session_slices(bars, window="RTH"):
    """Contiguous index ranges, one per trading day, inside the window.

    Returns (starts, stops, dates) with stops exclusive. Days with too few
    bars (holidays, half sessions) are dropped.
    """
    lo, hi = WINDOWS[window]
    sel = (bars["tod"] >= lo) & (bars["tod"] < hi)
    idx = np.flatnonzero(sel)
    if len(idx) == 0:
        return np.array([], int), np.array([], int), np.array([], int)

    date = bars["date"][idx]
    brk = np.flatnonzero(np.diff(date) != 0) + 1
    starts = np.r_[0, brk]
    stops = np.r_[brk, len(idx)]

    expect = (hi // 100 * 60 + hi % 100) - (lo // 100 * 60 + lo % 100)
    keep = (stops - starts) >= expect * 0.6
    return idx[starts[keep]], idx[stops[keep] - 1] + 1, date[starts[keep]]


def r_grid(n=48, lo=27.0, hi=6561.0):
    """Log-spaced R values with the exact powers of three forced in.

    The point of the continuum is to see whether 3^n stands out from its
    neighbours or whether the statistic just varies smoothly with size.
    """
    g = np.geomspace(lo, hi, n)
    g = np.unique(np.round(np.concatenate([g, np.array(PO3, float)]), 2))
    return g


def is_po3(R, tol=1e-6):
    return any(abs(R - p) < tol for p in PO3)


def first_true(mask):
    """Index of the first True, or -1."""
    j = np.argmax(mask)
    return int(j) if mask[j] else -1
