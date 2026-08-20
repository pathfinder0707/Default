# GB-TIME TOOLS — NEW CHAT HANDOFF
## Eden · XAUUSD / GBPUSD / NAS100 scalper · 1m chart

---

## IDENTITY & CONTEXT

I'm Eden. I trade XAUUSD, GBPUSD, and NAS100 on the 1-minute chart using two frameworks:
- **Goldbach / PO3** (GB-time) — time-domain sequencing
- **Quarterly Theory (QT)** — SSMT, PO3, tCISD, killzone

**This handoff covers the tools only**, not the journal. The journal lives in Notion separately.

Your job: continue building and refining the tools below. Be direct, call out bugs, don't repeat mistakes from prior versions.

---

## FRAMEWORK RULES (establish as ground truth, never re-litigate)

### GB-TIME READS — THREE METHODS, MM PRIMARY

For any Zurich candle time HH:MM, three reads:
1. **MM** = minute alone (primary — wins the label)
2. **HH+MM** = hour + minute (extra confirmation)
3. **|HH−MM|** = absolute difference, always ≥0 (extra confirmation)

All three detect hits equally. MM wins the label when multiple methods hit. ±1 minute tolerance baked in everywhere.

**Example: 11:03 Zurich**
- MM = 3 → hits 03/7 node exactly (GB prime 3), **strong read, MM-exact**
- HH+MM = 14 → hits 11/14 node (CE alternate 14), secondary
- |HH−MM| = 8 → no node match

So 11:03 shows: `03/7 · A1+A2 · MM` (primary) + `11/14 · A2 · HH+MM` (secondary as triangle)

This was a critical bug fixed in prior versions — do NOT regress to only checking MM.

### GB-TIME NODE PATHS

**GB Primes (node values):** 3, 11, 17, 29, 41, 47, 53, 59, 71, 83, 89, 97
**CE Alternates (midpoints):** 7, 14, 23, 35, 44, 50, 56, 65, 77
The 00 node is also valid (MM=0, top of minute, or |HH−MM|=0 when HH=MM)

**Algo 1 (forward, bearish or bullish):**
```
00 → 11(14) → 41(44) → 03(7) → 17(23) → 71(77)/29(35) ⊣
```
Node values: `[0]`, `[11,14]`, `[41,44]`, `[3,7]`, `[17,23]`, `[71,77,29,35]`

**Algo 2 (reverse, bearish or bullish — walks END → START):**
```
29(35) → 47(50)/53(56) → 11(14) → 17(23) → 59(65) → 03(7) ⊣
```
Node values (index 0=terminal): `[3,7]`, `[59,65]`, `[17,23]`, `[11,14]`, `[47,50,53,56]`, `[29,35]`

**Key properties:**
- Both algos can run **bullish or bearish** — direction is NOT fixed by the algo
- Algo 2 is a **reverse algo** — sequences from end to start; terminal is at index 0 (03/7)
- Algos don't necessarily start/end at top of clock hour
- Nodes are **decision levels** (price holds as support, holds as resistance, or breaks through) — NOT reversal points
- ±1 min tolerance always applied

**Shared nodes across both algos:** 11/14, 17/23, 03/7, 29/35 — these appear in both paths and should be shown as "A1+A2" when both fire

**Terminals:** 71/77 or 29/35 on Algo 1 ⊣, 03/7 on Algo 2 ⊣

### CE CHAINS (subset of nodes, CE alternates only)

**Algo 1 CE chain (forward):** 14 → 44 → 7 → 23 → 35 ⊣
**Algo 2 CE chain (reverse):** 35 → 50/56 → 14 → 23 → 65 → 7 ⊣

### MINIMUM TRAVEL CONCEPT

At any point in time, the "minimum expected move" = the **nearest upcoming node in clock time across both algos**, found by scanning the next 90 minutes and returning the first minute where any method hits any node. This is the floor — price should at least travel to this node before the farther one matters.

---

## TOOL 1: GB CONFLUENCE TOOL
**File:** `gb-confluence.html`
**What it is:** Standalone HTML file (dark theme, runs offline in any browser)

### THREE TABS

