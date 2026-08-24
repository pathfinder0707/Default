"""Reduce a large local bar/tick file into something small enough to upload.

Run this on YOUR machine. Nothing here needs network access.

    python3 ticktool.py inspect NQ_OHLCV_1S_2010_2026.parquet     # do this FIRST
    python3 ticktool.py downsample NQ_OHLCV_1S_2010_2026.parquet  # 1s -> 1m, by year
    python3 ticktool.py slice NQ_OHLCV_1S_2010_2026.parquet --start 2026-06-01 --end 2026-08-01

Parquet is read row group by row group, so a 1.5 GB file never loads into
memory. Parquet is already compressed -- gzipping it again does nothing, so the
size has to come from dropping rows or columns, not from packing harder.

`inspect` states every guess it makes rather than assuming silently.
"""
import argparse
import gzip
import io
import os
import sys

CHUNK = 2_000_000

TS_NAMES = ["ts_event", "ts_recv", "timestamp", "datetime", "date_time", "time",
            "date", "ts", "index", "__index_level_0__"]
OHLCV = {"o": ["open", "o", "px_open", "first"],
         "h": ["high", "h", "px_high", "max"],
         "l": ["low", "l", "px_low", "min"],
         "c": ["close", "c", "px_close", "last", "price"],
         "v": ["volume", "v", "vol", "size", "qty"]}


def human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return "%.1f %s" % (n, u)
        n /= 1024
    return "%.1f TB" % n


