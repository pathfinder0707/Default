# GB-Time Tools — Final New Chat Handoff

## Owner / User Context

User: Eden  
Trading focus: XAUUSD, GBPUSD, NAS100  
Chart: 1-minute execution  
Primary time reference: Zurich time, 24-hour format, IANA timezone `Europe/Zurich`

Eden trades using two frameworks:

1. **Goldbach / PO3 time sequencing** — GB-time node logic and path walking.
2. **Quarterly Theory / QT context** — SSMT, PO3, tCISD, killzones.

This handoff covers the **tools only**, not the trading journal.

The latest active Pine is:

```text
gb-time-multi-swing-path-scorer-final.pine
```

This Pine replaces earlier bloated scanner versions. It should be treated as the current working base.

---

## Critical Ground Rules

### Do not rebuild a global node scanner

Earlier versions became unusable because they labelled every candle where any mathematical GB-time read matched a node. That was too noisy and not tradable.

The current tool must remain a **multi-swing path scorer / runner**, not a global scanner.

Correct philosophy:

```text
Confirmed swing highs/lows → map swing time to node → score path → project next node.
```

Wrong philosophy:

```text
Every candle time that matches a GB node → label it.
```

### Nodes are decision levels, not directional signals

GB-time nodes mark where and when price may face a decision:

- hold as support,
- hold as resistance,
- or break through.

They are **not automatic buy/sell or bullish/bearish signals**.

Do not color Algo 1 as bearish and Algo 2 as bullish by default. Use neutral graphite/slate/gold themes unless Eden explicitly asks for directional colors.

---

## GB-Time Reads

For any Zurich candle time `HH:MM`, three reads exist:

1. **MM** = minute alone. Primary read. Wins the label.
2. **HH+MM** = hour plus minute. Secondary confirmation.
3. **|HH−MM|** = absolute difference. Secondary confirmation.

MM is primary. Secondary methods are useful, but they should not bloat the live chart.

Default intended settings:

```text
MM tolerance for swing ID: 0
Secondary tolerance for swing ID: 1
Use secondary methods for swing ID: true
Next-node scan tolerance: 1
Next-node scan uses secondary methods: true
```

Example:

```text
11:03 Zurich
MM = 3        → 03/7 node, primary MM exact
HH+MM = 14    → 11/14 node, secondary
|HH−MM| = 8   → no node
```

Do not regress to MM-only logic internally. The chart can display cleanly, but the detection engine must still understand all three reads.

---

## GB Node Paths

### GB primes

```text
3, 11, 17, 29, 41, 47, 53, 59, 71, 83, 89, 97
```

### CE alternates

```text
7, 14, 23, 35, 44, 50, 56, 65, 77
```

### 00 node

The `00` node is valid and configurable.

---

## Algo 1 Path

Algo 1 walks forward:

```text
00 → 11/14 → 41/44 → 03/7 → 17/23 → 29/35 or 71/77 terminal
```

Internal index order:

```text
0 = 00
1 = 11/14
2 = 41/44
3 = 03/7
4 = 17/23
5 = 29/35 or 71/77 terminal
```

Important:

- Algo 1 final bucket is terminal.
- `29/35` is shared with Algo 2 but is terminal for Algo 1.
- `71/77` is Algo 1 terminal only.

---

## Algo 2 Path

Algo 2 is reverse. It walks toward index `0`:

```text
29/35 → 47/53 → 11/14 → 17/23 → 59/65 → 03/7 terminal
```

Internal index order:

```text
5 = 29/35
4 = 47/53
3 = 11/14
2 = 17/23
1 = 59/65
0 = 03/7 terminal
```

Critical: Algo 2 advances by **decreasing** index. Do not treat Algo 2 as a forward `+1` sequence.

---

## CE Chains

CE-only chains are separate from the current Pine path scorer, but must remain part of the framework.

Algo 1 CE chain:

```text
14 → 44 → 7 → 23 → 35 terminal
```

Algo 2 CE chain:

```text
35 → 50/56 → 14 → 23 → 65 → 7 terminal
```

---

## Minimum Travel Concept

The minimum expected move is the nearest upcoming node in clock time across eligible active path candidates.

Current intended behavior:

- If Algo 1 is locked, primary next node comes from Algo 1.
- If Algo 2 is locked, primary next node comes from Algo 2.
- If ambiguous, choose minimum across candidates unless the user disables that behavior.
- Show optional alternate line so Eden can see the other candidate path.

The live chart should not show many future lines. It should show:

1. primary next-node vertical line,
2. optional alternate line,
3. compact table.

---

## Current Pine Tool: Multi-Swing Path Scorer

Filename:

```text
gb-time-multi-swing-path-scorer-final.pine
```

### Purpose

This Pine detects confirmed swing highs/lows, maps their **swing candle time** to GB nodes, scores Algo 1 vs Algo 2 over multiple swing nodes, and projects the next primary / alternate node.

It is not a general scanner.

### Main features

- Confirmed pivot swing highs/lows using left and right buffers.
- Multi-swing history array.
- Separate settings for:
  - history used for algo identification,
  - visible swing labels shown on chart.
