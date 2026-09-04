# Edenomics

A card game about money, built on one mechanic:

> **You don't pick an answer. You flick a card — and how hard you flick it is how sure you are.**

Push the card right for *true*, left for *false*. Nudge it and you've said 55%. Shove it to
the edge and you've said 99%. Confidence stops being a number you type and becomes something
your hand commits to.

Then it is scored on **calibration, not correctness**.

## Why that matters

Scoring uses a Brier rule, which is a *proper* scoring rule — your expected score is highest
when the number you state is the number you actually believe.

| What you say | What happens | Score |
| --- | --- | --- |
| 50/50 | anything | **50**, always |
| 90% | right | **+98** |
| 90% | wrong | **−62** |
| 99% | wrong | **−96** |

There is no way to farm it by always shouting 99%, and no way to hide by always hedging. The
only winning strategy is telling the truth about what you don't know.

That is the entire anti-casino guarantee, and it is enforced by arithmetic rather than by
copy on a page. A game about money that rewarded fast confident guessing would be training
the one habit that actually costs people money.

## What you get back

The scoreboard is a **calibration curve**: your stated confidence against how often you were
really right. Perfect calibration is the diagonal. Almost everyone sags below it, and seeing
your own dots sit under the line is a more convincing argument about overconfidence than
being told ever is.

A fresh record starts seeded with the shape most people actually have — roughly honest when
hedging, increasingly overconfident the surer they claim to be — so the curve teaches
something the moment you open it.

## The rest of it

- **The vault** — every idea in the game is a playing card. It turns face-up only when you
  call its claim correctly. Nothing is purchasable.
- **Ranks** — sorted by average score, not by how much you've played. Thirty calls can
  outrank three hundred.

## Running it

```bash
npm install
npm run dev      # http://localhost:3000
npm run build
npm run lint
```

### Or open it without installing anything

```bash
npm run build:standalone   # -> dist/edenomics.html
```

The whole game — CSS, JS and fonts — in one ~690 KB file that makes **zero** network
requests. Double-click it.

## Stack

Next.js 16 · React 19 · TypeScript · Tailwind v4 · Motion · lucide-react.

No charting library, no 3D engine, no audio files. The calibration curve and the card
faces are hand-rolled SVG and CSS; every sound is a few oscillators with an envelope, which
is why the confident-miss tone drops lower the surer you were.

## Structure

```
app/                     shell, tokens, fonts
components/
  table/                 the card, the flick, the verdict, the hand summary
  curve/                 the calibration chart and the full record
  vault/  ranks/         collected ideas, the table of players
  shell/                 HUD and view switching
lib/
  game/                  scoring (Brier), claims, concepts, ranks
  state/                 localStorage-backed record
  sound.ts  haptics.ts
```

## Notes on a few decisions

**Gesture is the input, but never the only input.** Under every card is a confidence slider
and two side buttons — the same move, available precisely, with no pointer. Both paths are
first-class; the whole game is playable from the keyboard.

**Colour means exactly one thing.** Jade is *true*, crimson is *false*, brass is score. They
appear nowhere else, so a colour on this page is always an answer.

**The waiting deck is face-down.** Small thing, but a stack of blank white faces behind the
card broke the illusion instantly.

**Body copy uses a solid token, not an alpha.** `text-cream/85` renders as `oklab(… / 0.85)`,
which is genuinely hard to verify for contrast. A real value is easier to check and easier to
reason about.

**Flex centring is done with `my-auto`, not `justify-center`.** Centring a column that grows
taller than the viewport clips its top off, and the summary screen does exactly that.

## Data

All claims, figures and table-mates are **illustrative**. It is a learning game: nothing here
is investment advice, and nothing is for sale.
