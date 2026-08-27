# Edenomics

A finance product built as a game, on one idea:

> The market is the level. You score by knowing **why** a price moved — never by
> guessing which way it went.

Most attempts to gamify finance end up training the exact habit that costs people
money: fast, confident, directional guessing. Edenomics is arranged so that is
impossible to win at. Every round can be won by someone with no view on the
market and lost by someone who guessed right.

## The loop

**A daily run** — five rounds, about three minutes, with a combo multiplier that
carries between them. Five different shapes of thinking, so it never becomes one
quiz format wearing different hats:

| Round | What it asks | What it teaches |
| --- | --- | --- |
| **Chart call** | Read a price move, then find out what caused it | Prices move on expectations, not results |
| **Order of magnitude** | Estimate a number on a log slider | Scale intuition — the thing prices hide |
| **Chain reaction** | Put a transmission chain in order | Mechanism, not vocabulary |
| **Name the business** | Identify a company from clues, XP decaying per clue | Where profits actually come from |
| **Who wins** | One shock, three sectors | Shocks move money, they don't destroy it |

**A skill constellation** — fourteen ideas, each unlocking the next. Rounds you
win feed mastery into the node they belong to.

**A portfolio lab** — ten lakh of play money, where an asset class stays locked
until you have mastered its node. Master valuation, unlock single stocks. That is
the opposite order to every brokerage app.

**A weekly league** — nine players, promotion at the top three. Nothing at stake
but next week's bracket, and nothing that can be bought.

Everything is wired to one store, so finishing a run visibly moves the level ring,
the streak calendar, the badge shelf, the skill map and your league row at once.

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

Bundles the whole game — CSS, JS and fonts — into one ~780 KB HTML file you can
double-click, email, or drop on any static host. It makes **zero** network
requests. It uses the same `app/globals.css` and the same components, so the
tokens cannot drift from the Next build; the only difference is that it renders
on the client rather than the server.

## Stack

Next.js 16 (App Router) · React 19 · TypeScript · Tailwind CSS v4 · Motion ·
lucide-react. No charting library and no 3D engine — the charts, the donut, the
level ring and the constellation are all hand-rolled SVG, and the run's
celebration is a single canvas.

## Structure

```
app/                     layout, tokens, page composition
components/
  game/                  the run, its five round types, combo, results
  player/                level ring, streak calendar, badges
  skills/                the constellation
  portfolio/             the lab and its donut
  league/                weekly table
  layout/                HUD header, tab bar, principles, footer
lib/
  game/                  types, round content, skills, portfolio, league, format
  state/                 localStorage-backed player store
  hooks/                 mounted, clock, scroll spy
scripts/build-standalone.mjs
```

## Data

All prices, companies, figures and rivals are **illustrative sample data**. It is
a learning game: nothing here is investment advice, and nothing is for sale.

Content lives entirely in `lib/game` behind the interfaces in `lib/game/types.ts`.
Adding a sixth round type means adding a variant to that union and a renderer —
nothing else changes.

## Notes on a few decisions

**Colour is information.** Cyan is the brand, gold is XP, coral is the streak,
lime is correct, rose is wrong. Nothing else on the page is saturated, which is
why a single gold number reads as "you earned something" with no other signal.

**The hero is the game.** No screenshot, no "get started" — the run is playable
before anyone has decided whether they want it.

**Playable entirely from the keyboard.** Number keys answer, Enter advances. All
43 interactive elements are named and have a visible focus state, and every text
colour clears WCAG AA on the surface it actually sits on.

**Decoration never scrolls.** The soft glows use a `.clip-decor` utility
(`overflow: clip`, with `hidden` as fallback) rather than `overflow: hidden`.
`hidden` makes an element scrollable, so a glow poking past the right edge can be
scrolled to — the browser does exactly that when something inside takes focus,
and the whole section slides sideways under the fixed header.

**Reduced motion collapses durations** rather than swapping element types.
Swapping strands Motion's inline opacity — React never set that style, so it
never cleans it up — and the block is left invisible.
