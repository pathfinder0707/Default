"""Exhaustive search: is there ANY navigation of this space that pays?

The claim under test is not "does the average level trade work" -- that has been
answered -- but the much more reasonable "there is a way to trade these levels
profitably and we have not found the right combination yet". That deserves a
real search rather than an argument, so this walks the whole space:

    entry model   limit at the level, or structure entry at the retest close
    target/stop   every combination of the ATR grid, plus 4 R multiples
    condition     zone, session, volatility, break depth, sweep, confluence,
                  HTF alignment, direction, and each of the twenty levels

which is a few thousand cells. Two things make the answer meaningful rather
than a fishing licence:

  DISCOVERY / VALIDATION   cells are scored on 2010-2018 and then re-scored,
  unchanged, on 2019-2026. Searching thousands of combinations will always
  throw up winners in-sample; the only question is whether they survive on
  data that had no vote in selecting them.

  COSTS   every expectancy is net of a round-trip, converted at the median ATR
  of the trades in that cell, so a cell cannot win by trading a hit rate that
  is really a spread.

The headline output is deliberately blunt: of the cells that look profitable in
discovery, how many are still profitable in validation, and is that more than
chance would give. Plus the win-rate-versus-expectancy table, because the
single most expensive misconception in this space is that they are the same
question.
"""
import json
import os

import numpy as np

import gbr
import controls as ct
from edge import (atr, causal_mean, prior_day_levels, roll_extremes, collect,
                  annotate, first_hits, structure_trade, dedup, FAV, ADV, BIG,
                  RMULTS, RETEST_MAX, HORIZON, DEDUP, COST_PTS)

HERE = os.path.dirname(os.path.abspath(__file__))
SPLIT = 2019


def build_ctx():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    raw = {k: np.asarray(npz[k]) for k in npz.files}
    h, l, c = raw["h"], raw["l"], raw["c"]
    a = atr(h, l, c)
    pdh, pdl = prior_day_levels(raw["date"], h, l)
    rmax, rmin = roll_extremes(h, l, 120)
    return {"h": h, "l": l, "c": c, "atr": a, "yr": raw["yr"],
            "date": raw["date"], "tod": raw["hh"] * 100 + raw["mm"],
            "volr": a / np.maximum(causal_mean(a, 7200), 1e-9),
            "pdh": pdh, "pdl": pdl, "rmax": rmax, "rmin": rmin}


def cuts(ev):
    """Every filter a trader could apply, evaluated at entry time."""
    z, s, e, v = ev["zone"], ev["sess"], ev["excb"], ev["volb"]
    out = {"ALL": np.ones(len(ev["i"]), bool)}
    for k in ("EXT", "EQ", "FV", "GIP", "LLOD"):
        out["zone=" + k] = z == k
    for k in ("NYopen", "RTHrest", "London", "Asia"):
        out["sess=" + k] = s == k
    for k in np.unique(e):
        out["exc=" + str(k)] = e == k
    for k in np.unique(v):
        out[str(k)] = v == k
    out["sweep"] = ev["sweep"]
    out["no_sweep"] = ~ev["sweep"]
    out["htf"] = ev["conf"]
    out["long"] = ev["up"]
    out["short"] = ~ev["up"]
    out["shallow"] = e != "exc_2.5+"
    out["shallow+sweep"] = (e != "exc_2.5+") & ev["sweep"]
    out["EXT+sweep"] = (z == "EXT") & ev["sweep"]
    out["RTH+shallow"] = np.isin(s, ["NYopen", "RTHrest"]) & (e != "exc_2.5+")
    for p in gbr.LEVELS:
        out["level=%d" % p] = ev["pct"] == p
    # the two lines any grid has, which measured strongest on rejection
    out["boundary+EQ"] = np.isin(ev["pct"], [0.0, 50.0])
    # multi-scale confluence
    conf = ct.conf_map([27, 243, 729, 2187, 6561])[ct.bin_of(ev["L"])]
    out["confluence>=3"] = conf >= 3
    out["confluence<=1"] = conf <= 1
    return out


def score(win, pnl_r, atr_at, risk_atr, mask):
    """Win rate and cost-adjusted expectancy in R, for a subset."""
    n = int(mask.sum())
    if n < 300:
        return None
    p = float(win[mask].mean())
    gross = float(pnl_r[mask].mean())
    # cost as a fraction of the risk actually taken, per trade
    risk_pts = risk_atr[mask] * atr_at[mask]
    cost_r = float(np.mean(COST_PTS / np.maximum(risk_pts, 1e-9)))
    return {"n": n, "p": p, "ev_gross": gross, "ev_net": gross - cost_r}


