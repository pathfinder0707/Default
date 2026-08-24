# GB-Ranges backtest

Tests the Goldbach Trifecta's price-lattice framework on NASDAQ 1-minute data.

Read in this order:

| File | What it is |
|---|---|
| `SPEC.md` | The recovered specification, and how it was recovered from the source PDF's charts |
| `PREREG.md` | Hypotheses, nulls and decision rules, frozen before any statistic was computed |
| `../gb-ranges-report.html` | The report |

## Result

Null on every claim. Across 144 grid tests the largest z-score is +2.89, which
is what 144 draws from noise produce. The level-reaction test returns 0.500 at
every level, block size and horizon.

The power analysis bounds it: a +1pp edge on the reject rate would have
registered at +3.50 sigma, and 2% of swings being level-attracted at +3.08
sigma. The tests had the resolution to see anything tradeable.

## Pipeline

```
prep.py       load HistData CSVs -> bars.npz, confirm the timezone
gbr.py        engine: PO3 lattice, level set, fractal swings
h1.py         primary test (swings on levels) + 48-cell robustness grid
reaction.py   level touch -> reject/continue, per level, three horizons
structure.py  layer dwell, boundary sweep-and-reverse, round-decimal control
power.py      inject known effects, find the detection floor
build_report.py + report_template.html
```

Run:

```
python3 prep.py '/path/to/DAT_ASCII_NSXUSD_M1_*.csv'
python3 h1.py --grid && python3 reaction.py && python3 structure.py && python3 power.py
python3 -c "import json;json.dump({k:json.load(open(f)) for k,f in \
  (('h1','h1.json'),('reaction','reaction.json'),('structure','structure.json'),\
   ('power','power.json'))} ,open('ALL.json','w'),indent=1)"
python3 build_report.py
```

`bars.npz` and the raw CSVs are gitignored — data is redistributable from HistData.

## Note on the data

HistData `NSXUSD` is the **cash** Nasdaq-100 CFD, not CME futures. Since the
lattice is anchored on absolute price, the basis partially decorrelates this
feed's lattice phase from MNQ's. That is why a phase-agnostic hypothesis was
registered alongside the phase-specific one — it is null too, which argues the
basis is not what hides the effect. See the report's limitations section.
