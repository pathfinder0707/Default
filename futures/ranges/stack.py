"""The two filters that measured large, stacked and scored in points.

Two findings in this repo produced spreads far too big to be noise:

  30-minute close at a level   +21.6pp between close-through and close-back,
                               monotone from 3m to 30m
  quiet arrival                55.4% vs a 47.1% baseline, +11.9pp

Both were only ever scored as directional probabilities -- P(reaches EQ before
the opposite level). Neither was stacked with the other, and neither was ever
converted into net points after cost with a real stop. A 61% directional hit
rate is worthless if the winners are half the size of the losers, and that
question has not been asked once.

So: take a 30-minute bar that straddles a Goldbach level, split on where it
closes, stack the arrival filters, and trade it with a fixed ATR stop and
target on one-minute bars.

Rules that have to hold for anything reported here:
  - cost 0.45 points a round turn, same as everywhere else
  - if stop and target are both inside one minute bar, the stop fills
  - LONG and SHORT setups are scored separately and BOTH must pay; a real
    effect at a level is a mirror image, an artifact picks a side
  - day-clustered bootstrap, discovery/validation at 2019
  - every cell rerun on shifted lattices, so the question is not "does this
    make money" but "does it make money BECAUSE of Goldbach"
"""
import json
import os

import numpy as np

import gbr

HERE = os.path.dirname(os.path.abspath(__file__))
COST = 0.45
SPLIT = 2019
NBOOT = 2000
MAXHOLD = 240          # one-minute bars; four hours
PHASES = (0.0, 12.5, 25.0, 37.5, 50.0, 62.5, 75.0, 87.5)


def htf_index(date, hh, mm, tf):
    """Last 1m bar index of each tf-minute bucket, plus the bucket's o/h/l/c."""
    key = date.astype(np.int64) * 10000 + (hh.astype(np.int64) * 60
                                           + mm.astype(np.int64)) // tf
    change = np.empty(len(key), bool)
    change[0] = True
    change[1:] = key[1:] != key[:-1]
    start = np.flatnonzero(change)
    end = np.append(start[1:] - 1, len(key) - 1)
    return start, end


def bucket_ohlc(o, h, l, c, v, start, end):
    n = len(start)
    bo = o[start]
    bc = c[end]
    bh = np.empty(n); bl = np.empty(n); bv = np.empty(n)
    for i in range(n):
        a, b = start[i], end[i] + 1
        bh[i] = h[a:b].max(); bl[i] = l[a:b].min(); bv[i] = v[a:b].sum()
    return bo, bh, bl, bc, bv


def roll_med(x, w):
    """Rolling median, causal, via a coarse but fast geometric proxy."""
    out = np.empty(len(x))
    out[:] = np.nan
    for i in range(w, len(x)):
        out[i] = np.median(x[i - w:i])
    return out


def atr(bh, bl, bc, w=20):
    pc = np.roll(bc, 1); pc[0] = bc[0]
    tr = np.maximum(bh - bl, np.maximum(np.abs(bh - pc), np.abs(bl - pc)))
    a = np.full(len(tr), np.nan)
    csum = np.cumsum(tr)
    a[w:] = (csum[w:] - csum[:-w]) / w
    return a


def race(h, l, entry_i, side, entry_px, stop_px, tgt_px):
    """Forward race on one-minute bars. Stop wins ties inside a bar."""
    n = len(h)
    m = len(entry_i)
    pnl = np.full(m, np.nan)
    for k in range(m):
        a = entry_i[k]
        b = min(a + MAXHOLD, n - 1)
        if b <= a:
            continue
        seg_h = h[a:b + 1]; seg_l = l[a:b + 1]
        if side[k] > 0:
            hs = np.flatnonzero(seg_l <= stop_px[k])
            ht = np.flatnonzero(seg_h >= tgt_px[k])
        else:
            hs = np.flatnonzero(seg_h >= stop_px[k])
            ht = np.flatnonzero(seg_l <= tgt_px[k])
        is_ = hs[0] if len(hs) else 10 ** 9
        it = ht[0] if len(ht) else 10 ** 9
        if is_ == it == 10 ** 9:
            px = h[b] * 0 + (l[b] + h[b]) / 2.0     # flat exit at horizon
            pnl[k] = side[k] * (px - entry_px[k])
        elif is_ <= it:
            pnl[k] = side[k] * (stop_px[k] - entry_px[k])
        else:
            pnl[k] = side[k] * (tgt_px[k] - entry_px[k])
    return pnl - COST