#### TAB 1 — CONFLUENCE
Input: one or two swing times in Zurich 24h + direction (▼ low / ▲ high)
Output:
- **Verdict:** agree (both algos point to same next node) / conflict (different next nodes) / partial (only one algo reads)
- **Floor:** minimum-travel next node with its earliest clock time and method label
- **Both algo columns side by side:** what node this swing is, what the next node is, watch times
- **Confluence strength badge:** strong (MM exact both) / medium (tolerance or secondary) / low (one algo)
- **Swing cross-check (two-swing):** verifies the two swings sit consecutively on the same algo
- **Method reads (collapsible):** shows each method's value and what node it maps to

Two modes: **Two swings** (precise path ID) / **One swing** (explore — shows all possible node interpretations)

**Chaining from the floor:** once a floor is shown, a "Next minimum →" button chains forward step by step from there. Also has ← Back using history stack.

#### TAB 2 — WALK
Two sections:

**Section 1 — Minimum travel:**
Two swings → identifies which algo(s) the swings sit on (consecutive or skipped) → shows both candidates → pick one → minimum-travel chain forward (always the nearest node across both algos at each step, showing full method-time list, alternate path noted). ← Back with history.

Each candidate card has two buttons:
- "Walk §1 minimum →" — walks the min-travel chain in Section 1
- **"Walk path §2 →"** — loads the identified path into Section 2

**Section 2 — Walk a path (old-tracker style):**
Full algo sequence displayed as node pills. Connected to Section 1 via "Walk path §2 →" button, OR start manually with a time + algo selection.

The walk shows:
- Full path: confirmed nodes colored by reaction (green=support, red=resistance, grey/strikethrough=broke), cursor glowing gold, future nodes dimmed, numbered badges on confirmed nodes (1, 2, 3...)
- **Position indicator** — "node 3 of 6"
- **Next node panel:** node name large, all method times to watch (MM first, soonest highlighted), reaction buttons (held support / held resistance / broke through)
- Pick reaction (optional), click **Advance →** — node gets badge + color, cursor moves
- ← Back through history, Reset

#### TAB 3 — CE WALK
CE-to-CE minimum-travel chain. Enter a start time → identifies which CE position each algo is at → chains forward always picking the nearest CE alternate in clock time across both algos. Each step shows the CE node, which GB prime it maps to, all method times. ← Back, Reset.

---

### CORE LOGIC (shared across all three tabs)

```javascript
const TOL = 1; // ±1 minute tolerance, never changes

// All three methods
function methods(hh, mm) {
  return [
    { name: 'MM',      val: mm,              pri: true  },
    { name: 'HH+MM',   val: hh + mm,         pri: false },
    { name: '|HH−MM|', val: Math.abs(hh-mm), pri: false },
  ];
}

// Hit test: is readVal within TOL of any value in vals[]?
// Returns {d, method} for BEST hit — MM preferred, then smallest distance
function hitValues(hh, mm, vals) {
  const ms = methods(hh, mm);
  let best = null;
  ms.forEach(m => {
    vals.forEach(target => {
      const d = Math.abs(m.val - target);
      if (d <= TOL) {
        if (best === null || (m.pri && !best.method.pri) || (m.pri === best.method.pri && d < best.d)) {
          best = { d, method: m, val: target };
        }
      }
    });
  });
  return best;
}

// Watch-times for a node: scan next 90 min, MM-priority labelling
function solveTimes(vals, from) {
  const out = []; let h = from.hh, m = from.mm;
  for (let s = 0; s < 90 && out.length < 8; s++) {
    m++; if (m > 59) { m = 0; h = (h + 1) % 24; }
    const ms = methods(h, m); const via = [];
    ms.forEach(mt => {
      let hit = null;
      vals.forEach(t => { const d = Math.abs(mt.val - t); if (d <= TOL && (hit === null || d < hit)) hit = d; });
      if (hit !== null) via.push(mt.name + (hit > 0 ? '±' + hit : ''));
    });
    if (via.length) out.push({ time: pad(h) + ':' + pad(m), via: via.join(', ') });
  }
  return out;
}
```

