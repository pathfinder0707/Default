# GB-TIME TOOLS — REVISED NEW CHAT HANDOFF
## Eden · XAUUSD / GBPUSD / NAS100 scalper · 1m chart

---

## CONTEXT

Eden trades XAUUSD, GBPUSD, and NAS100 on the 1-minute chart using:

- **Goldbach / PO3 / GB-time** for time-domain node sequencing
- **Quarterly Theory** for SSMT, PO3, tCISD, killzones, and trade framing

This handoff covers the **tools only**. The journal is separate.

The latest major design correction: the Pine indicator should **not** be a global node scanner. A global scanner bloats the chart because many candles mathematically match a GB-time node. The usable trading tool must be a **multi-swing path scorer**:

1. Detect confirmed swing highs/lows with left/right buffers.
2. Map only those swing times to GB-time nodes.
3. Keep several previous swing-node reads internally.
4. Score Algo 1 vs Algo 2 across that swing history.
5. Project the next minimum node from the most likely path.
6. Keep the chart clean: limited swing labels, one primary next line, optional alternate line, compact table.

---

## FRAMEWORK RULES — GROUND TRUTH

### GB-time read methods

For Zurich candle time `HH:MM`, calculate three reads:

1. **MM** = minute alone. This is primary.
2. **HH+MM** = hour plus minute.
3. **|HH−MM|** = absolute difference.

MM is primary and wins the label when more than one method hits. Secondary methods are confirmation, not equal chart spam.

Default practical settings:

- Swing ID MM tolerance: `0`
- Secondary tolerance: `1`
- Next-node scan tolerance: `1`
- Secondary methods allowed for swing ID: optional, usually on for context
- Chart labels should show swing nodes only, not all time hits

### Node values

**GB primes:** `3, 11, 17, 29, 41, 47, 53, 59, 71, 83, 89, 97`

**CE alternates:** `7, 14, 23, 35, 44, 50, 56, 65, 77`

`00` is also a valid node.

### Algo paths

**Algo 1 — forward:**

```text
00 → 11/14 → 41/44 → 03/7 → 17/23 → 71/77 or 29/35 ⊣
```

Index mapping:

```text
0 = 00
1 = 11/14
2 = 41/44
3 = 03/7
4 = 17/23
5 = 29/35 or 71/77 terminal
```

**Algo 2 — reverse:**

```text
29/35 → 47/53 → 11/14 → 17/23 → 59/65 → 03/7 ⊣
```

Index mapping used in Pine:

```text
5 = 29/35
4 = 47/53
3 = 11/14
2 = 17/23
1 = 59/65
0 = 03/7 terminal
```

Algo 2 walks backward: next index = current index - 1.

### Critical interpretation

- Algo 1 and Algo 2 are **not bullish/bearish**.
- Nodes are **decision levels**, not automatic reversals.
- The tools should show **where and when price faces a decision**, not tell direction.
- Do not color A1/A2 as red/green by default because it makes the tool look directional.
- Use neutral graphite/slate labels and gold for primary/shared/next.

---

## LATEST PINE TOOL

### File

`gb-time-multi-swing-path-scorer.pine`

### Indicator name

`GB-Time · Multi-Swing Path Scorer`

### Pine version

`//@version=6`

### What it does

This is the latest practical rebuild. It replaces the bloated scanner.

It:

- Detects confirmed pivot swing highs/lows with left and right buffers.
- Maps only confirmed swing times to GB nodes.
- Stores the last N swing-node reads in arrays.
- Scores Algo 1 vs Algo 2 across the swing history.
- Locks path when one algo has enough evidence and a score margin.
- Handles ambiguous cases by showing the minimum candidate.
- Projects one primary next node line and one optional alternate line.
- Shows a compact table with path status, scores, last swing, previous swing, primary next, alternate next, and history count.
- Draws only the most recent visible swing-node labels, controlled by settings.

### Why this version exists

Earlier versions failed practically because they displayed every mathematical time hit. That bloated the chart and did not answer the trading question.

The trading question is:

> Given the recent swing-node sequence, which algo is most likely active, and what is the next minimum decision node?

This version is designed around that question.

---

## RECOMMENDED DEFAULT SETTINGS

### Swing Detection / History

```text
Left buffer candles: 2
Right buffer candles: 2
Algo ID history depth: 8
Visible swing-node labels: 5
Show non-node swing markers: off
Show swing number badges: on
Show method on swing labels: off
```

### Algo Identification

```text
Allow skipped-node path ID: on
Max skip distance: 3
Minimum valid steps to lock path: 2
Score margin to lock: 2
Require high/low alternation for scoring: off at first
Penalize wrong path direction: on
```

### Method Reads