def main():
    ctx = build_ctx()
    print("collecting retest events at R=81 ...")
    ev = annotate(collect(ctx, 81.0, 0.0), ctx, 81.0)
    i = ev["i"]
    yr = ctx["yr"][i]
    atr_at = ctx["atr"][i]
    n_ev = len(i)
    print("  %s events\n" % "{:,}".format(n_ev))

    C = cuts(ev)
    disc, val = yr < SPLIT, yr >= SPLIT

    # ---- build every (entry model, target, stop) payoff vector ------------
    plays = []
    for kf in range(len(FAV)):
        for ka in range(len(ADV)):
            tf, ta = ev["tf"][:, kf], ev["ta"][:, ka]
            live = (tf != BIG) | (ta != BIG)
            win = (tf < ta) & live
            pnl = np.where(win, FAV[kf], -ADV[ka]) * live
            # risk in ATR is the stop distance itself for the limit model
            plays.append(("limit %.2f/%.2f" % (FAV[kf], ADV[ka]), win, pnl,
                          np.full(n_ev, ADV[ka]), live))
    for q, rm in enumerate(RMULTS):
        r = ev["st"][:, q]
        live = r != 0
        win = r == 1
        pnl = np.where(win, rm, -1.0) * live
        plays.append(("structure %.1fR" % rm, win, pnl, ev["risk_atr"], live))
    print("%d entry/target/stop combinations x %d filters = %s cells\n"
          % (len(plays), len(C), "{:,}".format(len(plays) * len(C))))

    rows = []
    for pname, win, pnl, risk, live in plays:
        for cname, m in C.items():
            md, mv = m & disc & live, m & val & live
            a = score(win, pnl, atr_at, risk, md)
            b = score(win, pnl, atr_at, risk, mv)
            if not a or not b:
                continue
            rows.append({"play": pname, "cut": cname,
                         "disc_n": a["n"], "disc_p": a["p"],
                         "disc_ev": a["ev_net"],
                         "val_n": b["n"], "val_p": b["p"], "val_ev": b["ev_net"]})

    print("%s cells with enough data in both halves" % "{:,}".format(len(rows)))

    dev = np.array([r["disc_ev"] for r in rows])
    vev = np.array([r["val_ev"] for r in rows])
    pos_d = dev > 0
    print("\n=== the search ===")
    print("  profitable in DISCOVERY (2010-2018):      %s of %s  (%.1f%%)"
          % ("{:,}".format(int(pos_d.sum())), "{:,}".format(len(rows)),
             pos_d.mean() * 100))
    surv = pos_d & (vev > 0)
    print("  ... still profitable in VALIDATION:       %s  (%.1f%% of those)"
          % ("{:,}".format(int(surv.sum())),
             surv.sum() / max(pos_d.sum(), 1) * 100))
    print("  profitable in validation overall:         %.1f%%"
          % ((vev > 0).mean() * 100))
    print("  correlation, discovery EV vs validation:  %+.3f"
          % np.corrcoef(dev, vev)[0, 1])
    print("\n  If selection carried information, the survival rate would beat")
    print("  the base rate of %.1f%% and the correlation would be positive."
          % ((vev > 0).mean() * 100))

    print("\n=== best 12 cells in DISCOVERY, and what they did next ===")
    print("  %-18s %-16s %8s %7s %8s   %8s %7s %8s"
          % ("entry", "filter", "n", "win", "EV/R", "n", "win", "EV/R"))
    for r in sorted(rows, key=lambda x: -x["disc_ev"])[:12]:
        print("  %-18s %-16s %8s %7.3f %+8.3f   %8s %7.3f %+8.3f"
              % (r["play"], r["cut"], "{:,}".format(r["disc_n"]), r["disc_p"],
                 r["disc_ev"], "{:,}".format(r["val_n"]), r["val_p"],
                 r["val_ev"]))

    print("\n=== win rate is a dial: same events, different brackets ===")
    print("  %-18s %8s %9s %10s" % ("bracket", "win", "EV/R gross", "EV/R net"))
    for kf, ka in ((0, 6), (0, 5), (1, 5), (1, 3), (2, 2), (3, 1), (5, 0)):
        tf, ta = ev["tf"][:, kf], ev["ta"][:, ka]
        live = (tf != BIG) | (ta != BIG)
        win = (tf < ta) & live
        pnl = np.where(win, FAV[kf], -ADV[ka])[live]
        risk = ADV[ka] * atr_at[live]
        print("  %-18s %8.3f %+9.3f %+10.3f"
              % ("%.2f / %.2f" % (FAV[kf], ADV[ka]),
                 win[live].mean(), pnl.mean() / ADV[ka],
                 pnl.mean() / ADV[ka] - np.mean(COST_PTS / risk)))

    json.dump(rows, open(os.path.join(HERE, "search.json"), "w"))
    print("\nwrote search.json")


if __name__ == "__main__":
    main()
