"""TDT Trade Models #2 and #3, as the slides define them.

Model #2  Counts run on D1, execution on H1. The count starts at a swing and
          runs to where the leg turns; the number it reaches there is the read:

            [1-7]   continuation of the previous fractal
            [1-13]  reversal inside of the previous fractal

Model #3  The same count taken at three nested swing degrees on one chart --
          the slides draw the outer degree as circled numbers and the inner
          degrees in red on the same daily candles, not on separate
          timeframes. Each degree contributes its terminal count, giving a
          three-part signature, and the conclusion slide grades them:

            13-7-7  ok, 'Reversal inside of a Continuation'
            7-13-7  ok, 'Contunuation of a Continuation'   [sic]
            7-7-7   ok
            21-..-.., 7-21-13, 7-21-7, 13-21-7, ...  not advised

          So the grading rule is simply that a 21 anywhere in the signature
          disqualifies it. That is the one claim in this file cheap enough to
          test directly, and nulltest.py does.

Nothing here looks ahead: a swing of strength k is not known until k candles
after it prints, and `Leg.confirmed_at` carries that cost so the backtest
cannot enter before the signal existed.
"""
import numpy as np

import counting
import tdtcore
from counting import DOWN, UP

# The conclusion slide's verdicts, keyed by signature.
MODEL3_GRADE = {
    (13, 7, 7): ("ok", "Reversal inside of a Continuation"),
    (7, 13, 7): ("ok", "Contunuation of a Continuation"),
    (7, 7, 7): ("ok", ""),
}

# Model #2's two readings.
MODEL2_READ = {7: "continuation of previous fractal",
               13: "reversal inside of the previous fractal"}


def grade(signature):
    """('ok'|'not advised', label) for a three-part Model #3 signature.

    Anything containing a 21 is refused, which covers the slide's 21-..-..,
    7-21-13, 7-21-7 and 13-21-7 without enumerating them.
    """
    if signature is None or any(s is None for s in signature):
        return ("unclassified", "")
    if 21 in signature:
        return ("not advised", "contains a 21")
    if signature in MODEL3_GRADE:
        return MODEL3_GRADE[signature]
    return ("unlisted", "")


def bucket(n, keys=tdtcore.KEY_COUNTS, tol=1):
    """Snap a terminal count to the key count within tol, else None.

    A discretionary reader calls a leg that ran 6 or 8 candles 'a seven'; tol
    is how much of that latitude the study allows, and every result is
    reported against the tol it used.
    """
    if n is None or n < 0:
        return None
    best = min(keys, key=lambda k: abs(k - n))
    return int(best) if abs(best - n) <= tol else None


# ---------------------------------------------------------------------- legs
class Leg(object):
    """A swing-to-swing leg with its count already run.

    start/end are bar indices; `terminal` is the number the count reached at
    the end bar, and `key` is that snapped to 7/13/21 or None.
    """

    def __init__(self, start, end, direction, count, terminal, key, k,
                 confirmed_at):
        self.start = int(start)
        self.end = int(end)
        self.direction = int(direction)
        self.count = count
        self.terminal = int(terminal)
        self.key = key
        self.k = int(k)
        self.confirmed_at = int(confirmed_at)

    @property
    def bars(self):
        return self.end - self.start

    def as_dict(self):
        return {"start": self.start, "end": self.end, "dir": self.direction,
                "terminal": self.terminal, "key": self.key, "k": self.k,
                "confirmed_at": self.confirmed_at, "mode": self.count.mode}


