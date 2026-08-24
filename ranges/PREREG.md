# GB-Ranges backtest — pre-registration

Written **before** any hypothesis-driven statistic was computed. Only the data
sanity checks in `prep.py` (row counts, timezone confirmation, price extent)
were run first; those are not hypothesis-dependent.

Frozen: 2026-08-24, branch `claude/gb-time-trading-tool-4rwbyp`.

---

## 1. What the framework claims

Reconstructed from `goldbach_trifecta_plans_2026_01.pdf` (hopiplaka). The PDF is
a discretionary trade-plan narrative, but its chart geometry is exact and was
recovered by fitting the plotted lines — see `SPEC.md` for the derivation and
the residuals.

**The dealing range is a fixed price lattice.** For a power-of-three block size
`R`, the active block is

```
block_low = floor(price / R) * R
```

Verified against the author's own charts: the line labelled `[729 L]` sits at
25,515 = 35 x 729 exactly; the 2187 charts anchor at 21,870 = 10 x 2187 and
24,057 = 11 x 2187.

**Levels are percentages of the block.** Twenty distinct levels, symmetric
about 50:

| pct | name |
|---|---|
| 0 / 100 | range extreme, block boundary |
| 3 / 97 | internal range liquidity |
| 7 / 93 | LLOD — last line of defense |
| 11 / 89 | internal range liquidity |
| 17 / 83 | GIP — Goldbach inversion point |
| 23 / 77 | flow layer outer edge |
| 29 / 71 | flow layer middle |
| 35 / 65 | flow layer inner edge |
| 41 / 59 | external rebalance liquidity |
| 47 / 53 | internal rebalance liquidity |
| 50 | equilibrium |

Layers: **liquidity** `[0-11]` and `[89-100]`; **flow** `[23-35]` and `[65-77]`;
**rebalance** `[41-59]` centred on 50.

## 2. Data

HistData `NSXUSD` M1, 2023-01-02 → 2026-08-14, 1,192,912 bars, 1,879 sessions,
price 10,674.6 → 30,759.9. Timestamps are America/New_York **with DST** —
established empirically in the GB-time run and reconfirmed here (hour 17 is
absent in both winter and summer months, impossible under fixed EST).

### Known limitation, declared up front

This is HistData's **cash Nasdaq-100 CFD** feed, not CME futures. The Goldbach
lattice is anchored on absolute price, and cash differs from futures by the
basis — order tens to a couple hundred index points, drifting with rates and
dividends and resetting each contract roll. A drifting offset partially
decorrelates this feed's lattice phase from MNQ's.

