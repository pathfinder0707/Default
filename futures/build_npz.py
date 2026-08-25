"""Convert nq_1min_full.parquet (real CME NQ futures, UTC index) into the
bars.npz schema shared by ranges/prep.py and intraday/core.py, so both
existing pipelines run against it unmodified.

Timestamps verified UTC empirically: the daily maintenance-break gap lands at
the same New York hour (16:00) in both winter and summer once converted,
which is only possible with correct DST-aware conversion (same diagnostic
used to verify HistData's feed in the original studies).
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))


def session_id(date, hh):
    return np.where(hh >= 18, date * 10 + 1, date * 10)


def main():
    df = pd.read_parquet(os.path.join(HERE, "nq_1min_full.parquet"))
    df.index = df.index.tz_localize("UTC").tz_convert("America/New_York").tz_localize(None)
    df = df.sort_index()

    ts_str = df.index.strftime("%Y%m%d%H%M%S")
    ts = ts_str.astype(np.int64).values
    o, h, l, c = (df[k].astype(np.float64).values for k in ("o", "h", "l", "c"))
    # Volume was dropped from the original build and it should not have been.
    # It is the one input in the source data that is not derivable from price,
    # and it is exactly what would separate a sweep that gets absorbed from one
    # that runs -- the "when" question every conditional test here has asked of
    # price alone.
    v = df["v"].astype(np.float64).values

    date = ts // 1000000
    tod = ts % 1000000
    yr = date // 10000
    mo = (date // 100) % 100
    hh = tod // 10000
    mm = (tod // 100) % 100
    sess = session_id(date, hh)

    print("%s bars  %s -> %s" % ("{:,}".format(len(ts)), df.index[0], df.index[-1]))
    print("price range  %.1f -> %.1f" % (l.min(), h.max()))
    print("years        %s" % np.unique(yr).tolist())

    out = os.path.join(HERE, "bars.npz")
    np.savez_compressed(out, ts=ts, o=o, h=h, l=l, c=c, v=v,
                        date=date, yr=yr, mo=mo, hh=hh, mm=mm, sess=sess)
    print("wrote %s (%.1f MB)" % (out, os.path.getsize(out) / 1e6))


if __name__ == "__main__":
    main()