def legs(bars, k=3, mode="classic", max_count=60, tol=1):
    """Every alternating swing-to-swing leg, counted.

    Pivots alternate by construction: consecutive same-direction pivots are
    collapsed to the more extreme one, so a leg always runs low->high or
    high->low and its terminal count means what the slides mean by it.
    """
    ih, il = counting.swings(bars["h"], bars["l"], k)
    piv = sorted([(int(i), DOWN) for i in ih] + [(int(i), UP) for i in il])
    if not piv:
        return []

    # Collapse runs of same-direction pivots to the extreme one. A down leg
    # opens at the highest high of a run of swing highs.
    kept = []
    for idx, d in piv:
        if kept and kept[-1][1] == d:
            prev = kept[-1][0]
            better = bars["h"][idx] > bars["h"][prev] if d == DOWN \
                else bars["l"][idx] < bars["l"][prev]
            if better:
                kept[-1] = (idx, d)
        else:
            kept.append((idx, d))

    out = []
    for (a, da), (b, _) in zip(kept, kept[1:]):
        c = counting.count_from(bars, a, da, mode, max_count=max_count, stop=b + 1)
        terminal = next((j + 1 for j, bar in enumerate(c.idx) if bar == b), -1)
        if terminal < 0:
            # The end bar contracted and took no number; the leg's read is the
            # last number that printed before it.
            terminal = len(c)
        out.append(Leg(a, b, da, c, terminal, bucket(terminal, tol=tol), k,
                       confirmed_at=b + k))
    return out


# ------------------------------------------------------------------ model #2
def model2(bars, k=3, mode="classic", tol=1):
    """Model #2 signals: D1 legs whose count terminates on 7 or 13.

    Returns one record per qualifying leg with the slide's reading attached.
    The signal is only actionable from `confirmed_at`, k candles after the
    turn, which is when the pivot is knowable.
    """
    out = []
    for lg in legs(bars, k=k, mode=mode, tol=tol):
        if lg.key not in MODEL2_READ:
            continue
        out.append({
            "start": lg.start, "end": lg.end, "dir": lg.direction,
            "terminal": lg.terminal, "key": lg.key,
            "read": MODEL2_READ[lg.key],
            "confirmed_at": lg.confirmed_at,
            "bars": lg.bars,
            # After a down leg the expected move is up, and vice versa: both
            # readings resolve to trading against the leg that just counted.
            "expect": -lg.direction,
        })
    return out


# ------------------------------------------------------------------ model #3
def _innermost_ending_at(sub_legs, end, lo, hi):
    """The sub-leg inside [lo,hi] that ends nearest `end`, or None.

    The slides draw the inner counts terminating at the same extreme as the
    outer one, so the nest is anchored on the shared turn.
    """
    best, best_gap = None, None
    for lg in sub_legs:
        if lg.start < lo or lg.end > hi:
            continue
        gap = abs(lg.end - end)
        if best_gap is None or gap < best_gap:
            best, best_gap = lg, gap
    return best


def model3(bars, ks=(5, 3, 1), mode="classic", tol=1):
    """Nested three-degree signatures, outermost degree first.

    ks are the swing strengths for the three degrees, coarsest first. Each
    degree-1 leg is matched with the degree-2 leg inside it that ends on the
    same turn, and that with a degree-3 leg inside it in turn.
    """
    if len(ks) != 3:
        raise ValueError("model #3 takes exactly three degrees, got %r" % (ks,))
    d1 = legs(bars, k=ks[0], mode=mode, tol=tol)
    d2 = legs(bars, k=ks[1], mode=mode, tol=tol)
    d3 = legs(bars, k=ks[2], mode=mode, tol=tol)

    out = []
    for a in d1:
        b = _innermost_ending_at(d2, a.end, a.start, a.end)
        if b is None:
            continue
        c = _innermost_ending_at(d3, b.end, b.start, b.end)
        if c is None:
            continue
        sig = (a.key, b.key, c.key)
        verdict, label = grade(sig)
        out.append({
            "start": a.start, "end": a.end, "dir": a.direction,
            "signature": sig,
            "sig_str": "-".join(str(s) if s else "?" for s in sig),
            "terminals": (a.terminal, b.terminal, c.terminal),
            "verdict": verdict, "label": label,
            "confirmed_at": max(a.confirmed_at, b.confirmed_at, c.confirmed_at),
            "expect": -a.direction,
        })
    return out


def signature_table(nests):
    """Counts per signature, so the advised set can be compared with the rest."""
    tab = {}
    for n in nests:
        key = n["sig_str"]
        row = tab.setdefault(key, {"sig": key, "n": 0, "verdict": n["verdict"],
                                   "label": n["label"]})
        row["n"] += 1
    return sorted(tab.values(), key=lambda r: -r["n"])