Consequence, and how it is handled: the **phase-specific** hypothesis (H1) may
be under-powered on this feed through no fault of the framework. So a
**phase-agnostic** hypothesis (H1') is registered alongside it. H1' asks whether
*any* phase of the lattice shows structure, which is robust to a constant or
slow-drifting basis. A negative H1 with a positive H1' would point at the basis;
a negative on both is a negative on the framework as testable here.

This limitation is reported in the conclusions regardless of outcome. It is
not a reason to discount a negative result on H1'.

## 3. Primary hypothesis

**H1 — swing points cluster at GB levels.**

If the levels are real decision points, confirmed swing highs and lows should
land on them more often than chance.

- **Swings**: fractal pivots of strength `k` — a bar whose high exceeds the
  highs of the `k` bars either side (swing high), or whose low is below the lows
  of the `k` bars either side (swing low). Ties broken by first occurrence.
- **Primary configuration**, fixed now: `R = 2187`, `k = 5`, tolerance
  `±0.5` percentage points. Everything else is secondary.
- **Statistic**: fraction of swings whose block position falls within tolerance
  of any of the 20 GB percentages. Twenty levels at ±0.5pp cover **20.0%** of
  each block, so the uniform expectation is 0.200.

**H1' — phase-agnostic.** The best-scoring lattice phase out of 60, compared
against the distribution of best-of-60 under the phase null. Robust to a
constant basis offset.

## 4. Null models

Three, deliberately orthogonal. A finding must survive all three to count.

- **N1 — occupancy null.** Swings can only form where price goes. Compare the
  block-position distribution of swing prices against the block-position
  distribution of *all bar extremes* (bar highs for swing highs, bar lows for
  swing lows). This kills "price simply spends more time near block boundaries."
- **N2 — phase null.** Recompute the statistic under 60 lattice origins offset
  by `j * R / 60`, `j = 0..59`. The true lattice is `j = 0`. This kills "price
  respects round numbers in general" and is the direct analogue of the rotation
  null used for GB-time. Reported as the rank and z-score of `j = 0` against the
  59 shifted phases.
- **N3 — level-set null.** Compare the GB percentage set against 10,000 random
  20-element percentage sets drawn with matched minimum spacing. This kills
  "any twenty lines would do" and tests whether *these specific numbers* matter.

## 5. Secondary hypotheses

Registered now, reported with multiple-comparison context, not promotable to
headline findings.

- **H2 — rebalance dwell.** Price spends disproportionate time inside `[47-53]`
  relative to occupancy and phase nulls.
- **H3 — flow layer rejection.** On first touch of the flow layer (`[23-35]` /
  `[65-77]`), the rate of rejection back toward the rebalance layer exceeds the
  rate at matched non-GB bands of equal width.
- **H4 — GIP invalidation.** The PDF states that price passing `[17-83]`
  invalidates the liquidity plan. Test: `P(reach flow layer | passed GIP)`
  should exceed `P(reach flow layer | touched [11-89] but held GIP)`.
- **H5 — liquidity traversal.** The PDF's core mechanic: liquidity engineered at
  discount `[0-11]` is run to the *next block's* premium `[89-100]`. Test
  `P(reach adjacent block's opposite liquidity layer)` against the same
  measurement under the phase null.
- **H6 — Einstein sequence.** The ordered path `[0-100]` → block between
  `[3-97]` and `[11-89]` → gap to `[17-83]` → flow middle `[29-71]` → retrace to
  `[17-83]`. Tested as an ordered sequence against phase and chronology nulls,
  using the sequencing machinery from the GB-time run.

## 6. Robustness grid

Secondary. `R ∈ {81, 243, 729, 2187}` x `k ∈ {3, 5, 10, 20}` x tolerance
`∈ {0.25, 0.5, 1.0}` pp. 48 cells. Reported as a grid so that a single
favourable cell is visibly one cell out of 48, not a finding.

## 7. Decision rules, fixed in advance

- **Significance**: `|z| >= 3.0` against *every* applicable null. Chosen over
  1.96 because the robustness grid alone is 48 tests.
- **Direction matters**: a level effect must be positive. A significantly
  *negative* result is reported as evidence against, not as "an effect."
- **The round-number trap.** In the GB-time run a `+4.86σ` result at minute
  `:00` was traced to a round-clock artifact — `:30`, `:15`, `:45` behaved
  identically and are not GB nodes. The price analogue is decimal round numbers
  (25,000 / 24,500 / 25,250). Any positive result at a level will be checked
  against a matched set of round decimal prices before it is reported. If round
  decimals show the same effect, the finding is an artifact.
- **The chronology trap.** In the GB-time run a `+10.84σ` sequencing result came
  from a shuffle null that destroyed chronology and manufactured steps. Sequence
  tests here use the phase null and a chronological-random null, never a plain
  shuffle.
- **Stopping rule**: the tests listed above, on this data, once. No adding
  levels, no adding block sizes, no re-slicing after seeing results. Anything
  discovered afterwards is labelled exploratory and is not a finding.

## 8. What would make GB-ranges "work"

Stated now so it cannot be moved later:

1. H1 clears `+3σ` against N1, N2 and N3; **and**
2. the effect survives the round-decimal check; **and**
3. it is present in more than one block size or more than one year — a single
   cell of the robustness grid is not enough.

Anything less is reported as null.