def _open(path):
    if path.endswith(".gz"):
        return io.TextIOWrapper(gzip.open(path, "rb"), encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def detect(cols):
    """Map schema columns onto ts + OHLCV, case-insensitively."""
    low = {c.lower(): c for c in cols}
    ts = next((low[n] for n in TS_NAMES if n in low), None)
    got = {}
    for k, names in OHLCV.items():
        hit = next((low[n] for n in names if n in low), None)
        if hit:
            got[k] = hit
    return ts, got


def is_parquet(p):
    return p.endswith(".parquet") or p.endswith(".pq")


# ---------------------------------------------------------------- inspect
def cmd_inspect(args):
    path = args.path
    print("file      %s" % path)
    print("size      %s" % human(os.path.getsize(path)))

    if not is_parquet(path):
        return _inspect_text(args)

    import pyarrow.parquet as pq
    pf = pq.ParquetFile(path)
    md = pf.metadata
    print("rows      %s" % "{:,}".format(md.num_rows))
    print("row grps  %d" % md.num_row_groups)
    print("\nschema:")
    for f in pf.schema_arrow:
        print("  %-24s %s" % (f.name, f.type))

    cols = [f.name for f in pf.schema_arrow]
    ts, got = detect(cols)
    print("\nauto-detected:")
    print("  timestamp   %s" % (ts or "NOT FOUND -- pass --ts"))
    for k in "ohlcv":
        print("  %-11s %s" % (k, got.get(k, "-")))

    head = pf.read_row_group(0).to_pandas()
    tail = pf.read_row_group(md.num_row_groups - 1).to_pandas()
    print("\nhead:\n%s" % head.head(3).to_string())
    print("\ntail:\n%s" % tail.tail(3).to_string())

    if ts and ts in head.columns:
        import pandas as pd
        a = pd.to_datetime(head[ts].iloc[0]); b = pd.to_datetime(tail[ts].iloc[-1])
        print("\nspan      %s  ->  %s" % (a, b))
        print("tz        %s" % (getattr(a, "tzinfo", None) or "naive -- I will verify empirically"))
        d = head[ts].iloc[:200]
        try:
            gaps = pd.to_datetime(d).diff().dt.total_seconds().dropna()
            print("bar step  median %.2fs (min %.2f, max %.2f) over first 200 rows"
                  % (gaps.median(), gaps.min(), gaps.max()))
        except Exception:
            pass
    print("\n--- paste everything above back to Claude ---")
    print("also say, if you know: whether prices are raw traded prices or")
    print("back-adjusted across contract rolls. That one silently breaks the study.")


def _inspect_text(args):
    path, size = args.path, os.path.getsize(args.path)
    head = []
    with _open(path) as fh:
        for i, line in enumerate(fh):
            head.append(line.rstrip("\n"))
            if i >= 5:
                break
    print("\nfirst lines:")
    for h in head:
        print("  %s" % h[:220])
    probe = head[1] if len(head) > 1 else head[0]
    delim = max([",", ";", "\t", "|"], key=lambda d: probe.count(d))
    cols = head[0].split(delim)
    print("\ndelimiter guess   %r -> %d columns" % (delim, len(cols)))
    ts, got = detect(cols)
    print("auto-detected     ts=%s  %s" % (ts, got))
    n = 0
    with _open(path) as fh:
        for _ in fh:
            n += 1
    print("rows              %s" % "{:,}".format(n))
    print("\n--- paste everything above back to Claude ---")


# ------------------------------------------------------------- downsample
def cmd_downsample(args):
    """1-second bars -> 1-minute bars, streamed by row group, split by year."""
    import pandas as pd
    import pyarrow.parquet as pq

    pf = pq.ParquetFile(args.path)
    cols = [f.name for f in pf.schema_arrow]
    ts, got = detect(cols)
    ts = args.ts or ts
    if not ts or "h" not in got or "l" not in got:
        sys.exit("could not detect columns -- run `inspect` and pass --ts explicitly.\n"
                 "found: ts=%s %s" % (ts, got))

    use = [ts] + [got[k] for k in "ohlcv" if k in got]
    rule = args.rule
    print("resampling %s -> %s   using %s" % (ts, rule, use))

    parts, seen = [], 0
    for i in range(pf.metadata.num_row_groups):
        df = pf.read_row_group(i, columns=use).to_pandas()
        seen += len(df)
        t = pd.to_datetime(df[ts], errors="coerce", utc=False)
        df = df.assign(_t=t).dropna(subset=["_t"]).set_index("_t")
        agg = {}
        if "o" in got: agg[got["o"]] = "first"
        if "h" in got: agg[got["h"]] = "max"
        if "l" in got: agg[got["l"]] = "min"
        if "c" in got: agg[got["c"]] = "last"
        if "v" in got: agg[got["v"]] = "sum"
        g = df.resample(rule).agg(agg).dropna(how="all")
        parts.append(g)
        print("  rowgroup %d/%d   %s rows in" % (i + 1, pf.metadata.num_row_groups,
                                                 "{:,}".format(seen)), end="\r", flush=True)

    df = pd.concat(parts)
    # a row-group boundary can split a minute across two parts -- merge them
    agg2 = {}
    if "o" in got: agg2[got["o"]] = "first"
    if "h" in got: agg2[got["h"]] = "max"
    if "l" in got: agg2[got["l"]] = "min"
    if "c" in got: agg2[got["c"]] = "last"
    if "v" in got: agg2[got["v"]] = "sum"
    df = df.groupby(level=0).agg(agg2)
    df = df.dropna(subset=[got.get("c", got["h"])])
    df.index.name = "ts"
    df.columns = [k for k in "ohlcv" if k in got]
    for c in [x for x in df.columns if x != "v"]:
        df[c] = df[c].astype("float32")

    print("\n%s bars   %s -> %s" % ("{:,}".format(len(df)), df.index[0], df.index[-1]))
    stem = (args.out or "nq_%s" % rule).replace(".parquet", "")
    total = 0
    # batch several years per file so this is a few uploads, not sixteen
    span = max(1, args.per_file)
    for y, g in df.groupby(df.index.year // span * span):
        lo, hi = int(g.index.year.min()), int(g.index.year.max())
        out = "%s_%d.parquet" % (stem, lo) if lo == hi else "%s_%d_%d.parquet" % (stem, lo, hi)
        g.to_parquet(out, compression="zstd")
        sz = os.path.getsize(out); total += sz
        flag = "   <-- OVER 30MB CAP, lower --per-file" if sz > 29e6 else ""
        print("  %-30s %9s  %s bars%s" % (out, human(sz), "{:,}".format(len(g)), flag))
    print("\ntotal %s" % human(total))


# ------------------------------------------------------------------ slice
def cmd_slice(args):
    """Keep native resolution for a date window -- for fill-model work."""
    import pandas as pd
    import pyarrow.parquet as pq

    pf = pq.ParquetFile(args.path)
    cols = [f.name for f in pf.schema_arrow]
    ts, got = detect(cols)
    ts = args.ts or ts
    use = [ts] + [got[k] for k in "ohlcv" if k in got]
    start, end = pd.Timestamp(args.start), pd.Timestamp(args.end)

    keep = []
    for i in range(pf.metadata.num_row_groups):
        df = pf.read_row_group(i, columns=use).to_pandas()
        t = pd.to_datetime(df[ts], errors="coerce")
        m = (t >= start) & (t < end)
        if m.any():
            keep.append(df.loc[m].assign(**{ts: t[m]}))
        elif keep:
            break                       # chronological; past the window
        print("  rowgroup %d/%d" % (i + 1, pf.metadata.num_row_groups), end="\r", flush=True)

    if not keep:
        sys.exit("no rows in that window")
    df = pd.concat(keep).set_index(ts)
    df.index.name = "ts"
    df.columns = [k for k in "ohlcv" if k in got]
    for c in [x for x in df.columns if x != "v"]:
        df[c] = df[c].astype("float32")

    out = args.out or ("nq_1s_%s_%s.parquet" % (args.start[:7], args.end[:7]))
    df.to_parquet(out, compression="zstd")
    sz = os.path.getsize(out)
    print("\n%s rows  %s -> %s" % ("{:,}".format(len(df)), df.index[0], df.index[-1]))
    print("wrote %s (%s)%s" % (out, human(sz),
                               "   <-- OVER 30MB CAP, shorten the window" if sz > 29e6 else ""))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("inspect"); p.add_argument("path"); p.set_defaults(fn=cmd_inspect)

    p = sub.add_parser("downsample"); p.add_argument("path")
    p.add_argument("--ts"); p.add_argument("--rule", default="1min")
    p.add_argument("--per-file", type=int, default=4,
                   help="years per output file (default 4); lower it if a file busts 30MB")
    p.add_argument("--out"); p.set_defaults(fn=cmd_downsample)

    p = sub.add_parser("slice"); p.add_argument("path")
    p.add_argument("--start", required=True); p.add_argument("--end", required=True)
    p.add_argument("--ts"); p.add_argument("--out"); p.set_defaults(fn=cmd_slice)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
