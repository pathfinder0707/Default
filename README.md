# GB-Time Trader

A single self-contained HTML file — `gb-time-trader.html`. No dependencies, no build,
no network. Open it in any browser, works offline, remembers your settings.

Built from `GB_FINAL_HANDOFF.md`, `GB_NEW_CHAT_HANDOFF_MULTI_SWING.md`,
`GB_FINAL_IMPLEMENTATION_NOTES.md` and `tools-handoff-fixed.md`.

Seven tabs, keyboard `1`–`7`:
**LIVE · PATH ID · CONFLUENCE · WALK · CE WALK · TRADE · SETTINGS**

---

# How to actually trade with it

## Before the session — 30 seconds

1. **SETTINGS** (`7`) — check your killzone windows against your own charts, and confirm
   the contract value for the pair you're trading. Do this once; it persists.
2. **LIVE** (`1`) — hit **🔔 Alerts off** to turn alerts on. Do this every session; browsers
   need a click before they'll play sound. Allow the notification prompt.
3. Leave the tab open on a second screen or phone.

## During the session — the actual loop

### Step 1 · Two confirmed swings appear → identify the path

You need **confirmed** pivots — a swing that already has its right-side candles printed.
Don't use a live, unconfirmed high or low.

Go to **PATH ID** (`2`). Enter each swing's time, mark ▲ high or ▼ low, hit **+ Add swing**.
Add them oldest first.

Read the **path state**:

| State | What to do |
|---|---|
| **Algo 1 / Algo 2 locked** + confidence **strong** | Trust the projection. This is your path. |
| **locked** + confidence **medium** | Usable. Wait for a cleaner reaction at the node. |
| **A1 / A2 leaning** | Not confirmed. Add another swing before you lean on it. |
| **ambiguous A1/A2** | Don't pick. Fall back to minimum travel — the floor is still valid. |
| **terminal reached** | Path is finished. Projections stop. Wait for a fresh swing sequence. |

Two swings gives you a read. **Three or more is what actually locks it.** If you're stuck
ambiguous, add another swing before touching the lock margin.

Then hit **Send to LIVE runner →**.

### Step 2 · LIVE is now your screen

The big number on the right is the **countdown to the next decision**. That's the whole point
of the tool — you stop watching the clock and it tells you when something is due.

- **Node name** — what level is coming
- **strong / medium / weak** — MM-exact / MM ±1 / secondary-only. Grade of the read.
- **Countdown** goes amber at your lead time, gold when due
- **via** — which method produced it

The three cells under the clock are the live reads. Gold means that read is hitting a node
right now. `ON NODE` in the banner means a decision is live *this minute*.

**No path locked?** LIVE falls back to **minimum travel** — the nearest node across both
algos. That's still tradeable. It's the floor: the minimum the clock expects price to reach.

### Step 3 · The node prints — watch, don't enter

This is the single most important habit and the tool enforces it.

A node is a **decision level**. Price will hold it as support, hold it as resistance, or
break through it. You do not know which until it happens. Entering *at* the node time is
guessing.

Wait for the reaction. Then go to **TRADE** (`6`).

### Step 4 · TRADE — gate, then size

Tick only what is **actually true**. Four items are hard requirements:

- Price is at / just left a GB-time node
- **I have SEEN the reaction at the node**
- HTF bias / draw on liquidity agrees
- tCISD confirmed on entry timeframe

Miss any one of the four and the grade is **NO**, no matter how many other boxes are green.
That's deliberate. Time tells you *when*. It never tells you *which way* — HTF bias and
tCISD are what do that.

| Grade | Meaning |
|---|---|
| **A+ / A** | Full context. Size normally. |
| **B** | Marginal. Half size, or pass. |
| **C / NO** | Don't. The next node is minutes away; passing costs nothing. |

Then enter your entry and stop and the sizer gives you lots for your risk %. Target is
optional but it shows you R — and the **next node is your natural target boundary**. Don't
plan a target through the next node; that's where price faces its next decision.

### Step 5 · In the trade

Keep **LIVE** open. The countdown now tells you when your position faces its next decision
point. That's your management signal — not a fixed TP.

If you want to follow the sequence node by node, use **WALK** §2: it shows the whole path
with a cursor, and you tag each node as *held support / held resistance / broke through* as
it plays out.

---

## When to use the other tabs

