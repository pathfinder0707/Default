"""Shared plumbing for the TDT study: bar loading, resampling, swings, stats.

The source material (Inner Circle Morpheus, 'Time Dilation Theory') counts
candles on a chosen timeframe, so everything here exists to turn the 1-minute
bars.npz feed into a clean D1/H4/H1/M15 series and back.

bars.npz is the schema written by ../futures/build_npz.py: America/New_York
local time, DST-aware, with the maintenance break already in the gaps.
"""
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BARS = os.path.join(HERE, "bars.npz")

# Minutes per bar for each timeframe label the study uses.
TF_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "M30": 30,
              "H1": 60, "H4": 240, "D1": 1440}

# The counts TDT treats as meaningful. 7 and 13 carry the two model readings;
# 21 is the count the Model #3 slide explicitly warns off.
KEY_COUNTS = (7, 13, 21)


def load(path=BARS):
    """Load bars.npz into a dict of arrays.

    Raises a readable error rather than a numpy one when the data is absent --
    the feed is gitignored, so a fresh checkout has no bars until you run
    ../futures/build_npz.py.
    """
    if not os.path.exists(path):
        raise SystemExit(
            "no bars at %s\n"
            "  the 1-minute feed is gitignored; build it first:\n"
            "    python futures/build_npz.py   (writes futures/bars.npz)\n"
            "    ln -s ../futures/bars.npz tdt/bars.npz" % path)
    b = np.load(path)
    d = {k: b[k] for k in ("ts", "o", "h", "l", "c", "date", "yr", "hh", "mm")}
    if "v" in b.files:
        d["v"] = b["v"]
    d["tod"] = d["hh"] * 100 + d["mm"]
    return d


# ------------------------------------------------------------------ resample
def _bucket(bars, tf):
    """Integer bucket id per 1-min bar, one distinct id per output candle.

    D1 buckets on the trading date. Intraday timeframes bucket on elapsed
    minutes within the date, so an H1 candle is 09:00-09:59 local and never
    straddles the maintenance break.
    """
    if tf == "D1":
        return bars["date"].astype(np.int64)
    step = TF_MINUTES[tf]
    mins = bars["hh"].astype(np.int64) * 60 + bars["mm"].astype(np.int64)
    return bars["date"].astype(np.int64) * 10000 + mins // step


def resample(bars, tf):
    """Aggregate 1-min bars up to timeframe tf.

    Returns a dict with o/h/l/c/ts plus `src` -- the index of the first 1-min
    bar in each output candle, which is what lets a D1 count hand off to an H1
    execution leg without re-deriving the alignment.
    """
    if tf not in TF_MINUTES:
        raise ValueError("unknown timeframe %r" % tf)
    if tf == "M1":
        out = {k: bars[k] for k in ("ts", "o", "h", "l", "c")}
        out["src"] = np.arange(len(bars["ts"]))
        out["n"] = np.ones(len(bars["ts"]), np.int64)
        return out

    key = _bucket(bars, tf)
    # bars.npz is sorted by time, so bucket changes mark candle boundaries.
    starts = np.r_[0, np.flatnonzero(np.diff(key) != 0) + 1]
    stops = np.r_[starts[1:], len(key)]

    o = bars["o"][starts]
    c = bars["c"][stops - 1]
    h = np.maximum.reduceat(bars["h"], starts)
    l = np.minimum.reduceat(bars["l"], starts)
    return {"ts": bars["ts"][starts], "o": o, "h": h, "l": l, "c": c,
            "src": starts, "n": stops - starts}


# -------------------------------------------------------------------- stats
def zscore(observed, null_samples):
    """z of an observed statistic against a null sample distribution."""
    null_samples = np.asarray(null_samples, float)
    sd = null_samples.std(ddof=1)
    if sd == 0 or not np.isfinite(sd):
        return float("nan")
    return float((observed - null_samples.mean()) / sd)


def binom_z(hits, n, p):
    """z of a hit count against a binomial expectation."""
    if n == 0 or p <= 0 or p >= 1:
        return float("nan")
    return float((hits - n * p) / np.sqrt(n * p * (1 - p)))


def rank_of(observed, null_samples, higher_is_better=True):
    """1-based rank of observed among the nulls; 1 means it beat them all."""
    null_samples = np.asarray(null_samples, float)
    if higher_is_better:
        return int((null_samples >= observed).sum() + 1)
    return int((null_samples <= observed).sum() + 1)