def boot(pnl, days, rng):
    u, inv = np.unique(days, return_inverse=True)
    nd = len(u)
    if nd < 5:
        return float("nan"), float("nan")
    s = np.bincount(inv, weights=pnl, minlength=nd)
    cnt = np.bincount(inv, minlength=nd).astype(float)
    pick = rng.integers(0, nd, size=(NBOOT, nd))
    bs = s[pick].sum(1) / np.maximum(cnt[pick].sum(1), 1)
    return tuple(np.percentile(bs, [2.5, 97.5]))


def build_events(px_close_prev, bh, bl, bc, R, phase):
    """30m bars that straddle a GB level, with the level and approach side."""
    lv = gbr.LEVELS * R / 100.0
    base = np.floor((bl - R * phase / 100.0) / R) * R + R * phase / 100.0
    # candidate levels in this block and the one above
    cand = np.concatenate([base[:, None] + lv[None, :],
                           base[:, None] + R + lv[None, :]], axis=1)
    inside = (cand >= bl[:, None]) & (cand <= bh[:, None])
    # nearest straddled level to the bar's close
    d = np.where(inside, np.abs(cand - bc[:, None]), np.inf)
    j = np.argmin(d, axis=1)
    ok = np.isfinite(d[np.arange(len(bc)), j])
    L = cand[np.arange(len(bc)), j]
    return ok, L


