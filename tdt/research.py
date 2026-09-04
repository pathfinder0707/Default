"""The full research run: RESEARCH.json for the structured report.

Produces the evidence a risk committee would ask for before allocating to
anything found here -- performance, risk, overfitting, robustness, capacity --
for the one rule that survived the search, plus the TDT variants it has to be
compared against.

The rule under test, stated once:

    On M15 NQ, when a swing pivot of strength k confirms, enter on the next
    candle in the direction of the leg that just completed. Stop beyond that
    leg's extreme padded by 0.25 x its mean candle range. Target 3R. Give up
    after 20 candles. One position at a time.

TDT's contribution to that rule is the claim that the entry belongs on count 7.
It does not: the entry belongs on count k+1, which is the first candle the
pivot is knowable on, and equals 7 only when k happens to be 6.
"""
import numpy as np

import analytics as A
import holdtest
import sweep
import tdtcore

TF = "M15"
TRAIN = (2016, 2022)
TEST = (2023, 2026)
RR, TIMEOUT, PAD = 3.0, 20, 0.25


# ------------------------------------------------------------------- trades
def make_trades(bars, em, yrs, dt, k, offset, years, rr=RR, timeout=TIMEOUT,
                pad=PAD, cost=sweep.COST_PTS, follow=True, non_overlap=True):
    """Full trade records, including excursions, for one rule and period."""
    so, td, se = holdtest.signals_at_offset(bars, k, offset, follow=follow)
    ec = np.maximum(se, so + k)
    keep = ec < len(bars["c"]) - 1
    so, td, ec = so[keep], td[keep], ec[keep]
    segs = sweep.segment_extremes(bars, so, ec)
    buf = pad * segs["atr"]
    stop = np.where(td == sweep.UP, segs["seg_lo"] - buf, segs["seg_hi"] + buf)

    x0 = em["xmap"][ec + 1]
    xb = em["bars"]
    yr = yrs[np.clip(x0, 0, len(yrs) - 1)]
    sel = (yr >= years[0]) & (yr <= years[1]) & (x0 < len(xb["c"]) - 1)
    x0, td, stop = x0[sel], td[sel], stop[sel]
    if len(x0) < 30:
        return None

    entry = xb["o"][x0]
    risk = np.abs(entry - stop)
    g = (risk > 0) & np.isfinite(risk) & (((entry - stop) * td) > 0)
    x0, td, stop, entry, risk = x0[g], td[g], stop[g], entry[g], risk[g]
    target = entry + td * rr * risk

    outcome, exit_i, exit_px = sweep.simulate_vec(xb, x0, td, stop, target, timeout)

    # excursions in R, over the actual holding window of each trade
    mae = np.zeros(len(x0))
    mfe = np.zeros(len(x0))
    for step in range(timeout + 1):
        i = np.minimum(x0 + step, len(xb["c"]) - 1)
        live = (x0 + step) <= exit_i
        adv = np.where(td == sweep.UP, entry - xb["l"][i], xb["h"][i] - entry) / risk
        fav = np.where(td == sweep.UP, xb["h"][i] - entry, entry - xb["l"][i]) / risk
        mae = np.where(live, np.maximum(mae, adv), mae)
        mfe = np.where(live, np.maximum(mfe, fav), mfe)

    pts = (exit_px - entry) * td - cost
    r = pts / risk

    if non_overlap:
        order = np.argsort(x0, kind="stable")
        keep_i, free = [], -1
        for i in order.tolist():
            if x0[i] >= free:
                keep_i.append(i)
                free = exit_i[i]
        sel2 = np.array(keep_i, np.int64)
        x0, exit_i, td, entry, stop, risk = (x0[sel2], exit_i[sel2], td[sel2],
                                             entry[sel2], stop[sel2], risk[sel2])
        pts, r, mae, mfe, outcome = (pts[sel2], r[sel2], mae[sel2], mfe[sel2],
                                     outcome[sel2])

    return {"x0": x0, "exit_i": exit_i, "dir": td, "entry": entry, "stop": stop,
            "risk": risk, "pts": pts, "r": r, "mae": mae, "mfe": mfe,
            "outcome": outcome, "entry_dt": dt[x0], "exit_dt": dt[exit_i],
            "bars_held": exit_i - x0}


