import type { AssetClass, Scenario } from "@/lib/game/types";

/**
 * The portfolio lab.
 *
 * The rule that makes this more than a toy: an asset class stays locked until
 * the matching skill node is mastered. You cannot allocate to something the
 * game has not taught you yet — which is the opposite of how every real
 * brokerage app is arranged.
 */
export const ASSET_CLASSES: AssetClass[] = [
  {
    id: "cash",
    label: "Cash",
    blurb: "Loses to inflation slowly and reliably. Still the right answer sometimes.",
    expectedReturn: 6,
    volatility: 0,
    requires: null,
    tint: "#a9a3ce",
  },
  {
    id: "index",
    label: "Index funds",
    blurb: "Owning the whole market instead of guessing which part wins.",
    expectedReturn: 12,
    volatility: 15,
    requires: "diversify",
    tint: "#8fe04a",
  },
  {
    id: "bonds",
    label: "Bonds",
    blurb: "Lending to governments and companies. Dull, and that is the job.",
    expectedReturn: 7.5,
    volatility: 6,
    requires: "bonds",
    tint: "#3ddce8",
  },
  {
    id: "stocks",
    label: "Single stocks",
    blurb: "Higher ceiling, much lower floor. Concentration cuts both ways.",
    expectedReturn: 14,
    volatility: 28,
    requires: "valuation",
    tint: "#ffc845",
  },
  {
    id: "gold",
    label: "Gold",
    blurb: "No yield, no earnings. Tends to work exactly when nothing else does.",
    expectedReturn: 8,
    volatility: 14,
    requires: "gold",
    tint: "#ff7a5c",
  },
  {
    id: "crypto",
    label: "Crypto",
    blurb: "The most volatile thing here by a distance. Size it like it.",
    expectedReturn: 18,
    volatility: 62,
    requires: "bitcoin",
    tint: "#c084fc",
  },
];

/**
 * Stress tests. Each is a rough composite of how these assets behaved in a
 * real episode — enough to show that "safe" depends entirely on the shock.
 */
export const SCENARIOS: Scenario[] = [
  {
    id: "crash",
    label: "Equity crash",
    detail: "A fast, broad sell-off in shares. Think March 2020.",
    moves: { cash: 0, index: -32, bonds: 4, stocks: -41, gold: 6, crypto: -48 },
  },
  {
    id: "inflation",
    label: "Inflation shock",
    detail: "Prices jump and central banks raise hard. Think 2022.",
    moves: { cash: -6, index: -18, bonds: -13, stocks: -24, gold: 2, crypto: -64 },
  },
  {
    id: "boom",
    label: "Long expansion",
    detail: "Growth without a scare. The years nobody writes about.",
    moves: { cash: 6, index: 24, bonds: 5, stocks: 33, gold: -4, crypto: 71 },
  },
];

export interface PortfolioStats {
  expectedReturn: number;
  volatility: number;
  /** Crude concentration read, 0–1. Anything over ~0.5 is a warning. */
  concentration: number;
}

/**
 * Weighted stats for an allocation. Volatility is deliberately naive — it
 * ignores correlation, which would overstate the benefit of diversification
 * rather than understate it, so the lab never flatters a portfolio.
 */
export function portfolioStats(allocation: Record<string, number>): PortfolioStats {
  const total = Object.values(allocation).reduce((sum, v) => sum + v, 0) || 1;
  let expectedReturn = 0;
  let volatility = 0;
  let sumOfSquares = 0;

  for (const asset of ASSET_CLASSES) {
    const weight = (allocation[asset.id] ?? 0) / total;
    expectedReturn += weight * asset.expectedReturn;
    volatility += weight * asset.volatility;
    sumOfSquares += weight * weight;
  }

  return { expectedReturn, volatility, concentration: sumOfSquares };
}

/** What this allocation would have done in a given scenario, in percent. */
export function scenarioReturn(
  allocation: Record<string, number>,
  scenario: Scenario,
): number {
  const total = Object.values(allocation).reduce((sum, v) => sum + v, 0) || 1;
  return ASSET_CLASSES.reduce((sum, asset) => {
    const weight = (allocation[asset.id] ?? 0) / total;
    return sum + weight * (scenario.moves[asset.id] ?? 0);
  }, 0);
}

export const STARTING_BALANCE = 1_000_000;
