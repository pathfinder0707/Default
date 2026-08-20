# GB-Time backtest — NASDAQ 100, 1-minute, 2023–2025

Reproducible pipeline behind the report. Verdict: **no measurable edge.**

## Data

HistData NSXUSD M1, 2023–2025 — 980,708 bars, 785 trading days. Not committed (~68 MB).
Drop the three `DAT_ASCII_NSXUSD_M1_YYYY.csv` files in `data/` to re-run.

## Timezone — the thing that nearly broke it

HistData documents these timestamps as fixed EST, no DST. **They are not.** The daily
session break sits at 16:15–17:59 in both winter and summer; under fixed EST it would
shift an hour seasonally. They track `America/New_York` *with* DST.

This matters more than usual here: the framework reads the *minute value* of the Zurich
clock, so a 60-minute error changes `HH+MM` and `|HH−MM|` on every bar. `prep.py`
converts per-date via IANA rules, yielding 720 days at +6h and 65 days at +5h (the
US/EU DST misalignment windows). A fixed offset silently corrupts those 65 days.

## The control

Whether a minute is a GB node is a deterministic function of the clock, so node-minutes
are perfectly confounded with time-of-day. Every test uses a **rotation null** — the same
measurement under 59 clocks shifted 1–59 minutes. Rotation is a bijection on minutes, so
the node set keeps exactly its size (384 MM-exact minutes in all 60 variants).

## Run order

| Script | Does |
|---|---|
| `gbcore.py` | Engine ported from the tool's tested JS |
| `validate_port.py` | Cross-validates the port — 17/17 incl. all five density figures |
| `tzcheck.py` / `tzcheck2.py` | Timezone determination |
| `prep.py` | NY→Zurich, session blocks → `bars.pkl` |
| `analyse.py` | Tests 1–3 (landing, range, reversal) |
| `breakdown.py` | By node / killzone / confluence / year |
| `minprofile.py` | Minute-of-hour profile — kills the `:00` finding |
| `seqtest.py` / `seqtest2.py` | Algo path sequencing, three nulls |
| `tradetest.py` | Directional rules net of cost |
| `consolidate.py` → `build_report.py` | `ALL.json` → the HTML report |

## Results

- Swings land on nodes: **+0.08σ** (three buffer settings, all null)
- Range at nodes: **−0.14σ** — nodes fractionally calmer
- Reversals at nodes: **+0.90σ**, effect 0.0006 on a coin flip
- Sequencing vs random chronological points: **A1 −7.97σ, A2 −4.34σ** — worse than random
- Every directional rule loses ≈ the spread
- 27 slices, 1 past 2σ (chance predicts 1.4)

## The two false positives

1. **`00` node, +4.86σ, +55% lift.** Not GB — the round-clock effect. `:30` (+41.6%),
   `:15` (+14.4%) and `:45` (+13.5%) are *not* GB nodes and behave identically. Across
   the hour GB minutes average −0.095% vs +0.041% for non-GB.
2. **Algo 2 sequencing, +10.84σ** under a shuffle null. Artifact: shuffling destroys
   chronology, which was never the hypothesis, and A2's index map is partly monotonic
   with the clock — moving forward through an hour manufactures valid A2 steps.

## Scope

Tests GB-time alone on NASDAQ. Says nothing about XAUUSD/GBPUSD (pipeline is ready),
nothing about GB combined with the Quarterly Theory layer, and nothing about discretionary
use of the framework as a process scaffold.
