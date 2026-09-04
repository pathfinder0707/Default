# Edenomics — seven rooms

`index.html` is the whole thing. One file, no build step, no dependencies, no network calls
beyond a Google Fonts stylesheet. Open it and it runs.

> Seven rooms. Each one measures something different about how you handle money — and none
> of them can be won by guessing harder.

## The spine

A tab bar full of unrelated toys is a menu, not a product. What holds these together is **one
record**: each room contributes exactly one reading to a seven-part portrait of the player.
You cannot grind it, because no room can raise a trait that belongs to another room.

| Room | Trait | Reading is |
| --- | --- | --- |
| The Table | Calibration | Average Brier score over seven claims |
| The Terrarium | Structure | Best-spread tank you built before the storm |
| Boss Rush | Cost sense | How close your call was to the real fee damage |
| Ghost Lives | Patience | *declared* — what you did in the crash |
| The Bubble Room | Timing | Share of the peak price you walked away with |
| The Sleep Test | Risk appetite | *declared* — the line you drew for yourself |
| The Audit | Scepticism | How many of the three related red flags you marked |

Five readings are **earned** — you can be wrong. Two are **declared** — there is no wrong
answer, and the record renders those differently (a marker on a track, not a fill). Not
everything about money is a test, and the interface should not pretend otherwise.

## What each room actually teaches

- **The Table** — Brier scoring is a *proper* rule: expected score is maximised by stating
  your true belief. Drag distance encodes confidence, so a shove to the edge is a claim of
  99% and costs −96 when it's wrong. Claims are mechanisms, not lookups: an earnings beat
  does not mean the share rises, a rate cut raises the value of a bond you already hold.
- **The Terrarium** — correlated holdings share an animation phase, so they visibly drift in
  lockstep. Three great companies read as one bet before anything goes wrong.
- **Boss Rush** — you call the fee damage *before* the fight, so the room scores your
  estimate rather than your weapon. 0.20% vs 1.80% over 30 years is ₹2.17 Cr vs ₹1.40 Cr on
  ₹10 lakh at 11% gross. Almost everyone guesses low.
- **Ghost Lives** — the counterfactual, drawn. Selling to cash costs ₹1.07 Cr; even a
  three-year round trip costs ₹22 lakh. The cost of panic is the recovery you missed.
- **The Bubble Room** — the chart draws live, the room talks to you, and you get one press of
  SELL. Nobody rings a bell at the top.
- **The Sleep Test** — risk in rupees, not percentages, and no score at all. ₹26 lakh gone in
  one year at 100% equity, 49 months to get back.
- **The Audit** — six lines, all good news, company in trouble. Receivables up 96%, cash from
  operations negative, auditor replaced in Q3. One problem in three places.

## Notes on the build

- **No framework.** A seven-view router, seven mount functions, and a record. React would
  have been more code and one more failure mode.
- **Drag is hand-rolled** on pointer events with `setPointerCapture`, writing straight to
  `style.transform` — no per-frame React renders to avoid, because there are none.
- **Sound is synthesised** with oscillators and envelopes: no audio files, and the
  `AudioContext` is created on the first gesture rather than on load.
- **Colour has one job.** The corridor is achromatic aubergine; each room supplies the only
  saturated colour on screen through a single `--acc` token that the shell re-points on
  entry.
- **The record is per-viewer**, in `localStorage`, wrapped in try/catch so private-mode
  browsers still play. Nothing is sent anywhere. A shared server-side store was considered
  and rejected: without per-user scoping every viewer would overwrite the same profile.
- **Reduced motion** collapses durations rather than swapping element types — swapping
  strands an inline `opacity` that React never set and therefore never cleans up, which is
  how sections end up invisible.

## Data

All companies, claims and figures are **illustrative sample data**. It is a learning game:
nothing here is investment advice and nothing is for sale.

## Relationship to the app in `../`

`../` is the Next.js build of **The Table** alone, at more depth — a calibration curve over
your full history, a vault of collectible concepts, and ranks by average score. This
directory is the wider product: all seven rooms, one file.
