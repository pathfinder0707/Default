# TDT — Time Dilation Theory, implemented and tested

Counting engine, trade models, a statistical test and an offline counter tool for the
Time Dilation Theory material (Inner Circle Morpheus, 2026).

The framework's load-bearing claim is that legs turn on particular candle counts — **7**,
**13**, **21**. That is falsifiable, so this directory implements the counting exactly as
the slides draw it and then asks whether the numbers do any work.

```
tdtcore.py      bar loading, resampling, stats helpers
counting.py     the three counting modes + swing origins
models.py       Model #2 and Model #3 detection
nulltest.py     hazard / neighbour / offset nulls + the grade test
backtest.py     executable rules and what they pay
selftest.py     verification against the slides, no data needed
run_all.py      runs everything, writes ALL.json
build_report.py ALL.json -> ../tdt-report.html
tdt-counter.html  offline single-file counter tool
```

## Run it

```sh
python selftest.py              # verify the engine — no data required
python run_all.py --synthetic   # whole pipeline on a random walk
python run_all.py               # the real study (needs bars.npz)
python build_report.py          # writes ../tdt-report.html
```

`bars.npz` is the schema written by `../futures/build_npz.py` and is gitignored, so a
fresh checkout has no feed:

```sh
python ../futures/build_npz.py     # writes futures/bars.npz
ln -s ../futures/bars.npz bars.npz
```

Only `numpy` is required.

## The counting, as extracted from the slides

A count starts at an origin candle numbered **1** — a swing low opens an up leg, a swing
high a down leg — and runs forward.

| mode | a candle takes the next number when |
|---|---|
| `classic` | always |
| `wick` | its high (up leg) exceeds the last numbered candle's high |
| `body` | its body extreme, `max(o,c)` up / `min(o,c)` down, does the same |

A candle that fails the test is marked `x` and takes no number. Contraction counting
therefore reaches a given number **at or later than** classic does, never earlier — which
is exactly the disagreement the *Advanced Counting Examples* panels draw: the candle
classic calls 13 is contraction-by-wick's 12 on the EURUSD M1 example, and
contraction-by-body's 9 on the USDCAD D1 example. `selftest.py` pins that identity:

> classic number − contraction number, at any candle, equals the number of `x` marks
> before it.

## The models

**Model #2** — counts on D1, execution on H1.

| count reached | reading |
|---|---|
| `[1-7]` | continuation of the previous fractal |
| `[1-13]` | reversal inside of the previous fractal |

**Model #3** — the same count at three nested swing degrees, giving a signature. The
conclusion slide grades them:

| signature | verdict |
|---|---|
| `13-7-7` | ok — "Reversal inside of a Continuation" |
| `7-13-7` | ok — "Contunuation of a Continuation" *(sic)* |
| `7-7-7` | ok |
| `21-..-..`, `7-21-13`, `7-21-7`, `13-21-7`, … | not advised |

The grading rule reduces to: **a 21 anywhere disqualifies the signature.**

## What is inferred, not stated

The slides are a discretionary course, so making them testable required fixing things
they leave to the trader. These are choices, they are all parameters, and results depend
on them:

- **Swing degree.** The slides draw the three degrees of Model #3 by eye. Here they are
  fractal pivots of strength `k`, defaulting to `5/3/2` (`--ks`).
- **"Terminates on 7".** Real legs rarely stop exactly on a key count, so a terminal
  count snaps to the nearest key within `--tol` (default ±1). Widen it and more legs
  qualify, but the claim weakens.
- **Body extreme vs close.** "Using Body Closures" is read as the body extreme,
  `max(o,c)` / `min(o,c)`, not the close alone.
- **Entry timing.** A swing of strength `k` is not knowable until `k` candles later, so
  entry is the open *after* confirmation. This is the single most consequential line in
  `backtest.py`: entering at the turn itself manufactures an edge nobody could take.