def block(tr, label):
    if tr is None:
        return None
    p = A.perf(tr["r"], tr["exit_dt"], label)
    if p is None:
        return None
    p["mae_med"] = float(np.median(tr["mae"]))
    p["mfe_med"] = float(np.median(tr["mfe"]))
    p["mae_p90"] = float(np.quantile(tr["mae"], 0.90))
    p["bars_med"] = float(np.median(tr["bars_held"]))
    p["p_target"] = float((tr["outcome"] == 1).mean())
    p["p_stop"] = float((tr["outcome"] == 0).mean())
    p["p_timeout"] = float((tr["outcome"] == 2).mean())
    p["med_risk_pts"] = float(np.median(tr["risk"]))
    p["pct_long"] = float((tr["dir"] == sweep.UP).mean())
    return p


def strip(p):
    return {k: v for k, v in p.items() if not k.startswith("_")} if p else None


# ---------------------------------------------------------------- robustness
def by_group(tr, keys, names):
    """Split a trade series by a categorical key and report each bucket."""
    out = []
    for val in sorted(set(keys.tolist())):
        m = keys == val
        if m.sum() < 30:
            continue
        r = tr["r"][m]
        sd = r.std(ddof=1)
        out.append({"group": names.get(val, str(val)), "n": int(m.sum()),
                    "exp_r": float(r.mean()), "win_rate": float((r > 0).mean()),
                    "t": float(r.mean() / (sd / np.sqrt(m.sum()))) if sd > 0 else np.nan,
                    "total_r": float(r.sum())})
    return out


def cost_curve(bars, em, yrs, dt, k, years):
    """What per-round-turn cost takes the edge to zero."""
    rows = []
    for c in (0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0):
        tr = make_trades(bars, em, yrs, dt, k, k, years, cost=c)
        if tr is None:
            continue
        r = tr["r"]
        sd = r.std(ddof=1)
        rows.append({"cost_pts": c, "n": int(len(r)), "exp_r": float(r.mean()),
                     "t": float(r.mean() / (sd / np.sqrt(len(r)))) if sd > 0 else np.nan})
    return rows


def walk_forward(bars, em, yrs, dt, ks=(2, 3, 4, 6, 8), train_len=3):
    """Rolling re-selection of k, each fold validated on the year that follows.

    k is the one parameter with real leverage over the result, so it is the one
    re-chosen at every step. Nothing else is re-fitted, which is conservative:
    an adaptive system would do better and would also be easier to overfit.
    """
    folds = []
    for test_yr in range(TRAIN[0] + train_len, TEST[1] + 1):
        tr_years = (test_yr - train_len, test_yr - 1)
        best, best_t = None, -np.inf
        for k in ks:
            t = make_trades(bars, em, yrs, dt, k, k, tr_years)
            if t is None or len(t["r"]) < 100:
                continue
            sd = t["r"].std(ddof=1)
            tt = t["r"].mean() / (sd / np.sqrt(len(t["r"]))) if sd > 0 else -np.inf
            if tt > best_t:
                best, best_t = k, tt
        if best is None:
            continue
        te = make_trades(bars, em, yrs, dt, best, best, (test_yr, test_yr))
        if te is None:
            continue
        r = te["r"]
        sd = r.std(ddof=1)
        folds.append({"test_year": test_yr, "train": list(tr_years), "k": best,
                      "train_t": float(best_t), "n": int(len(r)),
                      "exp_r": float(r.mean()), "total_r": float(r.sum()),
                      "win_rate": float((r > 0).mean()),
                      "t": float(r.mean() / (sd / np.sqrt(len(r)))) if sd > 0 else np.nan})
    return folds


def pbo_matrix(bars, em, yrs, dt, ks=(2, 3, 4, 6, 8), offsets=range(1, 13)):
    """Monthly P&L for every (k, offset) config, for the PBO computation.

    This is the space the choice of count actually lives in, so it is the space
    where overfitting in choosing a count would show up.
    """
    cols, labels = [], []
    grid = None
    for k in ks:
        for off in offsets:
            tr = make_trades(bars, em, yrs, dt, k, off, (TRAIN[0], TEST[1]))
            if tr is None or len(tr["r"]) < 200:
                continue
            months = tr["exit_dt"].astype("datetime64[M]")
            if grid is None:
                grid = np.arange(months.min(), months.max() + np.timedelta64(1, "M"),
                                 dtype="datetime64[M]")
            idx = (months - grid[0]).astype(int)
            ok = (idx >= 0) & (idx < len(grid))
            pnl = np.bincount(idx[ok], weights=tr["r"][ok], minlength=len(grid))
            cols.append(pnl)
            labels.append("k=%d off=%d (count %d)" % (k, off, off + 1))
    if not cols:
        return None, []
    return np.column_stack(cols), labels