- Path scoring over recent swing-node pairs.
- MM / secondary method quality scoring.
- Algo 1 and Algo 2 evidence counts.
- Locked / leaning / ambiguous / terminal path states.
- Primary and alternate projected vertical lines.
- Compact GB Path table.
- Optional alert conditions for primary node soon / due.

### Recommended starting settings

```text
Left buffer candles: 2
Right buffer candles: 2
Algo ID history depth: 8
Visible swing-node labels: 5
Show rejected swings: false
Allow skipped-node path ID: true
Max skip distance: 3
Minimum valid steps to lock path: 2
Score margin to lock: 2
Use high/low alternation: false initially
Penalize wrong direction: true
MM tolerance for swing ID: 0
Secondary tolerance: 1
Use secondary methods for swing ID: true
Show primary line: true
Show alternate line: true
Ambiguous: show only minimum: false initially
```

### Why visible labels are limited

The indicator should use multiple swings internally, but it should not label every historical node forever.

Use:

```text
Algo ID history depth = how much swing history powers scoring.
Visible swing-node labels = how much is shown on chart.
```

This solves the bloat issue without making the path ID too weak.

---

## Scoring Logic

For each pair of consecutive confirmed swing-node reads in the history window:

### Algo 1 valid step

```text
current A1 index > previous A1 index
```

A move of `+1` is consecutive and strong. A skipped move is allowed if enabled and within `Max skip distance`.

### Algo 2 valid step

```text
current A2 index < previous A2 index
```

Because Algo 2 is reverse.

### Score weighting

Current scoring concept:

- Consecutive valid step: strong score.
- Skipped but valid step: medium score.
- MM exact node reads add more quality score.
- MM tolerance adds less.
- Secondary methods add lowest quality score.
- Wrong direction can penalize score.

Path states:

```text
Algo 1 locked
Algo 2 locked
A1 leaning
A2 leaning
ambiguous A1/A2
terminal reached
unlocked
waiting
```

---

## Practical Trading Display

The chart should show only:

- recent confirmed swing-node labels,
- primary next-node line,
- alternate next-node line if enabled,
- compact table.

Avoid:

- labels on every candle,
- giant debug labels,
- candle-direction-based directional interpretation,
- red/green algo colors that imply buys/sells,
- too many future verticals.

---

## Known Limitations / Next Improvements

### 1. Pine compile must be checked live

The latest Pine was written for Pine v6, but it still needs to be pasted into TradingView and compile-tested. Fix any Pine syntax issues directly in the Pine Editor.

Known past issue:

- `text` cannot be used as a variable name in Pine because it conflicts with named args. Use `swingLabelText`, `lineLabelText`, etc.

### 2. Terminal handling can be improved

The current Pine marks terminal reached when the latest swing node is terminal for the winning path. Future refinement:

- visually mark path complete,
- optionally reset the score window after terminal,
- optionally require a fresh swing before new path ID.

### 3. Improve primary / alternate logic

Current behavior selects primary based on locked algo, or nearest candidate when ambiguous. Next refinement could show:

```text
Primary = highest-confidence path
Minimum = nearest clock-time candidate
Alternate = other algo next node
```

This would make the table more explicit.

### 4. Alerts need trade-ready messages

Current alert conditions are generic. Better future messages:

```text
GB-Time: Primary A1 17/23 at 07:23 in 2 minutes.
GB-Time: Primary A2 03/7 terminal due next candle.
```

### 5. Add manual override mode

Useful input options:

```text
Manual active algo: Auto / Algo 1 / Algo 2
Manual last node: dropdown
Manual anchor time: HH:MM
```

This allows Eden to override the auto scorer when his discretionary read is clearer.

### 6. Add session / killzone filter

Optional future settings:

- show labels only during London / NY killzones,
- keep table active outside sessions,
- suppress path scoring outside session.

### 7. Add object cleanup safeguards

If TradingView object limits are hit, reduce:

```text
max_labels_count
visible swing labels
rejected swing markers
```

The current design should stay lightweight, but object cleanup should remain a priority.

---

## HTML Tool Status

Current HTML reference file:

```text
gb-confluence-fixed-reference.html
```

This is a standalone browser tool, useful for manual GB-time confluence / walking.

It includes:

- Confluence tab,
- Walk tab,
- CE walk tab,
- fixed midnight-safe sorting,
- two-swing validation,
- Section 2 back-state fix,
- better shared `29/35` handling.

The HTML is useful reference, but the current Pine direction is the main focus.

---

## Do Not Regress These Fixes

1. All three methods must be checked: MM, HH+MM, |HH−MM|.
2. MM remains primary.
3. Algo 2 must walk reverse.
4. Shared `29/35` must be handled cleanly.
5. Terminal tags must be algo-specific.
6. Do not turn the Pine back into a global scanner.
7. Do not label every time hit on the chart.
8. Separate “history used” from “history shown.”
9. Use swing-node pivots for trading context.
10. Keep the chart clean by default.

---

## Suggested First Message for New Chat

Use the included file:

```text
README_START_NEXT_CHAT_FINAL.txt
```

It tells the next assistant exactly where to start.