**Node definitions:**
```javascript
const A = {
  1: [
    { l: '00',    v: [0],          term: false },
    { l: '11/14', v: [11, 14],     term: false },
    { l: '41/44', v: [41, 44],     term: false },
    { l: '03/7',  v: [3, 7],       term: false },
    { l: '17/23', v: [17, 23],     term: false },
    { l: '71/29', v: [71,77,29,35],term: true  },
  ],
  2: [
    { l: '03/7',  v: [3, 7],         term: true  }, // terminal — algo 2 walks backward toward this
    { l: '59/65', v: [59, 65],       term: false },
    { l: '17/23', v: [17, 23],       term: false },
    { l: '11/14', v: [11, 14],       term: false },
    { l: '47/53', v: [47,50,53,56],  term: false },
    { l: '29/35', v: [29, 35],       term: false },
  ],
};

const CEA = {
  1: [
    { ce: [14],    l: '14',    gb: '11',     term: false },
    { ce: [44],    l: '44',    gb: '41',     term: false },
    { ce: [7],     l: '7',     gb: '03',     term: false },
    { ce: [23],    l: '23',    gb: '17',     term: false },
    { ce: [35],    l: '35',    gb: '29/71',  term: true  },
  ],
  2: [
    { ce: [7],     l: '7',     gb: '03',     term: true  },
    { ce: [65],    l: '65',    gb: '59',     term: false },
    { ce: [23],    l: '23',    gb: '17',     term: false },
    { ce: [14],    l: '14',    gb: '11',     term: false },
    { ce: [50,56], l: '50/56', gb: '47/53',  term: false },
    { ce: [35],    l: '35',    gb: '29',     term: false },
  ],
};
```

**Algo 2 direction:** Algo 2 walks **reverse** — nextIdx = idx - 1 (not +1). Terminal at index 0.

---

## TOOL 2: GB-TIME PINE INDICATOR
**File:** `gb-time-indicator.pine`
**Pine Version:** v5
**Chart:** 1-minute, overlay

### WHAT IT DOES
Marks candles where GB-time nodes fire. For each candle:
- Reads HH and MM in the chosen timezone (IANA string, DST-safe)
- Computes all three method values
- Checks each node's members against all three methods ±TOL
- **MM hit → full label below bar** (node, algo, method)
- **Secondary-only hit → small triangle** (optional, togglable)
- Shared nodes (A1+A2) shown in gold colour
- Terminal nodes marked with " T"
- Info table top-right: timezone time, three method values, minimum-travel next node

### FEATURES (all togglable)
1. **Forward node lines** — faint dotted verticals at the next N distinct upcoming node times (skips adjacent-minute repeats of same node due to tolerance), each labelled
2. **Anchor mode** — set an anchor swing time; only shows nodes at/after that time in the same session
3. **Read-quality score** — table row grading the best read: strong (MM exact) / medium (MM ±1) / weak (secondary only). Takes the MAX quality across all nodes on that bar, NOT a sum.
4. **Timezone** — Europe/Zurich default (handles DST via IANA)
5. **Tolerance** — default 1, configurable 0–3

### ALGO PATH DEFINITIONS (Pine)
```pine
// Algo 1 forward:  00 · 11/14 · 41/44 · 03/7 · 17/23 · 71/29(term)
// Algo 2 reverse:  03/7(term) · 59/65 · 17/23 · 11/14 · 47/53 · 29/35
f_method(H, M, a, b, c, d) =>
    // returns 1=MM, 2=HH+MM, 3=|HH-MM|, 0=none
    // checks: MM=M, HH+MM=H+M, |HH-MM|=math.abs(H-M)
    // MM is checked first (priority)
```

### KNOWN COMPILE RISKS
- Pine v5 cannot mutate outer-scope variables from inside a function — all node assembly done at top level with direct `:=` chaining
- `max_labels_count = 500, max_lines_count = 100` set in `indicator()`
- Forward lines use `array.new_line()` and are cleared/rebuilt on `barstate.islast`
- `while` loop used for forward-line scan (finds distinct nodes, not adjacent tolerance minutes)
- Can't be verified offline — paste into Pine Editor and check compile errors

---

## KNOWN BUGS FIXED (do NOT regress these)

1. **HH+MM and |HH−MM| not detecting nodes** — all three methods must check independently. 11:03 → HH+MM=14 must register CE 14 / 11/14 node. Fixed via single `hitValues()` function.

2. **Secondary tolerance showing same node 4 times** — forward-line scan clusters adjacent minutes on same node. Fixed with `lastNode` tracking — only fires on new distinct node names.

3. **Score summing across bars** — score must be `Math.max()` across all nodes, not `+=`. A bar with one weak secondary hit should score "weak", not inflate.

4. **Algo 2 direction** — Algo 2 walks backward (idx - 1 each step). Terminal at index 0. Common mistake: treating Algo 2 as forward.

5. **CE tab was a single-time lookup** — should be a CE-to-CE walk chain (nearest CE across both algos each step), not just "does this time hit a CE?"