- **Stop and target.** Stop beyond the extreme the count terminated on, padded by
  `pad × ` the leg's own mean candle range; target a multiple of risk, swept.

## The tests

| test | question |
|---|---|
| **hazard** | Given a leg that reached count `n`, how often does it turn there? A spike at 7 is the claim; a smooth curve through 7 is the null. |
| **neighbour** | Each key count against a baseline built from nearby counts, skipping its immediate neighbours so a real spike cannot flatter itself. |
| **offset** | The same legs renumbered from an origin displaced a few candles off the swing — the leg and its endpoint held fixed, so only the alignment varies. For `classic` this degenerates into the neighbour test by construction; it earns its keep on the contraction modes, where a displaced origin also changes which candles are skipped. |
| **grade** | The conclusion slide made falsifiable: do `ok` signatures beat `not advised` ones on forward move? |

Read the **at-risk column first**. Few legs survive to 21, so that row is the one most
likely to show a large z off almost nothing — on a random walk it produced a hazard of
100% from two legs.

## Status — run on real NQ, 2016–2026

`bars.npz` is built from 4,778,135 NQ 1-minute bars (2010-07-07 → 2026-08-06), merged
from five parquet files. Data checks: no duplicate timestamps, monotonic, no OHLC
violations, no nulls, no zero-volume bars, and no contract-roll artifact (roll months
average 0.0208% absolute bar-to-bar move against 0.0196% elsewhere).

**The study starts at 2016 by default,** because session coverage ramps hard:

| years | median bars/day | usable for |
|---|---|---|
| 2010–2012 | 113–283 (1.9–4.7 h) | nothing |
| 2013–2015 | 960–1101 (16–18.4 h) | D1 with caution |
| 2016–2021 | 1282–1365 (21.4–22.8 h) | all timeframes |
| 2022–2026 | 1380 (23 h) | all timeframes |

A daily candle built on two hours of trade is not the same object as one built on
twenty-three, and counting across the join silently mixes them. `--from-year` controls it.

### What the data says

**The counts do not mark turns.** On H1, where the sample is large enough to matter, the
turn rate at each key count against its own neighbours:

| count | mode | turn rate | neighbours | z | legs at risk |
|---|---|---|---|---|---|
| 7 | classic | 18.4% | 14.0% | +1.12 | 4,475 |
| 13 | classic | 19.2% | 17.1% | +1.29 | 1,457 |
| 21 | classic | 16.5% | 19.6% | −0.67 | 328 |
| 7 | body | 26.8% | 25.0% | +0.43 | 2,029 |
| 13 | body | 24.4% | 27.7% | −1.56 | 316 |

Nine tests, largest |z| = 1.56, and that one is negative. On D1 the only |z| above 2 is
count 13 at **−3.11** — legs turn there *less* often than at neighbouring counts.

**And the counting adds nothing to the trading.** Holding entry, stop, target and timeout
fixed and changing only which legs are traded (H1, classic):

| signal set | trades | exp R | t |
|---|---|---|---|
| TDT selects (terminal 7 or 13) | 3,233 | +0.0817 | +5.14 |
| every leg, no count filter | 9,023 | +0.0872 | +9.11 |
| legs TDT **rejects** | 5,622 | +0.0899 | +7.38 |

The legs TDT rejects pay slightly *more* than the ones it selects. Across both timeframes
and all three modes the difference never reaches |t| = 2. Model #2's +5.14 t-statistic is
real, but it belongs to the trade structure — fade a completed swing leg with an ATR stop
and a 2R target — not to the counting. The count only shrinks the sample.

That contrast is the point of `filter_test`, and it is why a backtest of the model alone
cannot settle the question: a healthy t-statistic looks identical whether the counting
contributes or not.

### Reproduce

```sh
python run_all.py --tf D1 --exec-tf H1     # the models as taught
python run_all.py --tf H1 --exec-tf M15    # where count 21 is testable at all
python build_report.py
```