```text
MM tolerance for swing ID: 0
HH+MM / |HH-MM| tolerance for swing ID: 1
Allow secondary methods for swing ID: on
Next-node scan tolerance: 1
Next-node scan uses secondary methods: on
```

### Next Node Projection

```text
Show primary next line: on
Show alternate next line: on
Ambiguous: show only minimum: off initially
Forward scan minutes: 240
Line style: dotted
Primary line opacity: 45
Alternate line opacity: 72
```

### Visuals

```text
Theme: GB Dark
Label size: tiny
Swing label opacity: 8
Swing label spacing ATR multiple: 0.10
```

### Table

```text
Show table: on
Position: top right
Size: small
Show last 3 swing nodes: on
```

---

## PATH SCORING LOGIC

The indicator stores recent swing nodes and scores transitions between consecutive swing nodes.

### Algo 1 scoring

Algo 1 is valid when the A1 node index moves forward:

```text
0 → 1 → 2 → 3 → 4 → 5
```

A consecutive step scores strongly. A skipped step can score if allowed and within max skip distance.

### Algo 2 scoring

Algo 2 is valid when the A2 node index moves downward:

```text
5 → 4 → 3 → 2 → 1 → 0
```

This is the common bug to avoid: **Algo 2 is reverse**.

### Score components

- Consecutive valid step: strong score
- Skipped but valid path-direction step: medium score
- MM exact method quality: highest boost
- MM tolerance: medium boost
- Secondary method: small boost
- Wrong path direction: penalty if enabled
- High/low alternation can be required, but default off

### Path status examples

```text
Algo 1 locked
Algo 2 locked
ambiguous A1/A2
A1 leaning
A2 leaning
unlocked
terminal reached
```

---

## KNOWN LIMITATIONS

1. Pine cannot accept manual click reactions like the HTML tool can. The path scorer infers from confirmed swing sequence, not from manual “held support / held resistance / broke” inputs.
2. Pivot swing detection confirms late by `rightBars` candles. This is expected. The tool is for structure/path detection, while the next line projects forward from the current bar.
3. The next-node line uses `time + minutes * 60000`, so it is designed for the 1-minute chart.
4. If the chart has poor or noisy swings, path status may remain ambiguous. Use more history depth, higher buffers, or require more evidence.
5. The indicator still needs live TradingView compile testing after any edit.

---

## DO NOT REGRESS THESE BUGS

1. Do not use `text` as a variable name in Pine. It caused compile errors.
2. Do not revert to a global scanner that labels every node-hit candle.
3. Do not treat Algo 2 as forward. It walks backward toward index 0.
4. Do not color A1/A2 as bullish/bearish by default.
5. Do not show all secondary hits on chart by default.
6. Do not limit path identification to only last two swings. Use multi-swing history internally.
7. Do not make visible labels equal to history depth. History used and labels shown must remain separate.
8. Do not use candle body color for swing label placement. Swing highs label above; swing lows label below.

---

## NEXT IMPROVEMENTS TO BUILD

High-value additions for the next chat:

1. **Manual override mode**
   - Manually choose active algo and current node if auto scoring is wrong.

2. **Path confidence meter**
   - Convert scores/evidence into a simple status: weak / medium / strong.

3. **Better terminal handling**
   - When terminal is reached, optionally hide next projections until a fresh swing sequence forms.

4. **Session filter**
   - London AM / NY AM / custom session filters to reduce noise.

5. **Alerts with richer variants**
   - Primary next node soon
   - Primary node due
   - Alternate node due
   - Terminal projected
   - Path locked / path changed

6. **Review mode toggle**
   - Separate clean live runner from historical study mode.

7. **HTML sync**
   - Bring the same multi-swing scorer logic into the standalone HTML tool.

---

## FILES IN THIS PACKAGE

1. `GB_NEW_CHAT_HANDOFF_MULTI_SWING.md` — this handoff.
2. `gb-time-multi-swing-path-scorer.pine` — latest revised Pine v6 indicator.
3. `README_START_NEXT_CHAT_MULTI_SWING.txt` — copy/paste starter message for the next chat.
4. `GB_MULTI_SWING_HANDOFF_PACKAGE.zip` — packaged copy of all files.

---

## STARTER MESSAGE FOR NEXT CHAT

Use the README file, or paste this:

```text
Continue from this GB-time tool handoff. The latest Pine is a multi-swing path scorer, not a global scanner. Keep the chart clean. Use confirmed swing highs/lows, map swing times to GB nodes, score Algo 1 vs Algo 2 across the last N swing nodes, then project the next minimum node from the most likely active path. Do not regress to labeling every mathematical node-hit candle. First, review the Pine for compile issues and then improve path confidence, manual override, terminal handling, and alerts.
```