def main():
    npz = np.load(os.path.join(HERE, "bars.npz"))
    o, h, l, c, v = (np.asarray(npz[k]).astype(np.float64)
                     for k in ("o", "h", "l", "c", "v"))
    date = np.asarray(npz["date"]); hh = np.asarray(npz["hh"])
    mm = np.asarray(npz["mm"]); sess = np.asarray(npz["sess"])

    start, end = htf_index(date, hh, mm, 30)
    bo, bh, bl, bc, bv = bucket_ohlc(o, h, l, c, v, start, end)
    a30 = atr(bh, bl, bc, 20)
    vmed = roll_med(bv, 40)
    rng_bar = bh - bl
    bday = date[end]
    byr = bday // 10000
    bsess = sess[end]
    prev_c = np.roll(bc, 1); prev_c[0] = bc[0]

    print("%s 30-minute bars, %s -> %s\n"
          % ("{:,}".format(len(bc)), bday[0], bday[-1]))

    results = {}
    for R in (243.0, 729.0):
        for phase in PHASES:
            ok, L = build_events(prev_c, bh, bl, bc, R, phase)
            good = ok & np.isfinite(a30) & np.isfinite(vmed) & (a30 > 0)
            # approach from below or above, judged by the PREVIOUS close
            up = prev_c < L
            dn = prev_c > L
            through_up = up & (bc > L)      # closed through, upward
            back_up = up & (bc <= L)        # closed back below, rejected
            through_dn = dn & (bc < L)
            back_dn = dn & (bc >= L)

            quiet = (rng_bar <= 0.8 * a30) & (bv <= vmed)
            rth = (bsess == 1) if bsess.dtype != bool else bsess

            setups = {
                "break_up":   (through_up, +1),
                "break_dn":   (through_dn, -1),
                "reject_up":  (back_up, -1),     # rejected at level, go short
                "reject_dn":  (back_dn, +1),
            }
            for filt_name, filt in (("all", np.ones(len(bc), bool)),
                                    ("quiet", quiet),
                                    ("rth", rth),
                                    ("quiet+rth", quiet & rth)):
                for stop_a, tgt_a in ((0.75, 1.5), (1.0, 1.0), (0.75, 2.25)):
                    for name, (m0, side_s) in setups.items():
                        m = good & m0 & filt
                        # entry on the first 1m bar after the signal bar
                        ei = end[m] + 1
                        m_idx = np.flatnonzero(m)
                        keep = ei < len(c)
                        ei = ei[keep]; m_idx = m_idx[keep]
                        if len(ei) < 300:
                            continue
                        px = c[end[m_idx]]
                        aa = a30[m_idx]
                        s = np.full(len(ei), float(side_s))
                        stop = px - s * stop_a * aa
                        tgt = px + s * tgt_a * aa
                        pnl = race(h, l, ei, s, px, stop, tgt)
                        gd = np.isfinite(pnl)
                        key = (int(R), phase, filt_name, stop_a, tgt_a, name)
                        results[key] = (pnl[gd], bday[m_idx][gd],
                                        byr[m_idx][gd])
            print("  R=%d phase=%.1f done" % (R, phase))

    # ---- report: true lattice only, both sides required ------------------
    rngen = np.random.default_rng(3)
    print()
    print("=" * 104)
    print("TRUE LATTICE -- a setup only counts if its mirror also pays")
    print("=" * 104)
    print("  %-6s %-10s %-9s %-11s %6s %7s %9s %9s %9s   %s"
          % ("R", "filter", "stop/tgt", "setup", "n", "win", "net/trade",
             "disc", "val", "95% CI"))
    keep_rows = []
    for R in (243, 729):
        for filt_name in ("all", "quiet", "rth", "quiet+rth"):
            for stop_a, tgt_a in ((0.75, 1.5), (1.0, 1.0), (0.75, 2.25)):
                for pair in (("break_up", "break_dn"),
                             ("reject_up", "reject_dn")):
                    rows = []
                    for nm in pair:
                        k = (R, 0.0, filt_name, stop_a, tgt_a, nm)
                        if k not in results:
                            rows = []
                            break
                        rows.append((nm, results[k]))
                    if not rows:
                        continue
                    means = [r[1][0].mean() for r in rows]
                    both = all(x > 0 for x in means)
                    for nm, (pnl, dd, yy) in rows:
                        lo, hi = boot(pnl, dd, rngen)
                        d_, v_ = yy < SPLIT, yy >= SPLIT
                        flag = "  <<<" if both and lo > 0 else ""
                        print("  %-6d %-10s %-9s %-11s %6s %7.3f %+9.3f %+9.3f %+9.3f   [%+.2f, %+.2f]%s"
                              % (R, filt_name, "%.2f/%.2f" % (stop_a, tgt_a),
                                 nm, "{:,}".format(len(pnl)), (pnl > 0).mean(),
                                 pnl.mean(), pnl[d_].mean() if d_.sum() else np.nan,
                                 pnl[v_].mean() if v_.sum() else np.nan, lo, hi, flag))
                        if both and lo > 0:
                            keep_rows.append((R, filt_name, stop_a, tgt_a, nm,
                                              float(pnl.mean())))

    # ---- the Goldbach question -------------------------------------------
    print()
    print("=" * 104)
    print("SHIFTED LATTICES -- is any of it BECAUSE the line is Goldbach?")
    print("=" * 104)
    print("  %-6s %-10s %-9s %-11s %10s %10s %8s"
          % ("R", "filter", "stop/tgt", "setup", "true", "shifted", "diff"))
    out = {}
    for R in (243, 729):
        for filt_name in ("all", "quiet", "rth", "quiet+rth"):
            for stop_a, tgt_a in ((0.75, 1.5), (1.0, 1.0), (0.75, 2.25)):
                for nm in ("break_up", "break_dn", "reject_up", "reject_dn"):
                    k0 = (R, 0.0, filt_name, stop_a, tgt_a, nm)
                    if k0 not in results:
                        continue
                    tv = results[k0][0].mean()
                    nulls = [results[(R, p, filt_name, stop_a, tgt_a, nm)][0].mean()
                             for p in PHASES[1:]
                             if (R, p, filt_name, stop_a, tgt_a, nm) in results]
                    if not nulls:
                        continue
                    nmn = float(np.mean(nulls))
                    out["%d|%s|%.2f/%.2f|%s" % (R, filt_name, stop_a, tgt_a, nm)] = {
                        "n": int(len(results[k0][0])), "true": float(tv),
                        "shifted": nmn, "diff": float(tv - nmn)}
                    print("  %-6d %-10s %-9s %-11s %+10.3f %+10.3f %+8.3f"
                          % (R, filt_name, "%.2f/%.2f" % (stop_a, tgt_a), nm,
                             tv, nmn, tv - nmn))

    json.dump(out, open(os.path.join(HERE, "stack.json"), "w"), indent=1)
    print("\nwrote stack.json")
    print("\n%d cell(s) paid on both sides with a lower bound above zero."
          % len(keep_rows))


if __name__ == "__main__":
    main()
