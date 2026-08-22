# Edenomics

A homepage for a finance product built around one idea:

> Make finance useful enough to visit every day, but simple enough that it never feels like homework.

Most finance sites solve for coverage — hundreds of headlines, tickers and tables, all
competing for the same attention. Edenomics solves for the opposite problem. The scarce
resource is not information, it is judgement about which information deserves your
attention. So the homepage answers four questions in a few seconds:

**What happened? Why does it matter? Does it affect anything I care about? Can I learn
something while I'm here?**

## What's on the page

| Section | What it does |
| --- | --- |
| **Hero** | A live greeting, today's date and real session status. The panel beside it is the brief itself — a contents page of the day, not a product mockup. |
| **Daily brief** | Five stories, sized unevenly so the lead earns its space. Each one is a headline, a sentence, the tickers it moved and a folded-away "Why it matters". On phones the same five become a swipeable rail. |
| **Your market** | The same day, filtered to what you follow. Editorial cards become an app-like list, so the two sections are never mistaken for each other. |
| **Markets at a glance** | Six numbers, no table. Selecting one explains in a sentence what it actually measures. |
| **Daily challenge** | Three questions, roughly a minute. A streak, a level and XP — every question explains the concept the moment you answer, right or wrong. |
| **Money never sleeps** | An interactive globe of the five sessions that cover the trading day, with live open/closed state derived from your own clock. |
| **Follow less. Know more.** | The watchlist picker and the notification promise, side by side. |

Everything is wired together: following a company from a headline, from the command
palette (`⌘K`), or from the chip picker all write to the same store — and the
personalised feed updates immediately.

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

Bundles the whole page — CSS, JS and fonts — into one HTML file you can
double-click, email, or drop on any static host. It uses the same
`app/globals.css` and the same components, so the tokens cannot drift from the
Next build.

Two things differ by necessity: the page renders on the client rather than the
server, and three.js is bundled in rather than code-split (the globe still
waits for an IntersectionObserver before creating the WebGL context). The Next
app is the real one.

## Stack

Next.js 16 (App Router) · React 19 · TypeScript · Tailwind CSS v4 · Motion ·
React Three Fiber · lucide-react. Charts are hand-rolled SVG rather than a charting
library — a sparkline does not need 100 KB of dependency.

## Structure

```
app/                     layout, tokens, page composition
components/
  layout/                header, command palette, tab bar, footer, CTA
  news/                  hero, daily brief, story card
  markets/               snapshot, sparkline, delta
  watchlist/             personalised feed, chips, notifications
  learn/                 daily challenge, streak panel
  3d/                    globe scene, fallback, lazy section wrapper
lib/
  data/                  mock financial content — one module per domain
  state/                 localStorage-backed stores for watchlist and progress
  hooks/                 mounted, clock, scroll spy
  types.ts               every shape the UI renders
  geo.ts, market-clock.ts
scripts/gen-land-mask.mjs  regenerates the globe's land data
```

## Data

All prices, stories and figures are **illustrative sample data** — nothing here is live,
and nothing here is investment advice.

The mock content lives entirely in `lib/data`, and every component reads through the
interfaces in `lib/types.ts`. Swapping in a real API means implementing those shapes;
no component changes. `lib/data/series.ts` generates deterministic price walks from a
seed so the server and client render identical paths and the demo looks the same every
time.

## Notes on a few decisions

**The accent is amber, not green.** Market green and red appear only on price movement,
at small sizes. If something on this page changes colour, it is because a number moved.

**Progressive disclosure everywhere.** "Why it matters", "Why it moved" and the market
explainers are all folded away by default. A beginner can open them; an experienced
investor never has to look at them.

**The globe ships one bit per point.** `scripts/gen-land-mask.mjs` samples Natural Earth
land polygons against a 9,000-point Fibonacci sphere and writes a base64 bitmask
(~1.1 KB). The browser regenerates the same point positions and keeps the ones over
land — no coordinate payload, no texture. Three.js itself (229 KB gzipped) is loaded
only when the section approaches the viewport, and falls back to a static SVG globe
where WebGL is unavailable.

**Accessibility is not a pass at the end.** Semantic sectioning, one `h1`, a skip link,
visible focus on all 78 interactive elements, `aria-expanded` on every disclosure,
labelled charts, and a `prefers-reduced-motion` path that collapses durations rather
than swapping element types — that swap strands Motion's inline opacity and leaves
blocks invisible. All text clears WCAG AA contrast on every surface it sits on.
