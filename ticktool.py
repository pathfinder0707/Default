"""Reduce a large local bar/tick file into something small enough to upload.

Run this on YOUR machine. Nothing here needs network access.

    python3 ticktool.py inspect NQ_OHLCV_1S_2010_2026.parquet     # do this FIRST
    python3 ticktool.py downsample NQ_OHLCV_1S_2010_2026.parquet  # 1s -> 1m, by year
    python3 ticktool.py slice NQ_OHLCV_1S_2010_2026.parquet --start 2026-06-01 --end 2026-08-01

Parquet is read row group by row group, so a multi-GB file never loads into
memory. Parquet is already compressed -- gzipping it again does nothing, so the
size has to come from dropping rows or columns, not from packing harder.

This file (Databento MDP3 OHLCV-1s) has two format quirks handled automatically:

  * Prices are fixed-point integers scaled by 1e9 (Databento's standard). Open
    1734500000000 means 1734.50. Detected from magnitude and un-scaled.
  * Rows for EVERY simultaneously-listed contract month are interleaved in one
    file, tagged by `instrument_id`, not already reduced to one continuous
    series. downsample/slice resolve this in two passes: pass 1 streams just
    (ts, instrument_id, volume) and picks the highest-volume instrument_id per
    calendar day (the standard "volume rollover" definition of front month);
    pass 2 keeps only rows matching that day's chosen contract before
    resampling. This keeps prices UNADJUSTED -- the roll gap between contracts
    is real and is exactly what a PO3 study anchored on absolute price needs.
    A day's chosen contract is printed whenever it changes, so the roll dates
    can be sanity-checked against known NQ quarterly expiries (Mar/Jun/Sep/Dec).

`inspect` states every guess it makes rather than assuming silently.
"""
import argparse
import gzip
import io
import os
import sys

TS_NAMES = ["ts_event", "ts_recv", "timestamp", "datetime", "date_time", "time",
            "date", "ts", "index", "__index_level_0__"]
OHLCV = {"o": ["open", "o", "px_open", "first"],
         "h": ["high", "h", "px_high", "max"],
         "l": ["low", "l", "px_low", "min"],
         "c": ["close", "c", "px_close", "last", "price"],
         "v": ["volume", "v", "vol", "size", "qty"]}
INSTR_NAMES = ["instrument_id", "symbol_id", "product_id", "instrumentid", "raw_symbol"]

PRICE_SCALE_DEFAULT = 1_000_000_000       # Databento fixed-point (1e-9 per unit)
PRICE_MAGNITUDE_THRESHOLD = 1_000_000     # int prices bigger than this need unscaling


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
    """Map schema columns onto ts + OHLCV + instrument, case-insensitively."""
    low = {c.lower(): c for c in cols}
    ts = next((low[n] for n in TS_NAMES if n in low), None)
    inst = next((low[n] for n in INSTR_NAMES if n in low), None)
    got = {}
    for k, names in OHLCV.items():
        hit = next((low[n] for n in names if n in low), None)
        if hit:
            got[k] = hit
    return ts, got, inst


def is_parquet(p):
    return p.endswith(".parquet") or p.endswith(".pq")


def detect_price_scale(sample, override=None):
    """Databento-style fixed-point prices are huge integers; real prices aren't."""
    if override:
        return float(override)
    try:
        med = float(sample.dropna().abs().median())
    except Exception:
        return 1.0
    return float(PRICE_SCALE_DEFAULT) if med > PRICE_MAGNITUDE_THRESHOLD else 1.0


