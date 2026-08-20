# GB-Time Final Implementation Notes

## Latest Pine

`gb-time-multi-swing-path-scorer-final.pine`

## Why this version exists

Earlier Pine versions were too bloated because they labelled every valid time-node candle. The current version only ingests confirmed swing highs/lows that map to GB-time nodes, then scores the sequence.

## Core implementation pattern

1. Detect pivot high / low using `ta.pivothigh()` and `ta.pivotlow()`.
2. Use the actual swing candle time: `time[rightBars]`.
3. Map that time to Algo 1 / Algo 2 nodes using all methods.
4. Store swing-node data in arrays.
5. Limit array history to `historyDepth`.
6. Score A1 and A2 over consecutive pairs in the history window.
7. Pick active path state.
8. Project primary and alternate next nodes.
9. Draw limited recent labels and one or two future lines.

## Key array fields

- `arrBar`
- `arrPrice`
- `arrIsHigh`
- `arrHour`
- `arrMinute`
- `arrA1Idx`
- `arrA1Lab`
- `arrA1Code`
- `arrA2Idx`
- `arrA2Lab`
- `arrA2Code`
- `arrNodeTxt`
- `arrSeq`

## Algo 1 index movement

Valid forward movement:

```text
current A1 index > previous A1 index
```

Consecutive is strongest. Skipped nodes are allowed only if enabled and within max skip distance.

## Algo 2 index movement

Valid reverse movement:

```text
current A2 index < previous A2 index
```

Never use `+1` progression for Algo 2.

## Compile caution

Pine reserved/named words should not be used as variable names. Avoid:

```text
text
line
table
float
int
color
```

Use names like:

```text
swingLabelTxt
primaryLabelTxt
nodeLabel
lineLabelText
```

## Settings to preserve

- Algo ID history depth
- Visible swing-node labels
- Allow skipped-node path ID
- Max skip distance
- Minimum valid steps to lock path
- Score margin to lock
- Method toggles / tolerances
- Primary / alternate next-node lines
- Table controls
- Theme controls

## Design target

A practical live trading aid:

```text
recent swing sequence → active/leaning/ambiguous algo → next primary node → alternate node
```

Not a signal generator, not a global scanner.
