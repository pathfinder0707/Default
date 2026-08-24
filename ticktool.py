"""Reduce a large local tick file into something small enough to upload.

Run this on YOUR machine. Nothing here needs network access.

    python3 ticktool.py inspect  ticks.csv          # <- do this FIRST, paste the output
    python3 ticktool.py sample   ticks.csv --month 2014-06
    python3 ticktool.py bars     ticks.csv --out nq_1m_2010_2016.csv

Everything streams in chunks, so a 1.5 GB file works in a few hundred MB of RAM.
Handles .csv, .csv.gz, .txt and .parquet.

`inspect` guesses nothing silently -- it prints what it found and what it
assumed, so the guesses can be corrected before anything is computed on them.
"""
import argparse
import gzip
import io
import os
import sys

CHUNK = 2_000_000


def _open(path):
    if path.endswith(".gz"):
        return io.TextIOWrapper(gzip.open(path, "rb"), encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return "%.1f %s" % (n, u)
        n /= 1024
    return "%.1f TB" % n


# ---------------------------------------------------------------- inspect
def cmd_inspect(args):
    path = args.path
    size = os.path.getsize(path)
    print("file      %s" % path)
    print("size      %s" % human(size))

    if path.endswith(".parquet"):
        import pandas as pd
        pf = pd.read_parquet(path)
        print("rows      %d" % len(pf))
        print("columns   %s" % list(pf.columns))
        print("\nhead:\n%s" % pf.head(4).to_string())
        print("\ndtypes:\n%s" % pf.dtypes.to_string())
        return

    head = []
    with _open(path) as fh:
        for i, line in enumerate(fh):
            head.append(line.rstrip("\n"))
            if i >= 5:
                break

    print("\nfirst lines:")
    for h in head:
        print("  %s" % h[:220])

    # delimiter guess
    cand = [",", ";", "\t", "|", " "]
    probe = head[1] if len(head) > 1 else head[0]
    delim = max(cand, key=lambda d: probe.count(d))
    cols = head[0].split(delim)
    print("\ndelimiter guess   %r  -> %d columns" % (delim, len(cols)))

    first_is_header = not any(c.replace(".", "").replace("-", "").isdigit()
                              for c in cols[:3])
    print("header row        %s" % ("yes" if first_is_header else "NO -- positional columns"))
    if first_is_header:
        print("column names      %s" % cols)

    # tail
    with _open(path) as fh:
        try:
            fh.seek(max(0, size - 4000))
        except Exception:
            pass
        tail = fh.read().splitlines()
    print("\nlast line:\n  %s" % (tail[-1][:220] if tail else "?"))

    # row count + rough time span
    n = 0
    with _open(path) as fh:
        for _ in fh:
            n += 1
    print("\nrows              %s" % "{:,}".format(n))
    print("bytes/row         %.0f" % (size / max(1, n)))
    print("\n--- paste everything above back to Claude ---")
    print("also say, if you know: the timezone of the timestamps, and whether")
    print("prices are raw traded prices or back-adjusted across contract rolls.")


# ---------------------------------------------------------------- sample
def cmd_sample(args):
    """Pull one month out verbatim -- small enough to upload, real enough to verify."""
    out = args.out or ("sample_%s.csv" % args.month)
    kept = 0
    with _open(args.path) as fh, open(out, "w") as w:
        first = fh.readline()
        if args.header:
            w.write(first)
        else:
            if args.month.replace("-", "") in first.replace("-", "").replace("/", ""):
                w.write(first)
                kept += 1
        key = args.month.replace("-", "")
        for line in fh:
            # match YYYY-MM or YYYYMM anywhere in the first field
            head = line[:32].replace("-", "").replace("/", "")
            if key in head:
                w.write(line)
                kept += 1
            elif kept:
                break                      # file is chronological; done
    os.system("gzip -f '%s'" % out)
    gz = out + ".gz"
    print("wrote %s  (%s rows, %s)" % (gz, "{:,}".format(kept), human(os.path.getsize(gz))))
    if os.path.getsize(gz) > 29e6:
        print("still over the 30MB cap -- try a single week with --month %s-1" % args.month)


# ---------------------------------------------------------------- bars
def cmd_bars(args):
    """Stream ticks -> 1-minute OHLCV. ~1.5 GB in, ~15 MB gzipped out."""
    import pandas as pd

    ts_col, px_col, sz_col = args.ts, args.price, args.size
    reader = pd.read_csv(
        args.path, chunksize=CHUNK, sep=args.sep,
        usecols=[c for c in (ts_col, px_col, sz_col) if c is not None],
    )

    parts = []
    seen = 0
    for chunk in reader:
        seen += len(chunk)
        t = pd.to_datetime(chunk[ts_col], errors="coerce", utc=args.utc)
        chunk = chunk.assign(_t=t).dropna(subset=["_t"]).set_index("_t")
        agg = {px_col: ["first", "max", "min", "last", "count"]}
        if sz_col:
            agg[sz_col] = "sum"
        g = chunk.resample("1min").agg(agg).dropna(how="all")
        parts.append(g)
        print("  %s ticks -> %s minutes" % ("{:,}".format(seen), "{:,}".format(sum(len(p) for p in parts))),
              end="\r", flush=True)

    df = pd.concat(parts)
    # chunk boundaries can split a minute across two parts -- merge them
    df.columns = ["o", "h", "l", "c", "ticks"] + (["v"] if sz_col else [])
    df = df.groupby(level=0).agg({"o": "first", "h": "max", "l": "min",
                                  "c": "last", "ticks": "sum",
                                  **({"v": "sum"} if sz_col else {})})
    df = df.dropna(subset=["o"])
    print("\n%s minutes  %s -> %s" % ("{:,}".format(len(df)), df.index[0], df.index[-1]))

    stem = (args.out or "bars_1m.csv").replace(".csv", "")
    # six years of 1-minute bars gzips to roughly 25-35 MB, which is at or over
    # the 30 MB upload cap -- so split by year by default
    groups = [("", df)] if args.no_split else [
        (str(y), g) for y, g in df.groupby(df.index.year)]
    for tag, g in groups:
        out = "%s%s.csv" % (stem, ("_" + tag) if tag else "")
        g.to_csv(out)
        os.system("gzip -f '%s'" % out)
        gz = out + ".gz"
        sz = os.path.getsize(gz)
        flag = "   <-- OVER 30MB CAP" if sz > 29e6 else ""
        print("  %-28s %9s  %s rows%s" % (gz, human(sz), "{:,}".format(len(g)), flag))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("inspect"); p.add_argument("path"); p.set_defaults(fn=cmd_inspect)

    p = sub.add_parser("sample"); p.add_argument("path")
    p.add_argument("--month", required=True, help="YYYY-MM")
    p.add_argument("--out"); p.add_argument("--header", action="store_true", default=True)
    p.set_defaults(fn=cmd_sample)

    p = sub.add_parser("bars"); p.add_argument("path")
    p.add_argument("--ts", required=True, help="timestamp column name")
    p.add_argument("--price", required=True)
    p.add_argument("--size", default=None)
    p.add_argument("--sep", default=",")
    p.add_argument("--utc", action="store_true")
    p.add_argument("--out")
    p.add_argument("--no-split", action="store_true",
                   help="one file instead of one per year")
    p.set_defaults(fn=cmd_bars)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
