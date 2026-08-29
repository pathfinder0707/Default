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

## Status

The committed `ALL.json` and `tdt-report.html` were built with `--synthetic`, on a random
walk, because no price feed was present. They are stamped `synthetic: true` and the
report banners it. **They are a null, not a result**: they show what the tests return
when there is provably nothing to find, which is the right thing to check before pointing
them at real data. Rebuild with `python run_all.py && python build_report.py` once
`bars.npz` is in place.

## The counter tool

`tdt-counter.html` — open it in any browser. No dependencies, no network, remembers your
settings. Counts a pasted OHLC series in any of the three modes, marks the `x` candles,
circles 7/13/21, and shows how far the live leg is from each. Paste `o,h,l,c` (optionally
with leading date/time columns), oldest candle first.
