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

# The CME session opens at 18:00 New York and the dead hour is 17:00 -- verified
# against this feed, where 17:00 holds 37 bars in four years and 18:00 holds
# ~59,000. A daily candle therefore runs 18:00 -> 17:00 the next day.
SESSION_OPEN_HOUR = 18

# The counts TDT treats as meaningful. 7 and 13 carry the two model readings;
# 21 is the count the Model #3 slide explicitly warns off.
KEY_COUNTS = (7, 13, 21)


def load(path=BARS, from_year=None, to_year=None):
    """Load bars.npz into a dict of arrays, optionally clipped by year.

    Raises a readable error rather than a numpy one when the data is absent --
    the feed is gitignored, so a fresh checkout has no bars until you run
    ../futures/build_npz.py.

    from_year matters more than it looks. The NQ feed's session coverage ramps
    from under two hours a day in 2010 to a full 23 by 2022, so a daily candle
    from 2011 is built on a couple of hours of trade and a 2023 one on the
    whole session. Those are not the same object, and counting across the join
    silently mixes them. Anything intraday is meaningless before 2016.
    """
    if not os.path.exists(path):
        raise SystemExit(
            "no bars at %s\n"
            "  the 1-minute feed is gitignored; build it first:\n"
            "    python futures/build_npz.py   (writes futures/bars.npz)\n"
            "    ln -s ../futures/bars.npz tdt/bars.npz" % path)
    b = np.load(path)
    keys = ["ts", "o", "h", "l", "c", "date", "yr", "hh", "mm"]
    if "sess" in b.files:
        keys.append("sess")
    if "v" in b.files:
        keys.append("v")
    d = {k: b[k] for k in keys}

    if from_year is not None or to_year is not None:
        sel = np.ones(len(d["yr"]), bool)
        if from_year is not None:
            sel &= d["yr"] >= int(from_year)
        if to_year is not None:
            sel &= d["yr"] <= int(to_year)
        d = {k: v[sel] for k, v in d.items()}
        if not len(d["ts"]):
            raise SystemExit("no bars left after the year filter")

    d["tod"] = d["hh"] * 100 + d["mm"]
    return d


# ------------------------------------------------------------------ resample
def session_index(bars):
    """A counter that increments once per CME session open, one id per session.

    Counts transitions into the 18:00 hour rather than doing calendar
    arithmetic, so a session runs unbroken from 18:00 to 17:00 the next day and
    the Friday-to-Sunday weekend gap costs exactly one increment. Requires
    time-sorted bars, which bars.npz guarantees.
    """
    hh = bars["hh"].astype(np.int64)
    open_ = hh >= SESSION_OPEN_HOUR
    opened = np.zeros(len(hh), bool)
    opened[0] = open_[0]
    opened[1:] = open_[1:] & ~open_[:-1]
    return np.cumsum(opened).astype(np.int64)


def _bucket(bars, tf):
    """Integer bucket id per 1-min bar, one distinct id per output candle.

    D1 buckets on the CME trading session, not the calendar date. The feed's
    dead hour is 17:00 NY and the session opens at 18:00, so a daily candle
    runs 18:00 -> 17:00 the next day. Bucketing on the calendar date instead
    would cut every daily candle in half at midnight, straight through the
    middle of the overnight session -- and since a count is a sequence of
    candles, that does not merely move the boundaries, it changes every count.

    Note that build_npz.py's own `sess` field cannot be used for this: it tags
    the evening half of a session (hh>=18) and the following morning half with
    two different ids, so bucketing on it splits every session in two. See
    session_index below.

    Intraday timeframes bucket on elapsed minutes within the session for the
    same reason, so an H1 candle never straddles the break.
    """
    sess = session_index(bars)
    if tf == "D1":
        return sess
    step = TF_MINUTES[tf]
    mins = bars["hh"].astype(np.int64) * 60 + bars["mm"].astype(np.int64)
    # minutes since the session opened, so the grid starts at 18:00 not 00:00
    since = (mins - SESSION_OPEN_HOUR * 60) % (24 * 60)
    return sess * 10000 + since // step


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


def exec_map(raw, count_tf, exec_tf):
    """Bridge a counting timeframe to a finer execution timeframe.

    Returns {"bars": <exec series>, "xmap": <array>} where xmap[i] is the index
    of the first execution candle that opens at or after counting candle i.
    Both series are resampled from the same 1-minute feed, so the mapping is
    exact rather than interpolated.
    """
    if TF_MINUTES[exec_tf] > TF_MINUTES[count_tf]:
        raise ValueError("execution timeframe %s is coarser than the counting "
                         "timeframe %s" % (exec_tf, count_tf))
    cnt = resample(raw, count_tf)
    ex = resample(raw, exec_tf)
    # both `src` arrays index the same 1-min feed and are sorted ascending
    xmap = np.searchsorted(ex["src"], cnt["src"], side="left")
    return {"bars": ex, "xmap": np.clip(xmap, 0, len(ex["src"]) - 1)}
