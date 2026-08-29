"""Performance, risk and overfitting statistics for a trade series.

Everything is built off a daily P&L series rather than per-trade averages,
because a per-trade mean says nothing about how the money arrives. Trades are
sized at constant fractional risk -- RISK_FRAC of a nominal account per trade,
position sized to the stop -- so a trade's contribution is its R multiple times
a fixed dollar amount, and the resulting curve is non-compounding. That keeps
the statistics readable: a Sharpe computed on a compounding curve mixes the
edge with the sizing rule.

The overfitting statistics matter more than the performance ones here. A search
over tens of thousands of configurations produces a best result whose Sharpe is
inflated by construction, and the deflated Sharpe ratio is what says by how
much.
"""
import numpy as np

ACCOUNT = 100_000.0        # nominal account, USD
RISK_FRAC = 0.01           # risked per trade
POINT_VALUE = 20.0         # NQ, USD per index point
TRADING_DAYS = 252.0
EULER = 0.5772156649015329


# ------------------------------------------------------------------ helpers
def ts_to_datetime64(ts):
    """bars.npz packs time as YYYYMMDDHHMMSS integers."""
    ts = np.asarray(ts, np.int64)
    y = ts // 10_000_000_000
    mo = (ts // 100_000_000) % 100
    d = (ts // 1_000_000) % 100
    hh = (ts // 10_000) % 100
    mi = (ts // 100) % 100
    out = (y.astype("datetime64[Y]") - 1970).astype("datetime64[Y]")
    out = out.astype("datetime64[M]") + (mo - 1)
    out = out.astype("datetime64[D]") + (d - 1)
    return out.astype("datetime64[m]") + hh * 60 + mi


def norm_cdf(x):
    from math import erf, sqrt
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def norm_ppf(p):
    """Inverse normal CDF (Acklam's rational approximation)."""
    if not 0.0 < p < 1.0:
        return float("nan")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = np.sqrt(-2 * np.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
               ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > ph:
        q = np.sqrt(-2 * np.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
           (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


# --------------------------------------------------------------- daily curve
def daily_pnl(r, exit_dt):
    """Aggregate per-trade R into a calendar-daily P&L series in USD.

    Days with no closed trade are zero, not missing, because a flat day is
    still a day of risk-taking capacity and dropping it inflates Sharpe.
    """
    dollars = np.asarray(r, float) * (ACCOUNT * RISK_FRAC)
    days = np.asarray(exit_dt, "datetime64[D]")
    if not len(days):
        return np.array([], "datetime64[D]"), np.array([])
    lo, hi = days.min(), days.max()
    grid = np.arange(lo, hi + np.timedelta64(1, "D"), dtype="datetime64[D]")
    idx = (days - lo).astype(int)
    pnl = np.bincount(idx, weights=dollars, minlength=len(grid))
    # weekends carry no trades; drop them so the day count is a trading count
    dow = (grid.astype("datetime64[D]").astype(int) + 4) % 7
    keep = dow < 5
    return grid[keep], pnl[keep]


def drawdown(equity):
    """Depth and duration of the worst peak-to-trough excursion."""
    eq = np.concatenate([[0.0], np.asarray(equity, float)])
    peak = np.maximum.accumulate(eq)
    dd = peak - eq
    i = int(np.argmax(dd))
    depth = float(dd[i])
    # duration: bars from the peak preceding i until equity recovers it
    j = int(np.argmax(eq[:i + 1] >= peak[i])) if i > 0 else 0
    rec = np.flatnonzero(eq[i:] >= peak[i])
    end = i + int(rec[0]) if len(rec) else len(eq) - 1
    return {"depth": depth, "start": j, "trough": i, "end": end,
            "duration": int(end - j),
            "recovered": bool(len(rec) > 0),
            "series": dd[1:]}


def perf(r, exit_dt, label=""):
    """The full performance block for one trade series."""
    r = np.asarray(r, float)
    if len(r) < 20:
        return None
    grid, pnl = daily_pnl(r, exit_dt)
    eq = np.cumsum(pnl)
    dd = drawdown(eq)
    n_days = max(1, len(grid))
    years = n_days / TRADING_DAYS

    mu_d, sd_d = pnl.mean(), pnl.std(ddof=1)
    downside = pnl[pnl < 0]
    sd_dn = downside.std(ddof=1) if len(downside) > 1 else np.nan
    ann_ret = mu_d * TRADING_DAYS
    sharpe = (mu_d / sd_d) * np.sqrt(TRADING_DAYS) if sd_d > 0 else np.nan
    sortino = (mu_d / sd_dn) * np.sqrt(TRADING_DAYS) if sd_dn and sd_dn > 0 else np.nan
    calmar = ann_ret / dd["depth"] if dd["depth"] > 0 else np.nan

    wins, losses = r[r > 0], r[r <= 0]
    sd_r = r.std(ddof=1)
    # higher moments of the daily series, needed by the deflated Sharpe
    z = (pnl - mu_d) / sd_d if sd_d > 0 else pnl * 0
    skew = float((z ** 3).mean())
    kurt = float((z ** 4).mean())

    return {
        "label": label,
        "n_trades": int(len(r)),
        "n_days": int(n_days),
        "years": float(years),
        "trades_per_year": float(len(r) / years) if years > 0 else np.nan,
        "win_rate": float((r > 0).mean()),
        "exp_r": float(r.mean()),
        "sd_r": float(sd_r),
        "t": float(r.mean() / (sd_r / np.sqrt(len(r)))) if sd_r > 0 else np.nan,
        "total_usd": float(eq[-1]) if len(eq) else 0.0,
        "ann_usd": float(ann_ret),
        "ann_pct": float(ann_ret / ACCOUNT * 100),
        "sharpe": float(sharpe),
        "sortino": float(sortino),
        "calmar": float(calmar),
        "max_dd_usd": float(dd["depth"]),
        "max_dd_pct": float(dd["depth"] / ACCOUNT * 100),
        "dd_days": int(dd["duration"]),
        "dd_recovered": dd["recovered"],
        "profit_factor": float(wins.sum() / abs(losses.sum()))
                         if len(losses) and losses.sum() < 0 else float("inf"),
        "payoff": float(wins.mean() / abs(losses.mean()))
                  if len(wins) and len(losses) and losses.mean() < 0 else np.nan,
        "skew_daily": skew,
        "kurt_daily": kurt,
        "best_day": float(pnl.max()) if len(pnl) else np.nan,
        "worst_day": float(pnl.min()) if len(pnl) else np.nan,
        "pct_days_traded": float((pnl != 0).mean()) if len(pnl) else np.nan,
        "equity": [round(float(v), 1) for v in eq[::max(1, len(eq) // 400)]],
        "equity_dates": [str(d) for d in grid[::max(1, len(grid) // 400)]],
        "dd_series": [round(float(v), 1) for v in dd["series"][::max(1, len(eq) // 400)]],
        "_daily": pnl,
    }


# --------------------------------------------------------------- overfitting
def deflated_sharpe(sharpe_ann, n_obs, n_trials, skew, kurt, var_sharpe_trials=None):
    """Bailey & Lopez de Prado's deflated Sharpe ratio.

    A search over many configurations produces a maximum Sharpe that is high by
    construction even when no edge exists. This asks whether the observed
    Sharpe beats the maximum a null search of the same width would be expected
    to reach, correcting for the non-normality of the return series.
    Returns the probability that the true Sharpe exceeds zero.
    """
    if not np.isfinite(sharpe_ann) or n_obs < 30 or n_trials < 2:
        return {"dsr": float("nan"), "sr0": float("nan")}
    sr = sharpe_ann / np.sqrt(TRADING_DAYS)          # per-observation
    v = var_sharpe_trials if var_sharpe_trials else 1.0 / n_obs
    e1 = norm_ppf(1 - 1.0 / n_trials)
    e2 = norm_ppf(1 - 1.0 / (n_trials * np.e))
    sr0 = np.sqrt(v) * ((1 - EULER) * e1 + EULER * e2)
    denom = np.sqrt(max(1e-12, 1 - skew * sr + (kurt - 1) / 4.0 * sr * sr))
    z = (sr - sr0) * np.sqrt(max(1, n_obs - 1)) / denom
    return {"dsr": float(norm_cdf(z)), "sr0_ann": float(sr0 * np.sqrt(TRADING_DAYS)),
            "sr_ann": float(sharpe_ann), "z": float(z), "n_trials": int(n_trials)}


def pbo(matrix, n_splits=10, seed=5):
    """Probability of backtest overfitting, by combinatorially symmetric CV.

    `matrix` is (n_periods, n_configs) of P&L. The series is cut into n_splits
    blocks; every balanced split of those blocks into in-sample and
    out-of-sample halves is formed; the config that ranks first in-sample has
    its out-of-sample rank recorded. PBO is how often that winner lands in the
    bottom half out of sample -- the rate at which selection picks a loser.
    """
    from itertools import combinations
    M = np.asarray(matrix, float)
    if M.ndim != 2 or M.shape[1] < 3 or M.shape[0] < n_splits * 2:
        return {"pbo": float("nan"), "n_splits": 0, "n_configs": int(M.shape[1] if M.ndim == 2 else 0)}
    n_splits -= n_splits % 2
    blocks = np.array_split(np.arange(M.shape[0]), n_splits)
    half = n_splits // 2
    combos = list(combinations(range(n_splits), half))
    if len(combos) > 400:
        rng = np.random.default_rng(seed)
        combos = [combos[i] for i in rng.choice(len(combos), 400, replace=False)]

    logits, below = [], 0
    for cin in combos:
        cout = [b for b in range(n_splits) if b not in cin]
        idx_in = np.concatenate([blocks[b] for b in cin])
        idx_out = np.concatenate([blocks[b] for b in cout])
        def sr(a):
            m, s = a.mean(axis=0), a.std(axis=0, ddof=1)
            return np.where(s > 0, m / np.where(s > 0, s, 1), -np.inf)
        s_in, s_out = sr(M[idx_in]), sr(M[idx_out])
        best = int(np.argmax(s_in))
        # rank of the in-sample winner among out-of-sample results
        rank = float((s_out < s_out[best]).sum()) / max(1, len(s_out) - 1)
        rank = min(max(rank, 1e-6), 1 - 1e-6)
        logits.append(np.log(rank / (1 - rank)))
        if rank < 0.5:
            below += 1
    return {"pbo": float(below / len(combos)), "n_splits": n_splits,
            "n_configs": int(M.shape[1]), "n_combos": len(combos),
            "median_logit": float(np.median(logits))}


def mc_drawdown(r, n_sim=5000, seed=11):
    """Drawdown distribution under random reordering of the same trades.

    Order is the one thing a backtest cannot claim to have predicted, so the
    realised drawdown is a single draw from this distribution. The 95th
    percentile is the number to size against.
    """
    r = np.asarray(r, float)
    if len(r) < 30:
        return {}
    rng = np.random.default_rng(seed)
    dollars = r * (ACCOUNT * RISK_FRAC)
    dds = np.empty(n_sim)
    for i in range(n_sim):
        eq = np.cumsum(rng.permutation(dollars))
        dds[i] = (np.maximum.accumulate(np.concatenate([[0.0], eq])) -
                  np.concatenate([[0.0], eq])).max()
    return {"median": float(np.median(dds)), "p95": float(np.quantile(dds, 0.95)),
            "p99": float(np.quantile(dds, 0.99)), "max": float(dds.max()),
            "realised": float((np.maximum.accumulate(np.concatenate([[0.0], np.cumsum(dollars)])) -
                               np.concatenate([[0.0], np.cumsum(dollars)])).max())}