Count 21 is untestable on D1 in principle, not just here: only ~3% of legs survive that
long, so NQ's entire daily history yields about nine legs at risk. It needs H1 or below.

## The full search (`sweep.py`)

The study above tests one parameterisation. `sweep.py` searches **25,920** configurations
— four timeframes, three counting modes, five swing degrees, both trade polarities, both
signal timings, and the reward/timeout/pad grid — selecting on **2016–2022** and paying
out on **2023–2026**, which selection never sees. Costs are 0.75 NQ points per round turn
($4 commission plus a tick of slippage each way at $20/point).

```sh
python sweep.py             # the grid -> SWEEP.json
python holdtest.py          # offset, hold and k-scan -> HOLD.json
python build_sweep_report.py   # -> ../tdt-sweep-report.html
```

**Result: 0 of 12 readings passed.** The bar was |t| > 2.87 on held-out data (Bonferroni
over 12 finalists) plus beating a matched control.

### Why the counts cannot work, mechanically

The search's strongest survivor was `reach 7, follow` on classic counting. Classic
counting numbers every candle, so "the count reaches 7" *is* "six candles after the
pivot". Tested against a plain origin+6 entry the contrast is **+0.0000R, t=+0.00** — not
near zero, the same trades. No counting occurs.

That leaves one question: is offset 6 better than its neighbours? It is — but only at
k=6. Scanning the swing strength:

| swing k | peak offset | = count |
|---|---|---|
| 2 | 2 | 3 |
| 3 | 3 | 4 |
| 4 | 4 | 5 |
| 6 | 6 | **7** |
| 8 | 8 | 9 |

The best count is always **k+1** — the first candle on which the pivot is knowable.
Offsets below k are masked because the swing has not confirmed yet. TDT's 7 coincides with
the peak only when the swing strength happens to be 6; change k and the "magic number"
moves with it. The number is a property of the pivot filter, not of the market.

### What the search did find

A real effect, and it is not TDT's: **when a swing pivot of strength k confirms, enter on
the next candle in the direction of the leg that just completed.** Stop beyond the leg's
extreme padded by 0.25 × its mean candle range, target 3R, timeout 20 candles. M15 NQ,
costs charged, non-overlapping (one position at a time):

| k | period | trades | win | mean pts | total $ | max DD $ | return/DD | t |
|---|---|---|---|---|---|---|---|---|
| 6 | train | 6,710 | 43.2% | +1.66 | +$223,358 | $60,487 | 3.69 | +2.44 |
| 6 | test | 3,640 | 43.7% | +4.17 | +$303,799 | $82,072 | 3.70 | +2.63 |
| 8 | train | 5,745 | 45.0% | +1.92 | +$220,181 | $67,566 | 3.26 | +2.52 |
| 8 | test | 3,119 | 44.3% | +3.78 | +$235,703 | $104,272 | 2.26 | +2.00 |

It is momentum after a confirmed pivot, decaying with every candle of delay — which is
exactly why the best count is k+1. The return-to-drawdown ratio at k=6 is 3.69 on train
and 3.70 on test, which is the kind of stability that makes an effect worth pursuing.
The t-statistics are modest and it came out of a 25,920-configuration search, so it needs
its own out-of-sample confirmation before it is a strategy rather than a candidate.

### Fixed-time hold

Strip the stop and target out entirely — enter, hold N candles, exit at the close — and
the TDT signal has no directional content: at k=6 it *loses* $119,470 on train and makes
$307,105 on test, a sign flip that is regime, not edge. The stop/target structure, not the
signal, is what makes the rule above work.

## The counter tool

`tdt-counter.html` — open it in any browser. No dependencies, no network, remembers your
settings. Counts a pasted OHLC series in any of the three modes, marks the `x` candles,
circles 7/13/21, and shows how far the live leg is from each. Paste `o,h,l,c` (optionally
with leading date/time columns), oldest candle first.
