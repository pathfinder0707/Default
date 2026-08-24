# GB-Ranges — recovered specification

Source: `goldbach_trifecta_plans_2026_01.pdf` (Goldbach Trifecta, trade plans
2026.01, by hopiplaka). Nine pages: seven pages of prose describing five
discretionary trade plans, each illustrated with one annotated TradingView
screenshot of MNQ.

The prose names the levels but never states how the dealing range is anchored —
which is the whole game, since every level is a percentage of it. That was
recovered from the chart images.

## Recovery method

Each screenshot plots the levels as horizontal lines with a price axis. Reading
the pixel position of each line against the axis gives its price. Fitting

```
level_price = block_low + R * pct / 100
```

then determines `block_low` and `R`.

The p8 chart is labelled `[PO3 729]` and carries a black line explicitly
labelled `[729 L]` — the block low. It reads 25,515.

**25,515 = 35 x 729, exactly.** The lattice is anchored on absolute price.

That hypothesis then predicts every other line on every other chart:

```
                              read      pct       predicted     err
p8 EINSTEIN     block low 25515, R=729   (25515/729 = 35.0000, exact)
  black  [729 L]              25515    [  0%]      25515.0     +0.0
  green                       25540    [  3%]      25536.9     +3.1
  dotted green                25575    [  7%]      25566.0     +9.0
  green                       25600    [ 11%]      25595.2     +4.8
  green  EXECUTE              25645    [ 17%]      25638.9     +6.1
  blue   RETRACE              25725    [ 29%]      25726.4     -1.4
  red    REBALANCE            25877    [ 50%]      25879.5     -2.5

p3 LIQUIDITY    block low 21870, R=2187  (21870/2187 = 10.0000, exact)
  green  bottom               23815    [ 89%]      23816.4     -1.4
  dotted LAST LINE DEFENSE    23895    [ 93%]      23903.9     -8.9
  green                       24000    [ 97%]      23991.4     +8.6

p3 LIQUIDITY    block low 24057, R=2187  (24057/2187 = 11.0000, exact)
  black  boundary             24060    [  0%]      24057.0     +3.0
  green                       24110    [  3%]      24122.6    -12.6
  dotted [3~11] label         24200    [  7%]      24210.1    -10.1
  green  top                  24300    [ 11%]      24297.6     +2.4

p6 FLOW LAYER   block low 24057, R=2187
  blue  band low              24550    [ 23%]      24560.0    -10.0
  blue  band mid              24700    [ 29%]      24691.2     +8.8
  blue  band high             24826    [ 35%]      24822.5     +3.5

p7 REBALANCE    block low 24057, R=2187
  red   outer low             24955    [ 41%]      24953.7     +1.3
  red   band low              25083    [ 47%]      25084.9     -1.9
  red   band high             25213    [ 53%]      25216.1     -3.1
  red   outer high            25353    [ 59%]      25347.3     +5.7
```

Every residual is within ~13 points on charts where one pixel is worth 1–3
points. Four independent block anchors all land exactly on the lattice
(10 x 2187, 11 x 2187, 35 x 729).

The clincher is that the author's own text labels land where the reconstruction
puts them: `EXECUTE` on 17 (the GIP), `RETRACE` on 29 (flow middle),
`REBALANCE` on 50 (equilibrium), `LAST LINE OF DEFENSE` on 93 (the LLOD named
in the prose). Those labels were not used to fit anything.

## The specification

**Block:** `block_low = floor(price / R) * R`, `R` a power of three. The charts
use `R ∈ {729, 2187}`; the framework's name (PO3) implies the family
`{..., 81, 243, 729, 2187, 6561, ...}`.

**Position within block:** `pct = (price mod R) / R * 100`.

**Levels**, symmetric about 50:

| pct | name | layer |
|---|---|---|
| 0 / 100 | range extreme, block boundary | liquidity |
| 3 / 97 | internal range liquidity | liquidity |
| 7 / 93 | LLOD, last line of defense | liquidity |
| 11 / 89 | internal range liquidity | liquidity |
| 17 / 83 | GIP, Goldbach inversion point | — |
| 23 / 77 | flow layer outer edge | flow |
| 29 / 71 | flow layer middle | flow |
| 35 / 65 | flow layer inner edge | flow |
| 41 / 59 | external rebalance liquidity | rebalance |
| 47 / 53 | internal rebalance liquidity | rebalance |
| 50 | equilibrium | rebalance |

**Layers:** liquidity `[0-11]` and `[89-100]`; flow `[23-35]` and `[65-77]`;
rebalance `[41-59]`.

## The trifecta connection

The percentage set is **identical** to the GB-time minute set tested in the
previous run — 0, 3, 7, 11, 17, 23, 29, 35, 41, 47, 50, 53, 59, 65, 71, 77, 83,
89, 93, 97. One axis is the Zurich clock, the other is price within a PO3
block. That shared number set is what "trifecta" refers to.

GB-time tested null across every claim. That says nothing about GB-ranges: the
two use the same numbers on different axes, and the ranges version is anchored
in price, so it does not inherit the confound that sank the time version (node
minutes being perfectly correlated with time-of-day).

## The five trade plans

Summarised from the prose, for the secondary hypotheses:

1. **Liquidity** — price hovers at `[11-89]`, `[3-97]`, `[0-100]`, `[7-93]`
   building liquidity, then is repriced to the *next* PO3 block's opposite
   liquidity levels, rejects, and trades back into the current block. Allows
   travel to the external GIP `[17-83]`; passing it invalidates the plan.
2. **Flow continuation** — price moves through the flow layer, retraces back
   into it, and that retrace is the entry, targeting the rebalance layer then
   the next flow layer.
3. **Flow rejection** — price arrives from the rebalance layer, rejects the flow
   layer (preferably the middle, `[29-71]`), gaps out, and the retrace into the
   gap is the entry.
4. **Rebalance** — price consolidates around `[47-53]`, stops are engineered
   both sides, entry on a hit of `[41-59]`, exit at the opposite `[41-59]`.
5. **Einstein** — price consolidates at `[0-100]`, blocks between `[3-97]` and
   `[11-89]`, gaps between `[11-89]` and `[17-83]`, runs to flow middle
   `[29-71]`, retraces to `[17-83]` which is the entry; partials at `[47-53]`.

## What the PDF does not specify

- **Which block size is live.** The charts use 729 and 2187 on different
  examples with no stated selection rule. Tested independently.
- **Objective entry/exit triggers.** The plans are discretionary ("price should
  aggressively reject", "look for potential gap"). The backtest therefore tests
  the *levels and the structural claims*, not the author's discretionary
  execution, which is not specified tightly enough to test.