# ---------------------------------------------------------------- inspect
def cmd_inspect(args):
    path = args.path
    print("file      %s" % path)
    print("size      %s" % human(os.path.getsize(path)))

    if not is_parquet(path):
        return _inspect_text(args)

    import pandas as pd
    import pyarrow.parquet as pq
    pf = pq.ParquetFile(path)
    md = pf.metadata
    print("rows      %s" % "{:,}".format(md.num_rows))
    print("row grps  %d" % md.num_row_groups)
    print("\nschema:")
    for f in pf.schema_arrow:
        print("  %-24s %s" % (f.name, f.type))

    cols = [f.name for f in pf.schema_arrow]
    ts, got, inst = detect(cols)
    print("\nauto-detected:")
    print("  timestamp   %s" % (ts or "NOT FOUND -- pass --ts"))
    for k in "ohlcv":
        print("  %-11s %s" % (k, got.get(k, "-")))
    print("  instrument  %s" % (inst or "none found -- treated as a single series"))

    head = pf.read_row_group(0).to_pandas()
    tail = pf.read_row_group(md.num_row_groups - 1).to_pandas()

    scale = detect_price_scale(head[got["c"]]) if "c" in got else 1.0
    if scale != 1.0:
        print("\nprice scale   values look like fixed-point x%s (e.g. %s -> %.4f)"
              % ("{:,.0f}".format(scale), head[got["c"]].iloc[0], head[got["c"]].iloc[0] / scale))
        print("              this is unpacked automatically by downsample/slice")

    print("\nhead:\n%s" % head.head(3).to_string())
    print("\ntail:\n%s" % tail.tail(3).to_string())

    if ts and ts in head.columns:
        a = pd.to_datetime(head[ts].iloc[0], unit="ns" if head[ts].dtype.kind in "iu" else None)
        b = pd.to_datetime(tail[ts].iloc[-1], unit="ns" if tail[ts].dtype.kind in "iu" else None)
        print("\nspan      %s  ->  %s  (UTC if these are Databento ts_event)" % (a, b))

    if inst:
        print("\nscanning instrument_id column across the whole file (fast, one column)...")
        ids = set()
        for i in range(md.num_row_groups):
            ids.update(pf.read_row_group(i, columns=[inst]).column(0).to_pylist())
            print("  rowgroup %d/%d" % (i + 1, md.num_row_groups), end="\r", flush=True)
        print("\n  %d distinct instrument_id values found." % len(ids))
        print("  This file mixes multiple contract months together (front month, back")
        print("  months, possibly spreads). downsample/slice auto-select the highest-")
        print("  volume instrument_id per calendar day -- the standard definition of")
        print("  'front month' -- and print every day the chosen contract switches, so")
        print("  the roll dates can be checked against real NQ quarterly expiries.")

    print("\n--- paste everything above back to Claude ---")


def _inspect_text(args):
    path = args.path
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
    ts, got, inst = detect(cols)
    print("auto-detected     ts=%s  %s  instrument=%s" % (ts, got, inst))
    n = 0
    with _open(path) as fh:
        for _ in fh:
            n += 1
    print("rows              %s" % "{:,}".format(n))
    print("\n--- paste everything above back to Claude ---")


# ---------------------------------------------------------- front-month roll
def build_roll_map(pf, ts, inst, vol):
    """Pass 1: highest-volume instrument_id per calendar day, streamed.

    Reads only 3 integer columns, so this is cheap even over 140M+ rows. The
    result is a small pandas Series (one row per calendar day) mapping day ->
    the instrument_id treated as front month that day.
    """
    import pandas as pd

    print("pass 1/2: scanning volume by contract and day (reads 3 columns only)...")
    parts = []
    for i in range(pf.metadata.num_row_groups):
        df = pf.read_row_group(i, columns=[ts, inst, vol]).to_pandas()
        t = pd.to_datetime(df[ts], unit="ns", errors="coerce")
        day = t.dt.floor("D")
        g = df.assign(_day=day).groupby(["_day", inst], observed=True)[vol].sum()
        parts.append(g)
        print("  rowgroup %d/%d" % (i + 1, pf.metadata.num_row_groups), end="\r", flush=True)

    total = pd.concat(parts).groupby(level=[0, 1]).sum()
    winners = total.groupby(level=0).idxmax().apply(lambda x: x[1])
    winners = winners.sort_index()

    switches = winners[winners != winners.shift(1)]
    print("\n  %d trading days, %d distinct front-month contracts, %d roll switches:"
          % (len(winners), winners.nunique(), max(0, len(switches) - 1)))
    for day, iid in switches.items():
        print("    %s  ->  instrument_id %s" % (day.date(), iid))
    return winners


def apply_roll_filter(df, ts, inst, roll_map):
    """Keep only rows whose instrument_id matches that day's front-month pick."""
    import pandas as pd
    t = pd.to_datetime(df[ts], unit="ns", errors="coerce")
    day = t.dt.floor("D")
    wanted = day.map(roll_map)
    keep = df[inst] == wanted
    return df.loc[keep].assign(_t=t.loc[keep])


