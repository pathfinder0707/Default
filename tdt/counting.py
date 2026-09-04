"""TDT candle counting: classic, contraction-by-wick, contraction-by-body.

Read off the 'Advanced Counting Examples' slides (USDCAD D1, EURUSD M1). A
count starts at an origin candle labelled 1 and runs forward:

  classic  every candle takes the next number.

  wick     a candle takes the next number only if it expands the leg -- its
           high (on an up leg) exceeds the high of the last numbered candle.
           One that does not is marked `x` and takes no number.

  body     the same test on the body extreme, max(o,c) up / min(o,c) down,
           rather than the wick.

That is the whole of the mechanic the slides show, and it is why the two
panels disagree: on the EURUSD M1 example the candle classic counting calls 13
is contraction-by-wick's 12, because one candle in between contracted and was
skipped. Contraction counting therefore always reaches a given number at or
later than classic does, never earlier.

The direction of a leg follows its origin: a swing low opens an up leg, a
swing high a down leg.
"""
import numpy as np

import tdtcore

MODES = ("classic", "wick", "body")

UP, DOWN = 1, -1


def _rail(bars, mode, direction):
    """The per-candle price the expansion test compares, given mode/direction.

    Up legs expand upward, so they read the top of the candle -- the high on a
    wick count, the body top on a body count. Down legs read the bottom.
    """
    if mode == "wick":
        return bars["h"] if direction == UP else bars["l"]
    if mode == "body":
        top = np.maximum(bars["o"], bars["c"])
        bot = np.minimum(bars["o"], bars["c"])
        return top if direction == UP else bot
    raise ValueError("mode %r has no rail" % mode)


class Count(object):
    """One count: which candles took numbers, which contracted, where 7/13/21 fell.

    idx[k] is the bar index that took number k+1, so idx[6] is the 7 candle.
    skipped[k] is how many candles were marked x before number k+1 was taken;
    it is all zeros for a classic count.
    """

    def __init__(self, origin, direction, mode, idx, skipped, x_idx):
        self.origin = int(origin)
        self.direction = int(direction)
        self.mode = mode
        self.idx = np.asarray(idx, np.int64)
        self.skipped = np.asarray(skipped, np.int64)
        self.x_idx = np.asarray(x_idx, np.int64)

    def __len__(self):
        return len(self.idx)

    def bar_of(self, n):
        """Bar index that took number n, or -1 if the count never reached n."""
        return int(self.idx[n - 1]) if 1 <= n <= len(self.idx) else -1

    def reached(self, n):
        return len(self.idx) >= n

    def span(self, n):
        """Candles consumed from the origin to reach number n (-1 if unreached)."""
        b = self.bar_of(n)
        return b - self.origin if b >= 0 else -1

    def labels(self):
        """(bar_index, label) pairs in bar order -- '1','2',... and 'x'."""
        out = [(int(b), str(k + 1)) for k, b in enumerate(self.idx)]
        out += [(int(b), "x") for b in self.x_idx]
        out.sort()
        return out

    def as_dict(self):
        return {"origin": self.origin, "direction": self.direction,
                "mode": self.mode, "n": len(self.idx),
                "idx": self.idx.tolist(), "skipped": self.skipped.tolist()}


def count_from(bars, origin, direction, mode="classic", max_count=34, stop=None):
    """Count forward from `origin`, which is itself number 1.

    max_count stops the walk once that number is taken. `stop` optionally caps
    the bar index the walk may reach (exclusive), which is how a nested count
    is confined to its parent leg.
    """
    if mode not in MODES:
        raise ValueError("unknown mode %r, want one of %s" % (mode, MODES))
    n = len(bars["c"])
    end = n if stop is None else min(n, int(stop))
    origin = int(origin)
    if not (0 <= origin < end):
        return Count(origin, direction, mode, [], [], [])

    if mode == "classic":
        last = min(end - 1, origin + max_count - 1)
        idx = np.arange(origin, last + 1, dtype=np.int64)
        return Count(origin, direction, mode, idx, np.zeros(len(idx), np.int64), [])

    rail = _rail(bars, mode, direction)
    better = (lambda a, b: a > b) if direction == UP else (lambda a, b: a < b)

    idx = [origin]
    skipped = [0]
    x_idx = []
    ref = rail[origin]
    pending = 0
    for i in range(origin + 1, end):
        if better(rail[i], ref):
            idx.append(i)
            skipped.append(pending)
            pending = 0
            ref = rail[i]
            if len(idx) >= max_count:
                break
        else:
            x_idx.append(i)
            pending += 1
    return Count(origin, direction, mode, idx, skipped, x_idx)


def count_all_modes(bars, origin, direction, max_count=34, stop=None):
    """The same leg counted three ways -- what the slides put side by side."""
    return {m: count_from(bars, origin, direction, m, max_count, stop)
            for m in MODES}


# ------------------------------------------------------------------- origins
def swings(high, low, k):
    """Fractal pivots of strength k, as ../futures/ranges/gbr.py defines them.

    A swing high is strictly above the k highs on each side; lows mirror.
    Reproduced here so tdt/ stands alone, and kept identical on purpose -- the
    origin definition is the one input every count downstream depends on.
    """
    n = len(high)
    if n < 2 * k + 1:
        return np.array([], np.int64), np.array([], np.int64)

    hi_nb = np.full(n, -np.inf)
    lo_nb = np.full(n, np.inf)
    for off in range(1, k + 1):
        hi_nb[off:] = np.maximum(hi_nb[off:], high[:-off])
        hi_nb[:-off] = np.maximum(hi_nb[:-off], high[off:])
        lo_nb[off:] = np.minimum(lo_nb[off:], low[:-off])
        lo_nb[:-off] = np.minimum(lo_nb[:-off], low[off:])

    valid = np.zeros(n, bool)
    valid[k:n - k] = True
    return (np.flatnonzero(valid & (high > hi_nb)).astype(np.int64),
            np.flatnonzero(valid & (low < lo_nb)).astype(np.int64))


def origins(bars, k=2):
    """Every swing pivot as a (bar_index, direction) origin, in bar order.

    A swing low opens an up leg, a swing high a down leg. Confirmation costs k
    candles: the pivot is only known k candles later, and every caller that
    trades off one has to respect that.
    """
    ih, il = swings(bars["h"], bars["l"], k)
    out = np.concatenate([
        np.stack([il, np.full(len(il), UP, np.int64)], axis=1),
        np.stack([ih, np.full(len(ih), DOWN, np.int64)], axis=1),
    ]) if len(ih) + len(il) else np.zeros((0, 2), np.int64)
    return out[np.argsort(out[:, 0], kind="stable")] if len(out) else out


def key_counts(bars, origin, direction, mode="classic", keys=tdtcore.KEY_COUNTS,
               max_count=34, stop=None):
    """Bar index where each key count landed; -1 where the count fell short."""
    c = count_from(bars, origin, direction, mode, max_count, stop)
    return {n: c.bar_of(n) for n in keys}
