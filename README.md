# GB-Time Trader

A single self-contained HTML file — `gb-time-trader.html`. No dependencies, no build,
no network. Open it in any browser, works offline, keeps its state in `localStorage`.

Built from `GB_FINAL_HANDOFF.md`, `GB_NEW_CHAT_HANDOFF_MULTI_SWING.md`,
`GB_FINAL_IMPLEMENTATION_NOTES.md` and `tools-handoff-fixed.md`.

---

## What it is

The previous HTML tool answered *"what does this swing time mean?"*. This one answers
the question you actually have at the chart:

> **A decision is due at 13:16. What is it, how good is the read, and am I allowed to trade it?**

Eight tabs, keyboard `1`–`8`:

| Tab | What it does |
|---|---|
| **LIVE** | Zurich clock, live three-method reads, on-node state, countdown to the next decision, upcoming decision times, alerts |
| **PATH ID** | Multi-swing scorer — the Pine path scorer ported to HTML |
| **CONFLUENCE** | One/two-swing read, verdict, strength, minimum-travel floor, chain forward |
| **WALK** | §1 identify path from two swings + walk minimum travel · §2 walk a full path with reactions |
| **CE WALK** | CE-alternate-only chain across both algos |
| **TRADE** | Setup gate (weighted checklist with hard requirements) + position sizer |
| **JOURNAL** | Logged trades, win rate and expectancy, broken down by condition |
| **SETTINGS** | Tolerance, horizon, alert rules, killzones, instrument contract values |

---

## Framework, as implemented

Ground truth, unchanged from the handoff:

- Three reads per Zurich `HH:MM` — `MM` (**primary, wins the label**), `HH+MM`, `|HH−MM|`.
  All three are checked independently, ±1.
- **Algo 1 forward** — `00 → 11/14 → 41/44 → 03/7 → 17/23 → 71/77 or 29/35 ⊣` (index **+1**)
- **Algo 2 reverse** — `29/35 → 47/53 → 11/14 → 17/23 → 59/65 → 03/7 ⊣` (index **−1**)
- Minimum travel = nearest upcoming node **in clock time**, compared by minutes-ahead so it
  is midnight-safe.
- Read quality is a **max**, never a sum: MM exact = strong, MM ±1 = medium, secondary = weak.
- **Nodes are decision levels.** Neither algo is bullish or bearish. Nothing in the UI colours
  A1/A2 directionally — gold is "primary/shared/next", not "buy".

---

## Bugs fixed from the previous build

Both were in `ceMin()` and both are reproducible in the old file:

1. **Algo 2 was silently dropped from every CE minimum comparison.** The A2 branch never set
   `time`, so `filter(x => x.time)` discarded it. Starting a CE walk anywhere on the A2 chain
   returned `{exhausted:true}` immediately — the tab looked like it worked and simply never
   walked.
2. **`times` was assigned a string instead of the array** (`times:n.times[0].time`), so the
   renderer's `s.times.map(...)` would throw a `TypeError` the moment A2 ever won a step.

The CE walk now completes the full documented reverse chain `35 → 50/56 → 14 → 23 → 65 → 7 ⊣`.

---

## On win rate

The handoff is explicit that nodes are decision levels, not directional signals, so the tool
does not claim a win rate and does not predict direction. What it does instead:

- **Filters** — the setup gate has four hard requirements (at a node, reaction *seen*, HTF bias
  agrees, tCISD confirmed). Miss any one and the grade is `NO`, regardless of the other points.
  Front-running a decision level is the expensive habit; the gate refuses it.
- **Prevents misses** — countdown, upcoming list, browser notification and sound, optionally
  restricted to killzones and MM-exact nodes only.
- **Measures** — every logged trade captures its grade, checklist ticks, killzone, node and R,
  so the Journal reports your *actual* win rate per node, per killzone, per grade and per
  condition. That is the only honest source of a win-rate number.

---

## Assumptions worth checking

- **Killzone windows are not in the handoff.** Defaults are the usual ICT windows converted to
  Zurich (London 08:00–11:00, NY AM 13:00–16:00, London Close 16:00–18:00, Asia 01:00–05:00,
  NY PM 18:00–20:00). Verify against your own charts — they are editable in Settings, and they
  shift with the DST alignment between Zurich and New York.
- **Instrument contract values vary by broker.** Defaults: XAUUSD `100` per $1.00 move per lot,
  GBPUSD `100000` per 1.0000 ($10/pip), NAS100 `1` per index point. Editable in Settings.
- Secondary-method hits are **off** by default on the live list, so it stays MM-driven. Turn
  them on in Settings for fuller context.

---

## Verification

The engine was tested headlessly before shipping — 88 assertions covering the three reads, the
11:03 worked example, MM-over-secondary label priority, both full algo chains, Algo 2's reverse
direction, terminal handling, shared `29/35` vs `71/77` labelling, midnight-safe minimum travel,
adjacent-minute dedupe, killzone midnight wrap, the scorer (lock, lean, skip limits, penalties,
confidence), the CE fix and the grade gate. All pass. Every tab was then driven in Chromium with
zero console errors, desktop and mobile.
