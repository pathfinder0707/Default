"""Fetch CME NQ/MNQ data from Databento, shaped for this repo's backtests.

Run this on YOUR machine (this session's network is locked to package
registries, so it cannot reach any data vendor). Then upload the .gz files.

    pip install databento
    export DATABENTO_API_KEY=db-xxxxxxxx
    python3 fetch_cme.py --tier a          # 1-minute bars, full history
    python3 fetch_cme.py --tier b          # trade prints, one month
    python3 fetch_cme.py --tier b --mbo    # market-by-order, one week

IMPORTANT -- prices must be UNADJUSTED. The PO3 lattice is anchored on absolute
price, so a back-adjusted continuous contract shifts every historical price by
the accumulated roll gaps and puts every lattice line in the wrong place.
Databento's continuous symbols (NQ.c.0) stitch raw contracts without price
adjustment, which is what we want -- the roll gaps are real and expected.

Check the cost estimate it prints BEFORE confirming. MBO is by far the largest.
"""
import argparse
import os
import sys

DATASET = "GLBX.MDP3"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", choices=["a", "b"], required=True,
                    help="a = 1-minute bars (full history); b = ticks (short window)")
    ap.add_argument("--symbol", default="NQ.c.0",
                    help="NQ.c.0 = front-month continuous, unadjusted. "
                         "Use MNQ.c.0 for the micro, or an explicit month like NQZ25.")
    ap.add_argument("--start", default=None)
    ap.add_argument("--end", default=None)
    ap.add_argument("--mbo", action="store_true",
                    help="tier b only: market-by-order instead of trades. "
                         "Gives real queue position. Very large -- keep it to days.")
    ap.add_argument("--yes", action="store_true", help="skip the cost confirmation")
    args = ap.parse_args()

    key = os.environ.get("DATABENTO_API_KEY")
    if not key:
        sys.exit("set DATABENTO_API_KEY first (export DATABENTO_API_KEY=db-...)")

    try:
        import databento as db
    except ImportError:
        sys.exit("pip install databento")

    if args.tier == "a":
        schema = "ohlcv-1m"
        start = args.start or "2023-01-01"
        end = args.end or "2026-08-15"
    else:
        schema = "mbo" if args.mbo else "trades"
        # short window on purpose -- a month of trades is enough to calibrate a
        # fill model, and three years of it is gigabytes for no extra insight
        start = args.start or ("2026-07-01" if not args.mbo else "2026-07-06")
        end = args.end or ("2026-08-01" if not args.mbo else "2026-07-11")

    client = db.Historical(key)

    print("dataset  %s" % DATASET)
    print("symbol   %s   (continuous symbols are UNADJUSTED -- roll gaps are real)" % args.symbol)
    print("schema   %s" % schema)
    print("range    %s -> %s" % (start, end))

    cost = client.metadata.get_cost(
        dataset=DATASET, symbols=[args.symbol],
        stype_in="continuous" if ".c." in args.symbol else "raw_symbol",
        schema=schema, start=start, end=end,
    )
    size = client.metadata.get_billable_size(
        dataset=DATASET, symbols=[args.symbol],
        stype_in="continuous" if ".c." in args.symbol else "raw_symbol",
        schema=schema, start=start, end=end,
    )
    print("\nestimated cost  $%.2f" % cost)
    print("estimated size  %.1f MB" % (size / 1e6))
    if not args.yes:
        if input("\nproceed? [y/N] ").strip().lower() != "y":
            sys.exit("aborted")

    data = client.timeseries.get_range(
        dataset=DATASET, symbols=[args.symbol],
        stype_in="continuous" if ".c." in args.symbol else "raw_symbol",
        schema=schema, start=start, end=end,
    )

    tag = args.symbol.replace(".", "_")
    out = "%s_%s_%s_%s.csv" % (tag, schema, start[:7], end[:7])
    df = data.to_df()
    print("\n%d rows" % len(df))
    print(df.head(3))
    print("\nindex tz: %s   <-- tell me this, or I will verify it empirically" % df.index.tz)

    df.to_csv(out)
    os.system("gzip -f '%s'" % out)
    gz = out + ".gz"
    print("\nwrote %s (%.1f MB)" % (gz, os.path.getsize(gz) / 1e6))
    if os.path.getsize(gz) > 29e6:
        print("OVER THE 30MB UPLOAD CAP -- split it, e.g. one file per year:")
        print("  python3 fetch_cme.py --tier a --start 2023-01-01 --end 2024-01-01")


if __name__ == "__main__":
    main()
