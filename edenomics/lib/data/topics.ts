import type { Topic } from "@/lib/types";

/**
 * The universe a user can follow. Deliberately mixed: tickers sit next to
 * ideas like "Interest Rates", because most people think in themes first.
 */
export const TOPICS: Topic[] = [
  {
    id: "nvda",
    label: "Nvidia",
    kind: "stock",
    symbol: "NVDA",
    blurb: "Earnings, chip demand and anything that moves the AI trade.",
  },
  {
    id: "aapl",
    label: "Apple",
    kind: "stock",
    symbol: "AAPL",
    blurb: "Product cycles, services growth and supply chain shifts.",
  },
  {
    id: "tsla",
    label: "Tesla",
    kind: "stock",
    symbol: "TSLA",
    blurb: "Deliveries, margins and the autonomy story.",
  },
  {
    id: "reliance",
    label: "Reliance",
    kind: "stock",
    symbol: "RELIANCE",
    blurb: "Capex cycles, retail, telecom and energy in one company.",
  },
  {
    id: "hdfcbank",
    label: "HDFC Bank",
    kind: "stock",
    symbol: "HDFCBANK",
    blurb: "Deposit growth, margins and what rates do to Indian lenders.",
  },
  {
    id: "nifty",
    label: "Indian Markets",
    kind: "region",
    symbol: "NIFTY",
    blurb: "NIFTY 50, Sensex and the flows that set the tone in Mumbai.",
  },
  {
    id: "us-markets",
    label: "US Markets",
    kind: "region",
    symbol: "SPX",
    blurb: "S&P 500, Nasdaq and the sessions that set global risk appetite.",
  },
  {
    id: "ai",
    label: "AI",
    kind: "theme",
    blurb: "Compute spending, model releases and who is actually paying.",
  },
  {
    id: "semis",
    label: "Semiconductors",
    kind: "sector",
    blurb: "Foundries, memory pricing and export controls.",
  },
  {
    id: "banks",
    label: "Banking",
    kind: "sector",
    blurb: "Credit growth, deposit wars and asset quality.",
  },
  {
    id: "rates",
    label: "Interest Rates",
    kind: "macro",
    blurb: "Central bank decisions and what they do to your loans.",
  },
  {
    id: "inflation",
    label: "Inflation",
    kind: "macro",
    blurb: "CPI prints, food and fuel, and where prices are heading.",
  },
  {
    id: "gold",
    label: "Gold",
    kind: "commodity",
    symbol: "XAU",
    blurb: "The hedge everyone remembers only when markets wobble.",
  },
  {
    id: "oil",
    label: "Crude Oil",
    kind: "commodity",
    symbol: "BRENT",
    blurb: "OPEC+ supply, demand signals and the knock-on to inflation.",
  },
  {
    id: "btc",
    label: "Bitcoin",
    kind: "crypto",
    symbol: "BTC",
    blurb: "Price, flows into spot ETFs and regulatory turns.",
  },
  {
    id: "rupee",
    label: "Rupee",
    kind: "macro",
    symbol: "USDINR",
    blurb: "The currency line that quietly changes import bills.",
  },
];

export const TOPIC_BY_ID = new Map(TOPICS.map((t) => [t.id, t]));

/** Sensible starting feed so the "For you" section is never empty on arrival. */
export const DEFAULT_FOLLOWED = ["nvda", "gold", "ai", "nifty"];

/** Short monogram for a topic avatar — ticker beats name where one exists. */
export function topicMonogram(topic: Topic): string {
  if (topic.symbol) return topic.symbol.slice(0, 2);
  return topic.label.slice(0, 2).toUpperCase();
}
