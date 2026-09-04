import type { ConceptId } from "@/lib/game/concepts";

/**
 * Today's hand. Seven claims, each one a mechanism rather than a fact you
 * could look up — so the answer follows from understanding how money moves,
 * not from remembering a number.
 *
 * Several are deliberately counterintuitive. The point of the game is to find
 * out where your confidence and your knowledge disagree, and that only happens
 * on claims where the obvious answer is sometimes wrong.
 */
export interface Claim {
  id: string;
  /** The card face. Short enough to read in one breath. */
  statement: string;
  isTrue: boolean;
  concept: ConceptId;
  /** Shown after the verdict. This is the actual product. */
  explanation: string;
  /** Share of players who called it correctly. */
  solvedPct: number;
}

export const HAND: Claim[] = [
  {
    id: "c1-beat",
    statement: "A company beats earnings and raises guidance, so its shares go up that day.",
    isTrue: false,
    concept: "expectations",
    solvedPct: 41,
    explanation:
      "Prices already contain the forecast. By the time results land, the beat everyone expected has been paid for — so a good number that merely matches the whisper gets sold. This is why “good news, stock down” is ordinary rather than irrational, and why chasing a company because it is doing well is not a strategy.",
  },
  {
    id: "c2-duration",
    statement: "When a central bank cuts rates, the bonds you already own become worth more.",
    isTrue: true,
    concept: "duration",
    solvedPct: 54,
    explanation:
      "Your bond pays a fixed coupon. If new bonds are issued paying less, yours is suddenly the better deal, so its price rises until the return matches. That is the whole of it — bond prices and yields move in opposite directions, always, mechanically. The longer the bond, the more violently it swings.",
  },
  {
    id: "c3-cashflow",
    statement: "A company can grow its revenue every single year and still go bankrupt.",
    isTrue: true,
    concept: "cashflow",
    solvedPct: 68,
    explanation:
      "Revenue is a promise; cash is a fact. Companies fail while growing all the time — they sell on credit, pay suppliers sooner than customers pay them, and run out of money in the gap. Growth actually widens that gap. “Profitable on paper, dead in the bank” is the most common way a good business dies.",
  },
  {
    id: "c4-index",
    statement: "An index fund has to sell a stock when its price falls.",
    isTrue: false,
    concept: "passive",
    solvedPct: 37,
    explanation:
      "It does nothing at all. A fund tracking a market-cap index holds a fixed number of shares; when a price falls, the holding's weight falls with it automatically. That is why index funds trade so little and cost so little. They only transact when the index composition changes, or when you put money in or take it out.",
  },
  {
    id: "c5-correlation",
    statement: "Combining two investments that both tend to rise always lowers your risk.",
    isTrue: false,
    concept: "correlation",
    solvedPct: 46,
    explanation:
      "Only if they fall at different times. Two things that rise together also crash together, and in a real panic almost everything becomes correlated at once — which is precisely when you needed the diversification. Owning ten technology stocks is owning one bet ten times.",
  },
  {
    id: "c6-split",
    statement: "A stock split makes the people who own the shares wealthier.",
    isTrue: false,
    concept: "splits",
    solvedPct: 72,
    explanation:
      "Same pie, more slices. Two shares at ₹500 is exactly one share at ₹1,000. Nothing about the business changed. Splits are done because a lower headline price feels approachable, which tells you something interesting about how prices are read — the number on the sticker is not the price of the company.",
  },
  {
    id: "c7-oil",
    statement: "When oil doubles, an airline feels it before you do.",
    isTrue: true,
    concept: "passthrough",
    solvedPct: 63,
    explanation:
      "Fuel is bought roughly now; fares are set in advance and compete against every other airline. So the cost lands immediately and the recovery arrives slowly, if at all. That lag is where the damage happens, and it is the same lag that makes an oil shock show up in your bills a quarter after it shows up in the news.",
  },
];
