"""GB-Ranges engine: PO3 lattice, level set, swing detection.

See SPEC.md for the derivation of the lattice from the source PDF.
"""
import numpy as np

# The 20 distinct Goldbach percentages. 100 is the same line as 0 of the block
# above, so it is not listed separately.
LEVELS = np.array(
    [0, 3, 7, 11, 17, 23, 29, 35, 41, 47, 50, 53, 59, 65, 71, 77, 83, 89, 93, 97],
    dtype=np.float64,
)

LEVEL_NAME = {
    0: "range extreme", 3: "internal rng liq", 7: "LLOD", 11: "internal rng liq",
    17: "GIP", 23: "flow outer", 29: "flow middle", 35: "flow inner",
    41: "ext rebalance liq", 47: "int rebalance liq", 50: "equilibrium",
    53: "int rebalance liq", 59: "ext rebalance liq", 65: "flow inner",
    71: "flow middle", 77: "flow outer", 83: "GIP", 89: "internal rng liq",
    93: "LLOD", 97: "internal rng liq",
}

LAYERS = {
    "liquidity_lo": (0.0, 11.0),
    "flow_lo": (23.0, 35.0),
    "rebalance": (41.0, 59.0),
    "flow_hi": (65.0, 77.0),
    "liquidity_hi": (89.0, 100.0),
}

PO3 = [81, 243, 729, 2187, 6561]


def block_pct(price, R, phase=0.0):
    """Position within the PO3 block, in percent [0,100).

    phase shifts the lattice origin, in percentage points of the block. The
    true lattice is phase=0.
    """
    shifted = price - R * phase / 100.0
    return np.mod(shifted, R) / R * 100.0


def on_level(pct, tol):
    """True where pct is within tol (percentage points) of any GB level.

    Wraps at 0/100 -- level 0 catches pct just under 100 as well.
    """
    d = np.abs(pct[:, None] - LEVELS[None, :])
    d = np.minimum(d, 100.0 - d)          # circular distance
    return (d <= tol).any(axis=1)


def level_index(pct, tol):
    """Index into LEVELS of the nearest GB level within tol, else -1."""
    d = np.abs(pct[:, None] - LEVELS[None, :])
    d = np.minimum(d, 100.0 - d)
    j = np.argmin(d, axis=1)
    best = d[np.arange(len(pct)), j]
    return np.where(best <= tol, j, -1)


def coverage(tol):
    """Fraction of a block covered by the level set at this tolerance.

    Accounts for overlap between adjacent levels (47/50/53 collide at tol>=1.5).
    """
    grid = np.linspace(0, 100, 100001, endpoint=False)
    return on_level(grid, tol).mean()


def swings(high, low, k):
    """Fractal pivots of strength k.

    A swing high is a bar whose high is strictly greater than the highs of the
    k bars on each side. Swing lows mirror. Returns (idx_high, idx_low).

    Uses a strided max/min so it stays O(n*k) without a Python loop over bars.
    """
    n = len(high)
    if n < 2 * k + 1:
        return np.array([], int), np.array([], int)

    # rolling max/min over the full 2k+1 window, excluding the centre bar
    hi_nb = np.full(n, -np.inf)
    lo_nb = np.full(n, np.inf)
    for off in range(1, k + 1):
        hi_nb[off:] = np.maximum(hi_nb[off:], high[:-off])
        hi_nb[:-off] = np.maximum(hi_nb[:-off], high[off:])
        lo_nb[off:] = np.minimum(lo_nb[off:], low[:-off])
        lo_nb[:-off] = np.minimum(lo_nb[:-off], low[off:])

    valid = np.zeros(n, bool)
    valid[k:n - k] = True
    ih = np.flatnonzero(valid & (high > hi_nb))
    il = np.flatnonzero(valid & (low < lo_nb))
    return ih, il


def zscore(observed, null_samples):
    """z of observed against a null sample distribution."""
    mu = np.mean(null_samples)
    sd = np.std(null_samples, ddof=1)
    if sd == 0:
        return float("nan")
    return (observed - mu) / sd


def binom_z(hits, n, p):
    """z of a hit count against a binomial expectation."""
    if n == 0:
        return float("nan")
    return (hits - n * p) / np.sqrt(n * p * (1 - p))
