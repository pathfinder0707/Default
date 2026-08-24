"""Load HistData NSXUSD M1 bars, tag session/time context, cache as .npz.

Timestamps in this feed track America/New_York including DST -- verified
empirically in the GB-time run by locating the daily session break, which sits
at 16:15-17:59 local in both summer and winter (impossible under fixed EST).
The vendor's own gap report in the 2026-08 status file confirms it again:
16:14:59 -> 18:00:05.

For the ranges work the clock matters far less than it did for GB-time -- the
lattice is anchored in price, not time -- so the timezone is only used for
session slicing.
"""
import glob
import os
import sys

import numpy as np

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
DATA_GLOB = None  # set by caller
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bars.npz")


def load(data_glob):
    files = sorted(glob.glob(data_glob))
    if not files:
        raise SystemExit("no CSVs matched %s" % data_glob)

    ts, o, h, l, c = [], [], [], [], []
    for fn in files:
        raw = np.loadtxt(fn, delimiter=";", dtype=str, usecols=(0, 1, 2, 3, 4))
        stamp = raw[:, 0]
        # "YYYYMMDD HHMMSS"
        yyyymmdd = np.char.partition(stamp, " ")[:, 0].astype(np.int64)
        hhmmss = np.char.partition(stamp, " ")[:, 2].astype(np.int64)
        ts.append(yyyymmdd * 1000000 + hhmmss)
        o.append(raw[:, 1].astype(np.float64))
        h.append(raw[:, 2].astype(np.float64))
        l.append(raw[:, 3].astype(np.float64))
        c.append(raw[:, 4].astype(np.float64))
        print("  %-44s %8d bars" % (os.path.basename(fn), len(stamp)))

    ts = np.concatenate(ts)
    o, h, l, c = (np.concatenate(x) for x in (o, h, l, c))

    order = np.argsort(ts, kind="stable")
    ts, o, h, l, c = ts[order], o[order], h[order], l[order], c[order]

    # drop exact duplicate timestamps, keep first
    keep = np.ones(len(ts), bool)
    keep[1:] = ts[1:] != ts[:-1]
    ts, o, h, l, c = ts[keep], o[keep], h[keep], l[keep], c[keep]

    return ts, o, h, l, c


def decompose(ts):
    """Split YYYYMMDDHHMMSS into components."""
    date = ts // 1000000
    tod = ts % 1000000
    yr = date // 10000
    mo = (date // 100) % 100
    dy = date % 100
    hh = tod // 10000
    mm = (tod // 100) % 100
    return date, yr, mo, dy, hh, mm


def session_id(date, hh):
    """CME-style session: 18:00 NY starts the next day's session."""
    return np.where(hh >= 18, date * 10 + 1, date * 10)


def main():
    data_glob = sys.argv[1]
    print("loading %s" % data_glob)
    ts, o, h, l, c = load(data_glob)
    date, yr, mo, dy, hh, mm = decompose(ts)
    sess = session_id(date, hh)

    print("\n%d bars  %d -> %d" % (len(ts), ts[0], ts[-1]))
    print("price range  %.1f -> %.1f" % (min(l), max(h)))
    print("sessions     %d" % len(np.unique(sess)))
    print("years        %s" % np.unique(yr).tolist())

    # sanity: session break location, per season -- reconfirms the tz finding
    for label, months in (("winter (Jan/Feb)", (1, 2)), ("summer (Jul/Aug)", (7, 8))):
        sel = np.isin(mo, months)
        present = np.unique(hh[sel])
        missing = sorted(set(range(24)) - set(present.tolist()))
        # find the sparsest hour instead -- 17:00 should be near-empty
        counts = np.bincount(hh[sel], minlength=24)
        print("  %-18s sparsest hours %s  (absent: %s)"
              % (label, np.argsort(counts)[:2].tolist(), missing))

    np.savez_compressed(
        OUT, ts=ts, o=o, h=h, l=l, c=c,
        date=date, yr=yr, mo=mo, hh=hh, mm=mm, sess=sess,
    )
    print("\nwrote %s (%.1f MB)" % (OUT, os.path.getsize(OUT) / 1e6))


if __name__ == "__main__":
    main()