def capacity(bars, em, tr, participation=0.01):
    """Contracts supportable at a given share of traded volume.

    Uses the volume actually printed in the entry candle, which is the bar the
    order has to be filled in.
    """
    v = em["bars"].get("v")
    if v is None or tr is None:
        return None
    vol = v[np.clip(tr["x0"], 0, len(v) - 1)]
    med = float(np.median(vol))
    return {"median_entry_volume": med,
            "contracts_at_participation": float(med * participation),
            "participation": participation,
            "notional_per_contract": float(np.median(tr["entry"]) * A.POINT_VALUE)}


# ------------------------------------------------------------------- driver
def main():
    import json
    import os
    import time

    HERE = os.path.dirname(os.path.abspath(__file__))
    t0 = time.time()

    raw = tdtcore.load(from_year=2016)
    bars = tdtcore.resample(raw, TF)
    em = tdtcore.exec_map(raw, TF, sweep.EXEC_OF[TF])
    xsrc = em["bars"]["src"]
    yrs = raw["yr"][xsrc]
    dt = A.ts_to_datetime64(raw["ts"][xsrc])
    em["bars"]["v"] = raw["v"][xsrc] if "v" in raw else None

    out = {"meta": {
        "built": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tf": TF, "train": list(TRAIN), "test": list(TEST),
        "rr": RR, "timeout": TIMEOUT, "pad": PAD,
        "cost_pts": sweep.COST_PTS, "point_value": A.POINT_VALUE,
        "account": A.ACCOUNT, "risk_frac": A.RISK_FRAC,
        "candles": int(len(bars["c"])),
        "exec_candles": int(len(em["bars"]["c"])),
        "first": str(dt[0]), "last": str(dt[-1]),
    }}

    # ---- headline rule, per k, both periods
    print("performance ...")
    out["performance"] = {}
    trades = {}
    for k in (2, 3, 4, 6, 8):
        for lbl, yy in (("train", TRAIN), ("test", TEST)):
            tr = make_trades(bars, em, yrs, dt, k, k, yy)
            trades[(k, lbl)] = tr
            p = block(tr, "k=%d %s" % (k, lbl))
            if p:
                out["performance"]["%d|%s" % (k, lbl)] = strip(p)
                print("  k=%d %-5s n=%5d sharpe %5.2f calmar %5.2f maxDD $%8s t=%+.2f"
                      % (k, lbl, p["n_trades"], p["sharpe"], p["calmar"],
                         format(round(p["max_dd_usd"]), ","), p["t"]))

    K = 6
    tr_tr, tr_te = trades[(K, "train")], trades[(K, "test")]
    out["meta"]["headline_k"] = K

    # ---- the TDT comparison: same rule, entry forced onto count 7
    print("TDT comparison ...")
    out["tdt_vs_rule"] = {}
    for k in (2, 3, 4, 6, 8):
        for lbl, yy in (("train", TRAIN), ("test", TEST)):
            t7 = make_trades(bars, em, yrs, dt, k, 6, yy)     # TDT's count 7
            tk = make_trades(bars, em, yrs, dt, k, k, yy)     # count k+1
            if t7 is None or tk is None:
                continue
            a, b = t7["r"], tk["r"]
            se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
            out["tdt_vs_rule"]["%d|%s" % (k, lbl)] = {
                "count7_exp_r": float(a.mean()), "count7_n": int(len(a)),
                "countk1_exp_r": float(b.mean()), "countk1_n": int(len(b)),
                "diff": float(a.mean() - b.mean()),
                "t": float((a.mean() - b.mean()) / se) if se > 0 else np.nan,
                "identical": bool(len(a) == len(b) and np.allclose(a, b)),
            }

    # ---- overfitting
    print("overfitting statistics ...")
    p_te = block(tr_te, "test")
    n_trials = 25920
    # DSR depends on how many trials you admit to. 25,920 is the full sweep and
    # the most conservative reading; 60 is the (k, offset) space this rule
    # actually lives in; 1 is the counterfactual where it had been specified in
    # advance. Reporting the curve is more honest than picking one.
    out["dsr"] = {"by_trials": [], "note_trials": n_trials}
    for nt in (1, 12, 60, 720, 25920):
        d_ = A.deflated_sharpe(p_te["sharpe"], p_te["n_days"], max(2, nt),
                               p_te["skew_daily"], p_te["kurt_daily"])
        d_["trials"] = nt
        out["dsr"]["by_trials"].append(d_)
    out["dsr"]["test"] = out["dsr"]["by_trials"][-1]
    M, labels = pbo_matrix(bars, em, yrs, dt)
    out["pbo"] = A.pbo(M) if M is not None else {}
    out["pbo"]["configs"] = labels[:60]
    print("  DSR %.4f (needs > 0.95)   PBO %.3f (needs < 0.50)"
          % (out["dsr"]["test"]["dsr"], out["pbo"].get("pbo", float("nan"))))

    # ---- robustness
    print("robustness ...")
    out["walk_forward"] = walk_forward(bars, em, yrs, dt)
    out["cost_curve"] = cost_curve(bars, em, yrs, dt, K, TEST)
    out["mc_dd"] = {"test": A.mc_drawdown(tr_te["r"]),
                    "train": A.mc_drawdown(tr_tr["r"])}
    out["capacity"] = capacity(bars, em, tr_te)

    # regimes on the test period
    reg = {}
    hh = raw["hh"][xsrc][tr_te["x0"]]
    sess = np.where(hh < 3, 0, np.where(hh < 9, 1, np.where(hh < 12, 2,
                    np.where(hh < 16, 3, 4))))
    reg["session"] = by_group(tr_te, sess,
                              {0: "18:00-02:59 Asia", 1: "03:00-08:59 London",
                               2: "09:00-11:59 NY AM", 3: "12:00-15:59 NY PM",
                               4: "16:00-17:59 close"})
    reg["direction"] = by_group(tr_te, tr_te["dir"], {1: "long", -1: "short"})
    reg["year"] = by_group(tr_te, tr_te["exit_dt"].astype("datetime64[Y]")
                           .astype(int) + 1970, {})
    # realised volatility quintiles, measured before entry so it is knowable
    rng_ = em["bars"]["h"] - em["bars"]["l"]
    csum = np.concatenate([[0.0], np.cumsum(rng_)])
    lo = np.maximum(tr_te["x0"] - 96, 0)
    vol = (csum[tr_te["x0"]] - csum[lo]) / np.maximum(1, tr_te["x0"] - lo)
    q = np.quantile(vol, [0.2, 0.4, 0.6, 0.8])
    reg["volatility"] = by_group(tr_te, np.searchsorted(q, vol),
                                 {0: "quietest 20%", 1: "2nd", 2: "middle",
                                  3: "4th", 4: "most volatile 20%"})
    out["regimes"] = reg

    # per-year for both periods, on the headline k
    allyr = {}
    for lbl in ("train", "test"):
        t = trades[(K, lbl)]
        if t is None:
            continue
        for y in sorted(set(t["exit_dt"].astype("datetime64[Y]").astype(int) + 1970)):
            m = (t["exit_dt"].astype("datetime64[Y]").astype(int) + 1970) == y
            if m.sum() < 20:
                continue
            r = t["r"][m]
            allyr[str(y)] = {"period": lbl, "n": int(m.sum()),
                             "exp_r": float(r.mean()), "total_r": float(r.sum()),
                             "usd": float(r.sum() * A.ACCOUNT * A.RISK_FRAC),
                             "win_rate": float((r > 0).mean())}
    out["by_year"] = allyr

    # MAE/MFE profile
    out["excursion"] = {
        "mae_deciles": [float(np.quantile(tr_te["mae"], q / 10)) for q in range(1, 10)],
        "mfe_deciles": [float(np.quantile(tr_te["mfe"], q / 10)) for q in range(1, 10)],
        "bars_deciles": [float(np.quantile(tr_te["bars_held"], q / 10)) for q in range(1, 10)],
    }

    with open(os.path.join(HERE, "RESEARCH.json"), "w") as fh:
        json.dump(out, fh, separators=(",", ":"), default=float)
    print("wrote RESEARCH.json in %.0fs" % (time.time() - t0))
    return out


if __name__ == "__main__":
    main()
