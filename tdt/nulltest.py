"""Does a count of 7, 13 or 21 actually mark a turn?

The framework's load-bearing claim is that particular numbers are special. It
is testable, and the honest way to test it is the one this repo already uses
on PO3 block sizes: hold everything else fixed and ask whether the named
number stands out from its own neighbours.

Three tests, in increasing strength:

  hazard    Given a leg that has already reached count n, how often does it
            turn there? If 7 is special the hazard spikes at 7. If the curve
            is smooth through 7, the number is doing no work -- legs simply
            have a length distribution, and 7 sits inside it.

  neighbour Each key count scored against a local baseline built from the
            counts either side of it, skipping its immediate neighbours so a
            genuine spike cannot contaminate its own null.

  offset    The same legs, counted from an origin displaced a few candles off
            the swing. The leg and its endpoint are held fixed and only the
            numbering slides, which isolates the one thing TDT chooses: where
            the count starts. For classic counting this degenerates into the
            neighbour test by construction -- displacing the origin by j just
            renumbers every candle by j -- so it earns its keep on the
            contraction modes, where a displaced origin also changes which
            candles get skipped.

And one direct test of the Model #3 conclusion slide:

  grade     Do the advised signatures (13-7-7, 7-13-7, 7-7-7) actually beat
            the ones it calls not advised (anything with a 21)? Measured as
            forward move in the expected direction, entered no earlier than
            the signal could have been known.
"""
import numpy as np

import counting
import models
import tdtcore
from counting import DOWN, UP

COUNT_RANGE = range(2, 31)


# ------------------------------------------------------------------- hazard
def hazard(bars, k=3, mode="classic", max_count=60):
    """P(leg turns at n | leg reached n), for each n in COUNT_RANGE.

    `at_risk` is how many legs were still running at n, so the reader can see
    where the sample thins out -- a spike at 21 off nine legs is not a finding.
    """
    lgs = models.legs(bars, k=k, mode=mode, max_count=max_count, tol=0)
    terminal = np.array([lg.terminal for lg in lgs], np.int64)
    rows = []
    for n in COUNT_RANGE:
        at_risk = int((terminal >= n).sum())
        turns = int((terminal == n).sum())
        rows.append({
            "n": int(n), "at_risk": at_risk, "turns": turns,
            "hazard": (turns / at_risk) if at_risk else float("nan"),
            "key": int(n) in tdtcore.KEY_COUNTS,
        })
    return {"mode": mode, "k": int(k), "legs": len(lgs), "rows": rows}


def neighbour_z(haz, keys=tdtcore.KEY_COUNTS, gap=1, width=4):
    """Score each key count against the counts around it.

    The baseline skips `gap` neighbours on each side -- if a count of 7 really
    does attract turns, 6 and 8 inherit some of that and would flatter the
    null -- and then takes `width` counts either side of the gap.
    """
    by_n = {r["n"]: r for r in haz["rows"]}
    out = []
    for key in keys:
        near = [by_n[m]["hazard"] for m in range(key - gap - width, key + gap + width + 1)
                if m in by_n and abs(m - key) > gap and np.isfinite(by_n[m]["hazard"])]
        row = by_n.get(key)
        if row is None or len(near) < 3 or not np.isfinite(row["hazard"]):
            out.append({"key": key, "z": float("nan"), "n": 0})
            continue
        near = np.asarray(near, float)
        out.append({
            "key": int(key),
            "hazard": row["hazard"],
            "at_risk": row["at_risk"],
            "baseline": float(near.mean()),
            "baseline_sd": float(near.std(ddof=1)),
            "z": tdtcore.zscore(row["hazard"], near),
            "rank": tdtcore.rank_of(row["hazard"], near),
            "n_baseline": len(near),
        })
    return out