6. **Section 2 of Walk tab was disconnected** — must be fed from Section 1's path identification via "Walk path §2 →" button AND support manual start from time+algo selection.

7. **Direction toggles** — implemented with `querySelectorAll('[data-s="..."]')` not fragile ID string concatenation.

---

## DESIGN PRINCIPLES

- **Dark theme** throughout: bg `#0d0f0e`, panel `#16181a`, gold `#d4a13a`, bear `#d65a4a`, bull `#5aa86a`
- **Monospace font** for all node names, times, method values
- **No fake certainty** — nodes are decision levels, not directional signals. The tools tell you WHERE and WHEN price will face a decision, not which way it goes.
- **MM is always primary** — show it first, label it, weight it. Secondary methods are confirmation, not equal.
- **±1 baked in** — no user-visible tolerance toggle in most views (it's there in Pine but not in the HTML tools)
- **Both algos, neither direction** — neither algo is inherently bullish or bearish. Direction toggle exists but defaults to neutral.

---

## FILES TO HAND OVER

The new chat should receive three files:
1. `gb-confluence.html` — the 3-tab web tool (paste content directly or share file)
2. `gb-time-indicator.pine` — the Pine v5 indicator (paste into TradingView Pine Editor)
3. This handoff document

The `.html` file is self-contained — no dependencies, runs offline. Open in any browser.

---

## WHAT'S STILL TO DO / OPEN QUESTIONS

1. **Pine indicator compile** — hasn't been tested live in TradingView. May have syntax issues in forward-line `while` loop or `for ... in` array iteration. First thing to verify in new chat.

2. **Alerts in Pine** — `alertcondition()` for node-hit and pre-node warning not yet added. High-value addition for stepping away from screen.

3. **Anchor mode in Section 2 of HTML** — Section 2 walk currently starts from a manually entered time or Section 1 feed. Could add: auto-detect starting node from the anchor time rather than requiring user to enter a time.

4. **GBPUSD SSMT triad** — for the journal (separate handoff), the GBPUSD correlated pair for SSMT divergence is still undefined. Gold = Gold/Silver. GBPUSD triad TBD.

5. **NAS100 in journal** — not formally journaled yet, only tape-read.

---

## COMMUNICATION STYLE

- Direct and concise — call out bugs and uncomfortable patterns plainly
- Don't re-explain basics (PO3, CISD, FVG, SSMT, tCISD, AMD)
- Don't repeat the same point more than once
- No cheerleading
- Surface what's wrong, not just what's right
- When building tools: verify logic offline before claiming it works
- When unsure: ask one question, don't guess and produce broken output

---

## PATCH NOTES — fixed build

The accompanying fixed files are:
1. `gb-confluence-fixed.html`
2. `gb-time-indicator-fixed.pine`
3. `tools-handoff-fixed.md`

### HTML fixes applied
- Minimum-travel timing is now midnight-safe. `solveTimes()` returns `step`/minutes-ahead, and all floor/minimum comparisons sort by `step`, not by clock-string order.
- Confluence two-swing mode now performs the same ordered path cross-check as the Walk tab and displays consecutive/skipped/failed path status.
- Confluence now shows a read-strength badge: strong, medium, or low.
- Direction buttons are visible as annotations only; they no longer imply directional certainty or hidden calculation logic.
- Section 2 Back now restores the exact previous state from history instead of popping confirmed nodes heuristically.
- Algo 1’s terminal bucket still remains one terminal step, but 29/35 hits display as `29/35` and 71/77 hits display as `71/77`, so shared 29/35 behavior is no longer buried under the old `71/29` label.

### Pine fixes applied
- Algo 1 terminal detection is split into `71/77` and `29/35` so `29/35` can merge cleanly with Algo 2.
- Shared-node color/merge now includes `29/35`.
- Terminal tags are algo-specific, so shared nodes like `03/7` do not appear globally terminal.
- Read-quality scoring now accepts four-value nodes, so `47/50/53/56` exact MM hits score correctly.
- Forward/minimum labels use `71/77` instead of the ambiguous old `71`/`71/29` wording.

### Remaining live check
- Pine still needs one paste into TradingView Pine Editor for a true compile check, because Pine cannot be compiled offline here.
- Back after a completed/exhausted chain now removes only the completion marker and restores the exact prior state, instead of accidentally rewinding an extra node.
