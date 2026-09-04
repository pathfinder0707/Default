/**
 * The vault: every idea in the game is a playing card you earn by calling a
 * claim correctly. Suits group them, and the rank is how hard the idea is —
 * an Ace is one most people get wrong.
 *
 * Nothing here can be bought. A card in your vault is a claim you actually
 * called right, which is the only currency the game has.
 */
export type ConceptId =
  | "expectations"
  | "duration"
  | "cashflow"
  | "passive"
  | "correlation"
  | "splits"
  | "passthrough"
  | "leverage"
  | "liquidity"
  | "inflation"
  | "compounding"
  | "moats"
  | "fees"
  | "cycles";

export type Suit = "markets" | "companies" | "money" | "risk";

export interface Concept {
  id: ConceptId;
  name: string;
  suit: Suit;
  /** Playing-card rank. Higher rank means fewer people call it correctly. */
  rank: string;
  line: string;
}

export const SUITS: Record<Suit, { label: string; glyph: string; tint: string }> = {
  markets: { label: "Markets", glyph: "♠", tint: "#eae4d6" },
  companies: { label: "Companies", glyph: "♥", tint: "#ce4a42" },
  money: { label: "Money", glyph: "♦", tint: "#d9a441" },
  risk: { label: "Risk", glyph: "♣", tint: "#3fbe8c" },
};

export const CONCEPTS: Concept[] = [
  {
    id: "passive",
    name: "How index funds actually behave",
    suit: "markets",
    rank: "A",
    line: "They do almost nothing, and that is the entire advantage.",
  },
  {
    id: "expectations",
    name: "Price is a forecast, not a scoreboard",
    suit: "markets",
    rank: "K",
    line: "The good news is already paid for before it is announced.",
  },
  {
    id: "correlation",
    name: "Correlation moves when you need it not to",
    suit: "risk",
    rank: "A",
    line: "Ten of the same bet is still one bet.",
  },
  {
    id: "duration",
    name: "Bond prices move against yields",
    suit: "money",
    rank: "K",
    line: "Rates down, your old bond is suddenly the better deal.",
  },
  {
    id: "passthrough",
    name: "Costs arrive faster than prices",
    suit: "companies",
    rank: "Q",
    line: "The lag is where the damage happens.",
  },
  {
    id: "cashflow",
    name: "Revenue is a promise, cash is a fact",
    suit: "companies",
    rank: "J",
    line: "Companies go bankrupt while growing. Often.",
  },
  {
    id: "splits",
    name: "A split changes nothing",
    suit: "markets",
    rank: "10",
    line: "Same pie, more slices, identical dinner.",
  },

  // Still in the deck.
  {
    id: "leverage",
    name: "Borrowed money cuts both ways",
    suit: "risk",
    rank: "K",
    line: "It multiplies the outcome, not the odds.",
  },
  {
    id: "liquidity",
    name: "The price is only real if you can sell",
    suit: "risk",
    rank: "Q",
    line: "Every crisis is a liquidity crisis wearing a costume.",
  },
  {
    id: "inflation",
    name: "The quiet tax on doing nothing",
    suit: "money",
    rank: "Q",
    line: "Cash is not safe, it is slowly shrinking.",
  },
  {
    id: "compounding",
    name: "Small and early beats large and late",
    suit: "money",
    rank: "J",
    line: "By more than feels arithmetically possible.",
  },
  {
    id: "moats",
    name: "Why some profits survive competition",
    suit: "companies",
    rank: "K",
    line: "Everyone else gives their profits away.",
  },
  {
    id: "fees",
    name: "The one number you control",
    suit: "money",
    rank: "10",
    line: "And the one that quietly decides the outcome.",
  },
  {
    id: "cycles",
    name: "Nothing goes one way forever",
    suit: "markets",
    rank: "Q",
    line: "The cure for high prices is high prices.",
  },
];

export const CONCEPT_BY_ID = new Map(CONCEPTS.map((c) => [c.id, c]));