- **CONFLUENCE** (`3`) — quick read on one or two swings without building a full path. Use it
  when you just want "what is this swing, and what's next?" The **agree** verdict — both algos
  pointing at the same next node — is the strongest single time read available.
- **WALK** (`4`) — §1 walks minimum travel step by step. §2 walks a full algo path with
  reactions. Use §2 when you're tracking one sequence through a session.
- **CE WALK** (`5`) — CE-alternate-only chain, when you're working the CE layer specifically.

---

## The one thing this tool will not do

It will not tell you which way price goes. The handoff is explicit that nodes are decision
levels, not directional signals, so there is no direction output anywhere in it and nothing
is coloured bullish or bearish.

What it does is remove the three ways this framework normally loses money:

- **Missing the node** — countdown, upcoming list, sound and browser alerts
- **Front-running the node** — the gate refuses to grade a setup where you haven't seen the reaction
- **Trading a weak read** — every read is graded strong / medium / weak, and you can restrict
  alerts to MM-exact nodes inside killzones only

---

# Framework, as implemented

- Three reads per Zurich `HH:MM` — `MM` (**primary, wins the label**), `HH+MM`, `|HH−MM|`.
  All three checked independently, ±1.
- **Algo 1 forward** — `00 → 11/14 → 41/44 → 03/7 → 17/23 → 71/77 or 29/35 ⊣` (index **+1**)
- **Algo 2 reverse** — `29/35 → 47/53 → 11/14 → 17/23 → 59/65 → 03/7 ⊣` (index **−1**)
- Minimum travel = nearest upcoming node **in clock time**, compared by minutes-ahead so it
  is midnight-safe.
- Read quality is a **max**, never a sum: MM exact = strong, MM ±1 = medium, secondary = weak.

## Bugs fixed from the previous HTML build

Both were in `ceMin()`, both reproducible in the old file:

1. **Algo 2 was silently dropped from every CE minimum comparison.** The A2 branch never set
   `time`, so `filter(x => x.time)` discarded it — a CE walk starting anywhere on the A2 chain
   returned `exhausted` immediately. It looked like it worked and simply never walked.
2. **`times` was assigned a string instead of the array**, so the renderer's `s.times.map(...)`
   would throw as soon as A2 ever won a step.

CE walk now completes the full reverse chain `35 → 50/56 → 14 → 23 → 65 → 7 ⊣`.

## Assumptions worth checking

- **Killzone windows are not in the handoff.** Defaults are the usual ICT windows converted to
  Zurich (London 08:00–11:00, NY AM 13:00–16:00, London Close 16:00–18:00, Asia 01:00–05:00,
  NY PM 18:00–20:00). They shift with Zurich/NY DST alignment. Editable in Settings.
- **Contract values vary by broker.** XAUUSD `100` per $1.00/lot, GBPUSD `100000` per 1.0000
  ($10/pip), NAS100 `1` per index point. Editable in Settings.
- Secondary-method hits are **off** by default on the live list so it stays MM-driven.

## Verification

88 headless assertions on the engine — the three reads, the 11:03 worked example,
MM-over-secondary label priority, both full algo chains, Algo 2's reverse direction, terminal
and shared-`29/35` handling, midnight-safe minimum travel, adjacent-minute dedupe, killzone
midnight wrap, the scorer (lock/lean/skip limits/penalties/confidence), the CE fix and the
grade gate. All pass. Every tab driven in Chromium, zero console errors, desktop and mobile.

---

# Pine indicator

`handoff/gb-time-multi-swing-path-scorer-final.pine` — statically reviewed and patched:

- **`f_firstFutureTime` had no early exit** — it scanned the full forward window (up to 720
  minutes) on every bar, twice per bar, even after finding the first hit. Now `break`s on the
  first match. This was the script's main performance risk.
- **The last-valid-node scan now breaks** once both algos have their node instead of walking
  the whole history every bar.
- **`int()` casts** added where `math.min`/`math.max` results feed `for`-loop bounds and
  typed-parameter functions, and the `bestCode` pick replaced with a plain comparison — Pine
  rejects a float where a `series int` is expected.

Structurally verified offline (destructuring arity vs return arity, call arity vs declaration,
reserved-name collisions, 4-space indent rule, bracket balance) — clean. **Pine cannot be
compiled outside TradingView, so this still needs one paste into the Pine Editor for a true
compile check.** I have not claimed it compiles.