# ------------------------------------------------------------- offset null
def offset_null(bars, k=3, mode="classic", offsets=(1, 2, 3, 4, 5), max_count=60):
    """Key-count hazard when the count starts off the swing by a few candles.

    Every leg keeps its true start and end; only the candle the count calls 1
    moves. So the sample, the leg lengths and the turns are all identical to
    the real run, and the only thing that varies is the alignment TDT claims
    is meaningful.
    """
    lgs = models.legs(bars, k=k, mode=mode, max_count=max_count, tol=0)
    if not lgs:
        return {"error": "no legs"}

    def hazards(shift):
        term = []
        for lg in lgs:
            if shift == 0:
                term.append(lg.terminal)
                continue
            o = lg.start + shift
            if o >= lg.end:
                continue
            c = counting.count_from(bars, o, lg.direction, mode,
                                    max_count=max_count, stop=lg.end + 1)
            t = next((j + 1 for j, bar in enumerate(c.idx) if bar == lg.end), len(c))
            term.append(t)
        term = np.asarray(term, np.int64)
        out = {}
        for key in tdtcore.KEY_COUNTS:
            at_risk = int((term >= key).sum())
            out[key] = ((term == key).sum() / at_risk if at_risk else np.nan, at_risk)
        return out

    real = hazards(0)
    shifted = [hazards(j) for j in offsets]

    rows = []
    for key in tdtcore.KEY_COUNTS:
        vals = np.asarray([h[key][0] for h in shifted if np.isfinite(h[key][0])], float)
        obs, at_risk = real[key]
        rows.append({
            "key": int(key),
            "real": float(obs) if np.isfinite(obs) else float("nan"),
            "at_risk": at_risk,
            "null_mean": float(vals.mean()) if len(vals) else float("nan"),
            "null_sd": float(vals.std(ddof=1)) if len(vals) > 1 else float("nan"),
            "z": tdtcore.zscore(obs, vals) if len(vals) > 1 and np.isfinite(obs)
                 else float("nan"),
            "rank": tdtcore.rank_of(obs, vals) if len(vals) and np.isfinite(obs) else 0,
            "offsets": len(vals),
        })
    return {"mode": mode, "k": int(k), "legs": len(lgs),
            "offsets": list(offsets), "rows": rows}


# ------------------------------------------------------------- grade test
def forward_move(bars, entry_idx, direction, horizon):
    """Signed move over `horizon` bars from the close at entry, in points."""
    n = len(bars["c"])
    if entry_idx < 0 or entry_idx >= n - 1:
        return float("nan")
    stop = min(n - 1, entry_idx + horizon)
    return float((bars["c"][stop] - bars["c"][entry_idx]) * direction)


def grade_test(bars, ks=(5, 3, 2), mode="classic", horizon=10, tol=1):
    """Advised vs not-advised Model #3 signatures, by forward move.

    Entry is the bar after `confirmed_at`, so nothing is earned from knowing
    where the swing ended before it was knowable.
    """
    nests = models.model3(bars, ks=ks, mode=mode, tol=tol)
    groups = {}
    for nst in nests:
        mv = forward_move(bars, nst["confirmed_at"] + 1, nst["expect"], horizon)
        if not np.isfinite(mv):
            continue
        groups.setdefault(nst["verdict"], []).append(mv)

    rows = []
    for verdict, vals in sorted(groups.items()):
        a = np.asarray(vals, float)
        rows.append({
            "verdict": verdict, "n": len(a),
            "mean": float(a.mean()), "median": float(np.median(a)),
            "sd": float(a.std(ddof=1)) if len(a) > 1 else float("nan"),
            "win_rate": float((a > 0).mean()),
            "t": float(a.mean() / (a.std(ddof=1) / np.sqrt(len(a))))
                 if len(a) > 1 and a.std(ddof=1) > 0 else float("nan"),
        })

    ok = np.asarray(groups.get("ok", []), float)
    bad = np.asarray(groups.get("not advised", []), float)
    contrast = {"n_ok": len(ok), "n_bad": len(bad)}
    if len(ok) > 1 and len(bad) > 1:
        se = np.sqrt(ok.var(ddof=1) / len(ok) + bad.var(ddof=1) / len(bad))
        contrast["diff"] = float(ok.mean() - bad.mean())
        contrast["t"] = float((ok.mean() - bad.mean()) / se) if se > 0 else float("nan")
    return {"mode": mode, "ks": list(ks), "horizon": horizon,
            "rows": rows, "contrast": contrast,
            "signatures": models.signature_table(nests)}


# ------------------------------------------------------------------- driver
def run(bars, k=3, ks=(5, 3, 2), modes=counting.MODES, horizon=10):
    out = {"hazard": {}, "neighbour": {}, "offset": {}, "grade": {}}
    for mode in modes:
        h = hazard(bars, k=k, mode=mode)
        out["hazard"][mode] = h
        out["neighbour"][mode] = neighbour_z(h)
        out["offset"][mode] = offset_null(bars, k=k, mode=mode)
        out["grade"][mode] = grade_test(bars, ks=ks, mode=mode, horizon=horizon)
    return out
