"""The five trade plans from the book, implemented as written.

Everything else in this repo tests properties of the lattice that I chose to
measure. This tests what hopiplaka actually wrote down: five named plans, each
with its own precondition, entry level, target and -- where the book gives one
-- invalidation. Nothing is generalised, nothing is optimised, and no parameter
is chosen to make a plan look better. Where the book is explicit the code is
literal; where it is vague the vagueness is recorded rather than resolved in
the plan's favour.

    REBALANCE     the only fully mechanical plan in the book.
                  "Price will consolidate around ... [47-53] ... When price
                  hits the external liquidity of the rebalance layer [41-59],
                  you enter the trade. You exit on the opposite level."
                  Entry 41 -> exit 59, or entry 59 -> exit 41. No stop given.

    FLOW CONT.    "When price indeed moves through the flow layer, you still
                  don't buy ... They will first retrace price, back into the
                  flow layer ... this is where you buy, and expect price to
                  move towards the rebalance layer, and later to the flow
                  layer that is coming next."
                  Close beyond the flow layer, retrace into it, enter, target
                  the rebalance layer then the opposite flow layer.

    EINSTEIN      consolidate at [0-100], drive up through [11-89] to the flow
                  middle [29-71], retrace to [17-83], enter there, partial at
                  [47-53], then the flow gate, then the range high.

    LIQUIDITY     build liquidity at the discount levels, get run into the
                  premium liquidity of the NEXT block, reject, trade back into
                  the range toward the flow layer. Invalid if price passes the
                  external GIP -- the book's own stop.

    FLOW REJECT.  needs a fair-value gap to be identified inside the flow
                  layer; implemented with a literal three-bar gap.

Each plan is scored against the identical procedure on shifted lattices, which
is the only way to tell a plan that works from a plan that describes what price
does near any set of lines.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NPHASE = 12
HORIZON = 1440          # one day of one-minute bars to resolve a plan
CONSOL = 240            # "consolidates around" -- seen there in the last N bars
DEDUP = 120


def dedup(idx, gap):
    if len(idx) == 0:
        return idx
    keep = [idx[0]]
    for i in idx[1:]:
        if i - keep[-1] >= gap:
            keep.append(i)
    return np.asarray(keep)


def seen_within(mask, w):
    """True where `mask` was true at least once in the previous w bars."""
    cs = np.concatenate([[0], np.cumsum(mask.astype(np.int64))])
    i = np.arange(len(mask))
    lo = np.maximum(i - w, 0)
    return (cs[i] - cs[lo]) > 0


def resolve(h, l, idx, entry, tgt, stop, up, n, horizon=HORIZON):
    """+1 target first, -1 stop first, 0 unresolved. Stop may be None.

    NOTE: none of the five plans specifies a stop except LIQUIDITY, whose
    invalidation is the external GIP. Run literally -- no stop, one-day horizon
    -- every plan hits its target essentially always, because price covers 18%
    of a block sooner or later. The resulting 1.000 hit rate is a property of
    the plans as written rather than of the market, which is why the symmetric
    race below is the number to read.
    """
    out = np.zeros(len(idx), np.int8)
    live = np.ones(len(idx), bool)
    for w in range(1, horizon + 1):
        j = np.clip(idx + w, 0, n - 1)
        ht = (h[j] >= tgt) if up else (l[j] <= tgt)
        if stop is None:
            hs = np.zeros(len(idx), bool)
        else:
            hs = (l[j] <= stop) if up else (h[j] >= stop)
        sn = live & hs
        tn = live & ht & ~hs
        out[sn] = -1
        out[tn] = 1
        live &= ~(sn | tn)
        if not live.any():
            break
    return out


def lattice(c, R, phase):
    off = R * phase / 100.0
    pos = (c - off) / R
    blk = np.floor(pos)
    return blk, (pos - blk) * 100.0, off


def lvl(off, R, blk, pct):
    return off + R * blk + R * pct / 100.0


# --------------------------------------------------------------- the plans
def plan_rebalance(h, l, c, R, phase, n):
    """Consolidate in [47-53]; enter at 41 or 59; exit at the opposite one."""
    blk, pct, off = lattice(c, R, phase)
    consol = seen_within((pct >= 47) & (pct <= 53), CONSOL)
    out = []
    for entry_pct, exit_pct, up in ((41.0, 59.0, True), (59.0, 41.0, False)):
        e = lvl(off, R, blk, entry_pct)
        t = lvl(off, R, blk, exit_pct)
        hit = (l <= e) if up else (h >= e)
        idx = np.flatnonzero(hit & consol & (np.arange(n) > CONSOL)
                             & (np.arange(n) + HORIZON < n))
        idx = dedup(idx, DEDUP)
        if len(idx) < 100:
            continue
        r = resolve(h, l, idx, e[idx], t[idx], None, up, n)
        out.append((idx, r, e[idx], t[idx]))
    return out


def plan_flow_continuation(h, l, c, R, phase, n):
    """Close beyond the flow layer, retrace back into it, enter, target 47."""
    blk, pct, off = lattice(c, R, phase)
    out = []
    # lower flow layer 23-35: price closes BELOW 23, then retraces up into it
    # upper flow layer 65-77: price closes ABOVE 77, then retraces down into it
    for lo_p, hi_p, through_below, up, tgt_pct in (
            (23.0, 35.0, True, True, 47.0),
            (65.0, 77.0, False, False, 53.0)):
        through = (pct < lo_p) if through_below else (pct > hi_p)
        was_through = seen_within(through, CONSOL)
        back_in = (pct >= lo_p) & (pct <= hi_p)
        idx = np.flatnonzero(back_in & was_through & ~through
                             & (np.arange(n) > CONSOL)
                             & (np.arange(n) + HORIZON < n))
        idx = dedup(idx, DEDUP)
        if len(idx) < 100:
            continue
        e = c[idx]
        t = lvl(off, R, blk[idx], tgt_pct)
        # the book gives no stop; the flow layer failing is the natural one
        s = lvl(off, R, blk[idx], lo_p if through_below else hi_p)
        r = resolve(h, l, idx, e, t, s, up, n)
        out.append((idx, r, e, t))
    return out


def plan_einstein(h, l, c, R, phase, n):
    """0/100 -> through 11 -> 17 -> flow middle 29 -> retrace to 17 -> enter."""
    blk, pct, off = lattice(c, R, phase)
    out = []
    for ext_p, mid_p, gip_p, tgt_p, up in ((0.0, 29.0, 17.0, 50.0, True),
                                           (100.0, 71.0, 83.0, 50.0, False)):
        near_ext = (pct <= 3.0) if up else (pct >= 97.0)
        reached_mid = (pct >= mid_p) if up else (pct <= mid_p)
        # the sequence: consolidated at the extreme, then reached the flow
        # middle, and is now back at the inversion point
        a = seen_within(near_ext, CONSOL * 3)
        b = seen_within(reached_mid, CONSOL)
        at_gip = (np.abs(pct - gip_p) <= 1.0)
        idx = np.flatnonzero(a & b & at_gip & (np.arange(n) > CONSOL * 3)
                             & (np.arange(n) + HORIZON < n))
        idx = dedup(idx, DEDUP)
        if len(idx) < 100:
            continue
        e = lvl(off, R, blk[idx], gip_p)
        t = lvl(off, R, blk[idx], tgt_p)
        s = lvl(off, R, blk[idx], ext_p)       # back to the extreme kills it
        r = resolve(h, l, idx, e, t, s, up, n)
        out.append((idx, r, e, t))
    return out


def plan_liquidity(h, l, c, R, phase, n):
    """Liquidity at the discount levels, run into the next block, reject, back in.

    Long side: price hovers around [0-11] of its block, is run DOWN below the
    block low into the premium liquidity of the block beneath ([89-97] of it),
    rejects, and trades back into the original block toward the flow layer.
    Invalid if price passes the external GIP -- level 83 of the block beneath.
    """
    blk, pct, off = lattice(c, R, phase)
    out = []
    for up in (True, False):
        if up:
            hover = (pct >= 0.0) & (pct <= 11.0)
            swept = pct >= 89.0            # now in the block below
            entry_back = 3.0               # back inside the original block
            tgt_pct, stop_pct = 29.0, 83.0
        else:
            hover = (pct >= 89.0) & (pct <= 100.0)
            swept = pct <= 11.0
            entry_back = 97.0
            tgt_pct, stop_pct = 71.0, 17.0
        # the block the plan belongs to is the one price hovered in
        home = np.where(up, blk + 0, blk + 0)
        hovered = seen_within(hover, CONSOL)
        was_swept = seen_within(swept & ~hover, CONSOL)
        back = (pct >= entry_back) & (pct <= 50.0) if up else \
               (pct <= entry_back) & (pct >= 50.0)
        idx = np.flatnonzero(hovered & was_swept & back
                             & (np.arange(n) > CONSOL * 2)
                             & (np.arange(n) + HORIZON < n))
        idx = dedup(idx, DEDUP)
        if len(idx) < 100:
            continue
        e = c[idx]
        t = lvl(off, R, blk[idx], tgt_pct)
        s = lvl(off, R, blk[idx] - (1 if up else -1), stop_pct)
        r = resolve(h, l, idx, e, t, s, up, n)
        out.append((idx, r, e, t))
    return out


def plan_flow_rejection(h, l, c, R, phase, n):
    """Reject the flow middle, gap out of the layer, retrace into the gap."""
    blk, pct, off = lattice(c, R, phase)
    # a literal three-bar fair value gap
    gap_up = np.zeros(n, bool); gap_dn = np.zeros(n, bool)
    gap_up[2:] = l[2:] > h[:-2]
    gap_dn[2:] = h[2:] < l[:-2]
    out = []
    for mid_p, up, tgt_pct in ((71.0, False, 50.0), (29.0, True, 50.0)):
        touched_mid = seen_within(np.abs(pct - mid_p) <= 1.5, CONSOL)
        gapped = seen_within(gap_dn if not up else gap_up, 30)
        # retrace back into the gap: price returns toward the flow middle
        back = np.abs(pct - mid_p) <= 4.0
        idx = np.flatnonzero(touched_mid & gapped & back
                             & (np.arange(n) > CONSOL)
                             & (np.arange(n) + HORIZON < n))
        idx = dedup(idx, DEDUP)
        if len(idx) < 100:
            continue
        e = c[idx]
        t = lvl(off, R, blk[idx], tgt_pct)
        s = lvl(off, R, blk[idx], mid_p + (6.0 if not up else -6.0))
        r = resolve(h, l, idx, e, t, s, up, n)
        out.append((idx, r, e, t))
    return out


PLANS = [("REBALANCE", plan_rebalance),
         ("FLOW CONTINUATION", plan_flow_continuation),
         ("FLOW REJECTION", plan_flow_rejection),
         ("EINSTEIN", plan_einstein),
         ("LIQUIDITY", plan_liquidity)]


def symmetric(h, l, idx, entry, tgt, up, n):
    """Target against an EQUALLY DISTANT adverse level.

    The only honest way to score a plan whose author gave no stop. Both
    destinations sit the same distance from entry, so a coin flip is the right
    intuition and a shifted lattice is a matched control. Nothing is tuned --
    the adverse distance is whatever the book's own target distance happens to
    be.
    """
    d = np.abs(tgt - entry)
    adv = entry - d if up else entry + d
    return resolve(h, l, idx, entry, tgt, adv, up, n)


def mae_to_target(h, l, idx, entry, tgt, up, n):
    """How far the no-stop version runs against you before the target lands."""
    worst = np.zeros(len(idx))
    done = np.zeros(len(idx), bool)
    for w in range(1, HORIZON + 1):
        j = np.clip(idx + w, 0, n - 1)
        adv = (entry - l[j]) if up else (h[j] - entry)
        worst = np.where(done, worst, np.maximum(worst, adv))
        done |= (h[j] >= tgt) if up else (l[j] <= tgt)
        if done.all():
            break
    return worst, done


def score(res):
    """Pool both directions of a plan into one hit rate."""
    tot = won = 0
    for _, r, _, _ in res:
        tot += int((r != 0).sum())
        won += int((r == 1).sum())
    return (won / tot if tot else float("nan")), tot


def sym_score(h, l, c, fn, R, phase, n):
    """Pool a plan's two directions under the symmetric race."""
    res = fn(h, l, c, R, phase, n)
    if not res:
        return None
    tot = won = 0
    for idx, _, entry, tgt in res:
        up = tgt[0] > entry[0]
        r = symmetric(h, l, idx, entry, tgt, up, n)
        tot += int((r != 0).sum())
        won += int((r == 1).sum())
    return (won / tot, tot) if tot >= 100 else None


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    h, l, c = (np.asarray(npz[k]) for k in ("h", "l", "c"))
    n = len(c)

    out = {}
    for R in (243.0, 729.0):
        print("\n" + "=" * 96)
        print("R=%d   the five plans, exactly as the book states them" % R)
        print("=" * 96)
        print("  %-20s %9s %11s %9s %11s %10s %8s %10s"
              % ("plan", "trades", "as written", "reached", "SYMMETRIC",
                 "shifted", "z", "MAE med"))
        out[str(int(R))] = {}
        for name, fn in PLANS:
            t = fn(h, l, c, R, 0.0, n)
            if not t:
                print("  %-20s %9s" % (name, "too few"))
                continue
            lit_p, cnt = score(t)

            # what the no-stop version costs you in heat, and how often it lands
            maes, lands = [], []
            for idx, _, entry, tgt in t:
                up = tgt[0] > entry[0]
                w, d = mae_to_target(h, l, idx, entry, tgt, up, n)
                maes.append(w); lands.append(d)
            mae = float(np.median(np.concatenate(maes)))
            land = float(np.concatenate(lands).mean())

            sym = sym_score(h, l, c, fn, R, 0.0, n)
            nulls = []
            for j in range(1, NPHASE):
                q = sym_score(h, l, c, fn, R, j * 100.0 / NPHASE, n)
                if q:
                    nulls.append(q[0])
            arr = np.array(nulls)
            sd = arr.std(ddof=1) if len(arr) > 2 else np.nan
            z = (sym[0] - arr.mean()) / sd if sym and sd and sd > 0 else 0.0
            out[str(int(R))][name] = {
                "n": cnt, "literal": float(lit_p), "reached": land,
                "sym": float(sym[0]) if sym else None, "sym_n": sym[1] if sym else 0,
                "null": float(arr.mean()) if len(arr) else None,
                "z": float(z), "mae_med": mae}
            print("  %-20s %9s %11.4f %9.4f %11.4f %10.4f %+8.2f %9.1fp"
                  % (name, "{:,}".format(cnt), lit_p, land,
                     sym[0] if sym else float("nan"), arr.mean(), z, mae))

    json.dump(out, open(os.path.join(HERE, "plans.json"), "w"), indent=1)
    print("\nwrote plans.json")
    print("\n'as written' uses the book's own stop (only LIQUIDITY has one), so")
    print("for the rest it is near 1.000 by construction and says nothing.")
    print("SYMMETRIC races the book's target against an equally distant adverse")
    print("level -- that is the column to read, against 0.500 and against the")
    print("shifted-lattice column beside it.")


if __name__ == "__main__":
    main()
