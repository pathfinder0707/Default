"""Executable rules for Model #2 and Model #3, and what they pay.

The models as taught are discretionary. Making them testable means fixing the
three things the slides leave to the trader, and every result below is
conditional on these choices:

  entry   the open of the bar after the signal could have been known. A swing
          of strength k is not confirmed until k candles later, so entry is at
          `confirmed_at + 1`. This is the single most important line in the
          file: entering at the turn itself would manufacture an edge that no
          one could have taken.

  stop    beyond the extreme the count terminated on, padded by `pad` times
          the leg's own average candle range. That extreme is the level the
          read is built on, so it is also what invalidates it.

  target  a multiple of the risk, with a bar timeout. Both are swept.

Costs are charged in points per round turn, once, on entry.
"""
import numpy as np

import counting
import models
from counting import DOWN, UP


def _atr(bars, lo, hi, fallback=1.0):
    """Mean candle range over [lo,hi), used to size the stop pad."""
    lo = max(0, lo)
    hi = min(len(bars["h"]), max(hi, lo + 1))
    r = bars["h"][lo:hi] - bars["l"][lo:hi]
    m = float(r.mean()) if len(r) else fallback
    return m if np.isfinite(m) and m > 0 else fallback


def simulate(bars, signals, rr=2.0, pad=0.25, timeout=20, cost=0.0):
    """Run one signal set through the same entry/stop/target rules.

    A trade resolves on whichever of stop or target the bar touches. When a
    single bar spans both, the stop is taken -- the pessimistic assumption,
    since intrabar order is unknowable from OHLC.
    """
    n = len(bars["c"])
    trades = []
    for sig in signals:
        entry_i = int(sig["confirmed_at"]) + 1
        if entry_i >= n - 1:
            continue
        d = int(sig["expect"])
        entry = float(bars["o"][entry_i])

        # the extreme the count terminated on
        seg_lo, seg_hi = int(sig["start"]), int(sig["end"]) + 1
        ext = float(bars["l"][seg_lo:seg_hi].min()) if d == UP \
            else float(bars["h"][seg_lo:seg_hi].max())
        buf = pad * _atr(bars, seg_lo, seg_hi)
        stop = ext - buf if d == UP else ext + buf
        risk = abs(entry - stop)
        if risk <= 0 or not np.isfinite(risk):
            continue
        target = entry + d * rr * risk

        out, exit_i, exit_px = "timeout", min(n - 1, entry_i + timeout), None
        for i in range(entry_i, min(n, entry_i + timeout + 1)):
            hit_stop = bars["l"][i] <= stop if d == UP else bars["h"][i] >= stop
            hit_tgt = bars["h"][i] >= target if d == UP else bars["l"][i] <= target
            if hit_stop:
                out, exit_i, exit_px = "stop", i, stop
                break
            if hit_tgt:
                out, exit_i, exit_px = "target", i, target
                break
        if exit_px is None:
            exit_px = float(bars["c"][exit_i])

        pts = (exit_px - entry) * d - cost
        trades.append({
            "entry_i": entry_i, "exit_i": int(exit_i), "dir": d,
            "entry": entry, "stop": stop, "target": target,
            "risk": risk, "pts": float(pts), "r": float(pts / risk),
            "outcome": out, "bars": int(exit_i - entry_i),
            "key": sig.get("key"), "sig": sig.get("sig_str"),
            "verdict": sig.get("verdict"),
        })
    return trades


def stats(trades):
    """Summary of a trade list, in R and in points."""
    if not trades:
        return {"n": 0}
    r = np.array([t["r"] for t in trades], float)
    p = np.array([t["pts"] for t in trades], float)
    wins, losses = p[p > 0], p[p <= 0]
    eq = np.cumsum(r)
    dd = float((np.maximum.accumulate(np.r_[0, eq]) - np.r_[0, eq]).max())
    sd = r.std(ddof=1) if len(r) > 1 else float("nan")
    return {
        "n": len(trades),
        "win_rate": float((p > 0).mean()),
        "exp_r": float(r.mean()),
        "exp_pts": float(p.mean()),
        "total_r": float(r.sum()),
        "sd_r": float(sd),
        "t": float(r.mean() / (sd / np.sqrt(len(r)))) if len(r) > 1 and sd > 0
             else float("nan"),
        "pf": float(wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() else float("inf"),
        "max_dd_r": dd,
        "p_target": float(sum(t["outcome"] == "target" for t in trades) / len(trades)),
        "p_stop": float(sum(t["outcome"] == "stop" for t in trades) / len(trades)),
        "p_timeout": float(sum(t["outcome"] == "timeout" for t in trades) / len(trades)),
        "med_bars": float(np.median([t["bars"] for t in trades])),
    }


def by(trades, field):
    """Stats split by a signal field -- key count, or Model #3 verdict."""
    groups = {}
    for t in trades:
        groups.setdefault(t.get(field), []).append(t)
    out = []
    for val, ts in groups.items():
        if val is None:
            continue
        row = {"value": val}
        row.update(stats(ts))
        out.append(row)
    return sorted(out, key=lambda r: -r["n"])


def equity(trades, cap=400):
    """Cumulative R curve, thinned for the report."""
    eq = np.cumsum([t["r"] for t in trades]) if trades else np.array([])
    step = max(1, len(eq) // cap)
    return [round(float(eq[i]), 3) for i in range(0, len(eq), step)]


# ------------------------------------------------------------------- driver
def run(bars, k=3, ks=(5, 3, 2), modes=counting.MODES,
        rr_grid=(1.0, 1.5, 2.0, 3.0), timeout=20, pad=0.25, cost=0.0, tol=1):
    """Both models, every counting mode, swept over the reward multiple."""
    out = {"model2": {}, "model3": {}, "sweep": [], "params": {
        "k": k, "ks": list(ks), "timeout": timeout, "pad": pad, "cost": cost,
        "tol": tol, "rr_grid": list(rr_grid)}}

    for mode in modes:
        m2 = models.model2(bars, k=k, mode=mode, tol=tol)
        m3 = models.model3(bars, ks=ks, mode=mode, tol=tol)

        for rr in rr_grid:
            for name, sigs in (("model2", m2), ("model3", m3)):
                tr = simulate(bars, sigs, rr=rr, pad=pad, timeout=timeout, cost=cost)
                row = {"model": name, "mode": mode, "rr": rr}
                row.update(stats(tr))
                out["sweep"].append(row)

        base2 = simulate(bars, m2, rr=2.0, pad=pad, timeout=timeout, cost=cost)
        base3 = simulate(bars, m3, rr=2.0, pad=pad, timeout=timeout, cost=cost)
        out["model2"][mode] = {"n_signals": len(m2), "stats": stats(base2),
                               "by_key": by(base2, "key"),
                               "equity": equity(base2)}
        out["model3"][mode] = {"n_signals": len(m3), "stats": stats(base3),
                               "by_verdict": by(base3, "verdict"),
                               "by_sig": by(base3, "sig"),
                               "equity": equity(base3)}
    return out
