"""Verification of the counting engine against the slides' worked examples.

Runs with no market data, so it is the check that survives a fresh checkout.

The slides give two panels of the same leg counted two ways, and the thing
worth pinning down is how the panels disagree:

  EURUSD M1   the candle classic counting numbers 13, contraction-by-wick
              numbers 12 -- exactly one candle in between contracted.
  USDCAD D1   the candle classic numbers 13, contraction-by-body numbers 9 --
              four contracted.

Both are the same invariant: classic number - contraction number at any candle
equals the count of x marks before it. These tests build series that contract
a chosen number of times and assert that identity, rather than trying to
reproduce two screenshots pixel for pixel.
"""
import sys

import numpy as np

import counting
from counting import DOWN, UP

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  ok    %s" % name)
    else:
        print("  FAIL  %s   %s" % (name, detail))
        FAILURES.append(name)


def make_bars(highs, lows=None, opens=None, closes=None):
    h = np.asarray(highs, float)
    l = np.asarray(lows, float) if lows is not None else h - 1.0
    o = np.asarray(opens, float) if opens is not None else (h + l) / 2 - 0.1
    c = np.asarray(closes, float) if closes is not None else (h + l) / 2 + 0.1
    return {"o": o, "h": h, "l": l, "c": c}


def leg(n_bars, contract_at=(), step=1.0):
    """A rising leg of n_bars candles, contracting on the given 0-based indices.

    A contracting candle repeats the previous high instead of advancing it, so
    it fails the expansion test on both wick and body.
    """
    highs, cur = [], 10.0
    for i in range(n_bars):
        if i and i not in contract_at:
            cur += step
        highs.append(cur)
    return make_bars(highs)


# ------------------------------------------------------------------- classic
def test_classic():
    print("classic counting")
    bars = leg(20)
    c = counting.count_from(bars, 0, UP, "classic")
    check("number equals offset from origin",
          all(c.bar_of(n) == n - 1 for n in range(1, 21)),
          c.idx[:5].tolist())
    check("7 lands on the 7th candle", c.bar_of(7) == 6, c.bar_of(7))
    check("13 lands on the 13th candle", c.bar_of(13) == 12, c.bar_of(13))
    check("21 lands on the 21st candle", counting.count_from(
        leg(30), 0, UP, "classic").bar_of(21) == 20)
    check("no candle is ever skipped", len(c.x_idx) == 0, len(c.x_idx))
    check("counting from a later origin shifts the whole leg",
          counting.count_from(bars, 5, UP, "classic").bar_of(7) == 11)


# ---------------------------------------------------- the EURUSD M1 relation
def test_m1_wick_relation():
    print("EURUSD M1 panel: classic 13 is contraction-by-wick 12")
    # one contraction anywhere before the 13th candle
    bars = leg(20, contract_at={5})
    classic = counting.count_from(bars, 0, UP, "classic")
    wick = counting.count_from(bars, 0, UP, "wick")
    bar13 = classic.bar_of(13)
    num = next(k + 1 for k, b in enumerate(wick.idx) if b == bar13)
    check("contraction numbers that candle 12", num == 12, num)
    check("exactly one x precedes it", (wick.x_idx < bar13).sum() == 1,
          int((wick.x_idx < bar13).sum()))


# ---------------------------------------------------- the USDCAD D1 relation
def test_d1_body_relation():
    print("USDCAD D1 panel: classic 13 is contraction-by-body 9")
    bars = leg(20, contract_at={3, 6, 8, 10})
    classic = counting.count_from(bars, 0, UP, "classic")
    body = counting.count_from(bars, 0, UP, "body")
    bar13 = classic.bar_of(13)
    num = next(k + 1 for k, b in enumerate(body.idx) if b == bar13)
    check("contraction numbers that candle 9", num == 9, num)
    check("four x marks precede it", (body.x_idx < bar13).sum() == 4,
          int((body.x_idx < bar13).sum()))


# ----------------------------------------------------------- the invariant
def test_invariant():
    print("the invariant behind both panels")
    rng = np.random.default_rng(7)
    worst = 0
    for trial in range(200):
        n = 40
        contract = set(rng.choice(np.arange(1, n), size=rng.integers(0, 12),
                                  replace=False).tolist())
        bars = leg(n, contract_at=contract)
        classic = counting.count_from(bars, 0, UP, "classic", max_count=n)
        for mode in ("wick", "body"):
            cc = counting.count_from(bars, 0, UP, mode, max_count=n)
            for k, bar in enumerate(cc.idx):
                classic_num = bar + 1
                x_before = int((cc.x_idx < bar).sum())
                if classic_num - (k + 1) != x_before:
                    worst += 1
            if len(cc) > len(classic):
                worst += 1
    check("classic number - contraction number == x marks before it, "
          "over 200 random legs", worst == 0, "%d violations" % worst)

    bars = leg(30, contract_at={2, 5, 9})
    for mode in counting.MODES:
        cc = counting.count_from(bars, 0, UP, mode)
        check("%s never numbers a candle before its origin" % mode,
              (cc.idx >= 0).all() and cc.idx[0] == 0)


