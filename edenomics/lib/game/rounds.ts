import type { Round } from "@/lib/game/types";
import { pumpAndFade } from "@/lib/data/series";

/**
 * Today's run. Five rounds, five different shapes of thinking:
 * read a move, judge a size, order a mechanism, identify a business, and
 * work out who benefits.
 *
 * The rule every round follows: you cannot win it by guessing which way a
 * price went. You win by knowing why it went.
 */
export const RUN: Round[] = [
  {
    id: "r1-chart",
    kind: "chart-call",
    kindLabel: "Chart call",
    skill: "earnings",
    xp: 100,
    solvedPct: 61,
    asset: "Nvidia",
    ticker: "NVDA",
    setup:
      "Nvidia beat earnings by a wide margin and raised guidance. The chart below is the two hours after the release.",
    series: pumpAndFade(41, 40, 17, 0.22),
    revealAt: 18,
    outcome: "It gave back most of the pop and closed up just 0.4%.",
    options: [
      {
        id: "rip",
        label: "Kept ripping higher",
        note: "The obvious read — and the one that loses money most often.",
      },
      {
        id: "fade",
        label: "Faded most of the gain",
        note: "Correct. The beat was already in the price before it was announced.",
      },
      {
        id: "crash",
        label: "Sold off hard",
        note: "A genuine beat rarely causes a crash. Something else would have to break.",
      },
    ],
    correctId: "fade",
    teaches:
      "Prices move on the gap between results and expectations, not on results. When a stock has run up for weeks into an event, the good news is already paid for — so a beat that merely matches the whisper number gets sold. This is why \"good news, stock down\" is normal rather than irrational.",
  },
  {
    id: "r2-magnitude",
    kind: "magnitude",
    kindLabel: "Order of magnitude",
    skill: "valuation",
    xp: 120,
    solvedPct: 34,
    question: "What is Apple worth in total?",
    anchor: "For scale: the entire Indian stock market is about $5 trillion.",
    min: 5e10,
    max: 1e13,
    answer: 3.4e12,
    unit: "market cap",
    format: "usd",
    tolerance: 0.35,
    teaches:
      "Most people are fluent with prices and hopeless with sizes, which is how a \"cheap\" ₹20 stock feels safer than a ₹4,000 one. Market cap — price times share count — is the only number that says what a company actually costs. Apple at roughly $3.4tn is worth about two thirds of every listed Indian company combined.",
  },
  {
    id: "r3-cause",
    kind: "cause-effect",
    kindLabel: "Chain reaction",
    skill: "rates",
    xp: 140,
    solvedPct: 48,
    trigger: "The central bank raises interest rates.",
    // Presented out of order; `order` holds the answer.
    steps: [
      { id: "s3", label: "Demand cools, and price rises slow down" },
      { id: "s1", label: "Banks reprice loans, so borrowing costs more" },
      { id: "s2", label: "Households and firms borrow and spend less" },
    ],
    order: ["s1", "s2", "s3"],
    teaches:
      "A rate rise does not touch prices directly — it works through borrowing. That chain takes roughly four to six quarters to run, which is why central banks look like they are reacting late. They are actually aiming at where inflation will be, not where it is.",
  },
  {
    id: "r4-identify",
    kind: "identify",
    kindLabel: "Name the business",
    skill: "moats",
    xp: 110,
    solvedPct: 72,
    clues: [
      "Almost none of its revenue comes from selling a product to you",
      "It takes a cut of a transaction it never touches",
      "Two companies control most of this market worldwide",
      "Its network is worth more the more shops accept it",
    ],
    options: [
      { id: "visa", label: "Visa", note: "Correct. A toll booth on spending, not a lender." },
      { id: "hdfc", label: "HDFC Bank", note: "A bank earns on loans and deposits — quite different." },
      { id: "paytm", label: "Paytm", note: "Closer, but it competes inside a network rather than owning one." },
      { id: "amazon", label: "Amazon", note: "It very much sells products to you." },
    ],
    correctId: "visa",
    teaches:
      "The strongest businesses often sit beside the transaction rather than in it. Visa does not lend money or carry credit risk; it charges a small fee for the rails. Because every extra merchant makes the card more useful to every cardholder, the advantage compounds on its own — the textbook network moat.",
  },
  {
    id: "r5-bullbear",
    kind: "bull-bear",
    kindLabel: "Who wins",
    skill: "oil",
    xp: 130,
    solvedPct: 55,
    scenario: "Crude oil jumps 20% in a week after a supply disruption.",
    options: [
      {
        id: "explorers",
        label: "Oil producers",
        note: "Correct. They sell the barrel, so the whole price rise lands in revenue.",
      },
      {
        id: "airlines",
        label: "Airlines",
        note: "Fuel is up to a third of their costs, and ticket prices adjust slowly.",
      },
      {
        id: "paints",
        label: "Paint makers",
        note: "Crude derivatives are a core raw material — margins get squeezed.",
      },
    ],
    correctId: "explorers",
    teaches:
      "A price shock moves money rather than destroying it: producers gain roughly what heavy users lose. The pain concentrates in businesses that buy crude and cannot reprice quickly — airlines, paints, chemicals, logistics. For an oil-importing country the same logic scales up: the bill rises, the currency softens, and inflation follows a quarter later.",
  },
];

/** Multiplier for an answer streak of N. Caps so a run can't run away. */
export const COMBO_STEPS = [1, 1.25, 1.5, 2, 2.5] as const;

export function comboMultiplier(streak: number): number {
  if (streak <= 0) return 1;
  return COMBO_STEPS[Math.min(streak, COMBO_STEPS.length - 1)];
}

/** Highest score obtainable in a run, for the results screen. */
export const PERFECT_RUN_XP = RUN.reduce(
  (total, round, index) => total + Math.round(round.xp * comboMultiplier(index)),
  0,
);