# ------------------------------------------------------------- downsample
def cmd_downsample(args):
    """1-second bars -> 1-minute bars, front-month resolved, streamed by row group."""
    import pandas as pd
    import pyarrow.parquet as pq

    pf = pq.ParquetFile(args.path)
    cols = [f.name for f in pf.schema_arrow]
    ts, got, inst = detect(cols)
    ts = args.ts or ts
    if not ts or "h" not in got or "l" not in got:
        sys.exit("could not detect columns -- run `inspect` and pass --ts explicitly.\n"
                 "found: ts=%s %s" % (ts, got))

    roll_map = None
    if inst and not args.no_roll:
        roll_map = build_roll_map(pf, ts, inst, got.get("v", inst))

    price_scale = None
    if "c" in got:
        sample = pf.read_row_group(0, columns=[got["c"]]).to_pandas()[got["c"]]
        price_scale = detect_price_scale(sample, args.price_scale)
        if price_scale != 1.0:
            print("unscaling prices by %s" % "{:,.0f}".format(price_scale))

    use = [ts] + [got[k] for k in "ohlcv" if k in got] + ([inst] if roll_map is not None else [])
    rule = args.rule
    print("\npass 2/2: resampling %s -> %s   using %s" % (ts, rule, use))

    parts, seen = [], 0
    for i in range(pf.metadata.num_row_groups):
        df = pf.read_row_group(i, columns=use).to_pandas()
        seen += len(df)
        if roll_map is not None:
            df = apply_roll_filter(df, ts, inst, roll_map)
        else:
            df = df.assign(_t=pd.to_datetime(df[ts], unit="ns", errors="coerce"))
        df = df.dropna(subset=["_t"]).set_index("_t")
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
    # a row-group boundary can split a bar across two parts -- merge them
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
    if price_scale and price_scale != 1.0:
        for c in [x for x in df.columns if x != "v"]:
            df[c] = df[c] / price_scale
    for c in [x for x in df.columns if x != "v"]:
        df[c] = df[c].astype("float32")

    print("\n%s bars   %s -> %s" % ("{:,}".format(len(df)), df.index[0], df.index[-1]))
    print("price range  %.2f -> %.2f  (sanity-check this looks like real NQ)"
          % (df["l"].min(), df["h"].max()) if "l" in df and "h" in df else "")

    stem = (args.out or "nq_%s" % rule).replace(".parquet", "")
    total = 0
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
    """Keep native resolution for a date window, front-month resolved."""
    import pandas as pd
    import pyarrow.parquet as pq

    pf = pq.ParquetFile(args.path)
    cols = [f.name for f in pf.schema_arrow]
    ts, got, inst = detect(cols)
    ts = args.ts or ts
    start, end = pd.Timestamp(args.start), pd.Timestamp(args.end)

    roll_map = None
    if inst and not args.no_roll:
        roll_map = build_roll_map(pf, ts, inst, got.get("v", inst))
        roll_map = roll_map[(roll_map.index >= start) & (roll_map.index < end)]

    price_scale = None
    if "c" in got:
        sample = pf.read_row_group(0, columns=[got["c"]]).to_pandas()[got["c"]]
        price_scale = detect_price_scale(sample, args.price_scale)

    use = [ts] + [got[k] for k in "ohlcv" if k in got] + ([inst] if roll_map is not None else [])
    keep = []
    for i in range(pf.metadata.num_row_groups):
        df = pf.read_row_group(i, columns=use).to_pandas()
        t = pd.to_datetime(df[ts], unit="ns", errors="coerce")
        m = (t >= start) & (t < end)
        if not m.any():
            if keep:
                break
            continue
        chunk = df.loc[m].assign(_t=t[m])
        if roll_map is not None:
            day = chunk["_t"].dt.floor("D")
            wanted = day.map(roll_map)
            chunk = chunk.loc[chunk[inst] == wanted]
        keep.append(chunk)
        print("  rowgroup %d/%d" % (i + 1, pf.metadata.num_row_groups), end="\r", flush=True)

    if not keep:
        sys.exit("no rows in that window")
    df = pd.concat(keep).set_index("_t")
    df.index.name = "ts"
    df = df[[got[k] for k in "ohlcv" if k in got]]
    df.columns = [k for k in "ohlcv" if k in got]
    if price_scale and price_scale != 1.0:
        for c in [x for x in df.columns if x != "v"]:
            df[c] = df[c] / price_scale
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
    p.add_argument("--price-scale", type=float, default=None,
                   help="override auto-detected price divisor")
    p.add_argument("--no-roll", action="store_true",
                   help="skip front-month resolution (only if the file is already one contract)")
    p.add_argument("--out"); p.set_defaults(fn=cmd_downsample)

    p = sub.add_parser("slice"); p.add_argument("path")
    p.add_argument("--start", required=True); p.add_argument("--end", required=True)
    p.add_argument("--ts"); p.add_argument("--price-scale", type=float, default=None)
    p.add_argument("--no-roll", action="store_true")
    p.add_argument("--out"); p.set_defaults(fn=cmd_slice)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