# ------------------------------------------------------------ wick vs body
def test_wick_body_differ():
    print("wick and body counts genuinely differ")
    # candle 2 pokes a higher high on an upper wick but its body tops lower:
    # an expansion by wick, a contraction by body. This is the whole reason
    # the slides show the two panels separately.
    h = [10.0, 11.0, 11.5, 12.5]
    l = [9.0, 10.0, 10.2, 11.0]
    o = [9.5, 10.2, 10.4, 11.2]
    c = [9.8, 10.9, 10.5, 12.2]     # body top 9.8, 10.9, 10.5, 12.2
    bars = make_bars(h, l, o, c)
    wick = counting.count_from(bars, 0, UP, "wick")
    body = counting.count_from(bars, 0, UP, "body")
    check("wick counts the higher-high candle", 2 in wick.idx.tolist(),
          wick.idx.tolist())
    check("body marks it x", 2 in body.x_idx.tolist(), body.x_idx.tolist())
    check("the two modes end on different numbers", len(wick) != len(body),
          (len(wick), len(body)))


# ------------------------------------------------------------- down legs
def test_down_legs():
    print("down legs mirror up legs")
    rng = np.random.default_rng(11)
    for trial in range(50):
        n = 25
        contract = set(rng.choice(np.arange(1, n), size=5, replace=False).tolist())
        up = leg(n, contract_at=contract)
        down = {"o": -up["o"], "c": -up["c"], "h": -up["l"], "l": -up["h"]}
        for mode in counting.MODES:
            a = counting.count_from(up, 0, UP, mode)
            b = counting.count_from(down, 0, DOWN, mode)
            if a.idx.tolist() != b.idx.tolist():
                check("mirror holds for %s" % mode, False,
                      (a.idx.tolist(), b.idx.tolist()))
                return
    check("mirrored prices give mirrored counts in all three modes", True)


# ------------------------------------------------------------------ bounds
def test_bounds():
    print("bounds and degenerate input")
    bars = leg(30)
    c = counting.count_from(bars, 0, UP, "wick", stop=10)
    check("stop confines the walk", c.idx.max() < 10, c.idx.max())
    check("a count that falls short reports -1",
          counting.count_from(leg(4), 0, UP, "classic").bar_of(13) == -1)
    check("reached() agrees with bar_of()",
          not counting.count_from(leg(4), 0, UP, "classic").reached(13))
    check("origin past the end gives an empty count",
          len(counting.count_from(bars, 99, UP, "wick")) == 0)
    check("max_count caps the walk",
          len(counting.count_from(bars, 0, UP, "classic", max_count=7)) == 7)
    flat = make_bars([5.0] * 12)
    fc = counting.count_from(flat, 0, UP, "wick")
    check("a leg that never expands numbers only its origin", len(fc) == 1,
          len(fc))
    check("and marks every other candle x", len(fc.x_idx) == 11, len(fc.x_idx))


# ------------------------------------------------------------------ swings
def test_swings():
    print("swing origins")
    # bars 2 and 6 both top their two neighbours on each side; bar 4 bottoms.
    h = np.array([1, 2, 5, 2, 1, 2, 3, 2, 1], float)
    l = h - 1
    ih, il = counting.swings(h, l, 2)
    check("finds both interior swing highs", ih.tolist() == [2, 6], ih.tolist())
    check("finds the interior swing low", il.tolist() == [4], il.tolist())
    check("edges are never pivots -- k candles are needed on each side",
          0 not in ih.tolist() and len(h) - 1 not in il.tolist())
    bars = make_bars(h, l)
    og = counting.origins(bars, k=2)
    check("origins are sorted by bar", (np.diff(og[:, 0]) >= 0).all() if len(og) > 1 else True)
    check("a swing high opens a down leg",
          all(d == DOWN for b, d in og.tolist() if b in ih.tolist()))


def main():
    for fn in (test_classic, test_m1_wick_relation, test_d1_body_relation,
               test_invariant, test_wick_body_differ, test_down_legs,
               test_bounds, test_swings):
        fn()
        print()
    if FAILURES:
        print("%d FAILED: %s" % (len(FAILURES), ", ".join(FAILURES)))
        return 1
    print("all counting checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
