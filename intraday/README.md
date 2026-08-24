# PO3 intraday study

Tests power-of-three block sizes for intraday NQ trading, with explicit entry
and exit rules. GB percentage levels are deliberately out of scope here — this
is about the block sizes only.

Report: `../po3-intraday-report.html` (interactive).

## Result

**No PO3 edge.** Three things, in order of importance:

1. **A power of three is not a special size.** Performance varies smoothly with
   block size; no PO3 value is a peak. In the NY morning the best block is
   R=196.9 (t=8.25) against 243's t=3.78.
2. **The lattice phase is irrelevant.** Shifting the lattice origin changes
   nothing (z between -1.00 and +1.80, true origin ranking 2nd to 16th of 20) —
   and the shifted origins are profitable too, which is the point.
3. **The one profitable-looking setup was a fill artifact.** S2 edge fade showed
   +3.32 pts/trade, t=9.63. Requiring price to trade N points *through* the level
   before counting a limit fill decays it monotonically: +2.09 at 1pt, +0.93 at
   2pt, -0.38 at 3pt, -2.55 at 5pt. Roughly 1.2 points of expectancy per point of
   penetration — the signature of pure adverse selection.

## What survives

The sizing table, and the drift finding: NQ's median RTH range went 170 -> 377
points across the sample while range-as-%-of-price held near 1.2%. So a fixed
point size decays. P(day range <= 243) fell from 73.8% (2023) to 16.8% (2026).

If you place blocks at all, scale spacing to ~0.5-0.6x the trailing 20-day
median RTH range rather than fixing a number.

## Pipeline

```
core.py     session slicing, R grid, PO3 helpers
sizing.py   realized range by timeframe/window/year -> sizing.json
strat.py    S1/S2/S3 backtests swept over 52 block sizes -> strat.json
deep.py     phase null, per-year, cost, random-time, volatility scaling -> deep.json
fill.py     fill-penetration realism, time of day -> fill.json
build_report.py + report_template.html
```

Run (needs `../ranges/bars.npz` from `ranges/prep.py`):

```
python3 sizing.py && python3 strat.py && python3 deep.py && python3 fill.py
python3 -c "import json;json.dump({k:json.load(open(f)) for k,f in \
  (('sizing','sizing.json'),('strat','strat.json'),('deep','deep.json'),('fill','fill.json'))} \
  | {'meta':{'bars':1192912,'rth_sessions':797,'start':'2023-01-02','end':'2026-08-14', \
  'instrument':'NSXUSD (HistData cash Nasdaq-100 CFD)','cost':1.0,'stop_f':0.10}}, \
  open('ALL.json','w'),indent=1)"
python3 build_report.py
```

## Fill model

Deliberately conservative. Level entries are resting limits at a price the bar
actually traded through, detected by high/low straddle — never by a close that
has already moved past. Stop and target resolve from the entry bar inclusive, so
a bar that blows through the level is charged as a loss. A bar containing both
resolves as the stop. Cost is charged round-trip on every trade.

Two bugs found and fixed during development, both of which had manufactured fake
edges: detecting boundary crosses from the close (pre-breached stops, giving an
impossible 4.7% win rate on a symmetric 1:1 bracket), and processing levels in
price order rather than time order (which selects trades using knowledge of
which levels get visited later in the session).
