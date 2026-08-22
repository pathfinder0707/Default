import type { Quote } from "@/lib/types";
import { series } from "@/lib/data/series";

/**
 * The whole market snapshot. Six lines, chosen so an Indian and a US reader
 * both find their bearings — anything deeper belongs on a markets page,
 * not the homepage.
 */
export const SNAPSHOT: Quote[] = [
  {
    id: "nifty",
    label: "NIFTY 50",
    symbol: "NSEI",
    display: "24,842",
    changePct: 0.84,
    spark: series(11, 26, 2.2),
    blurb:
      "India's 50 largest listed companies, weighted by size. The default read on the Indian market.",
  },
  {
    id: "sensex",
    label: "SENSEX",
    symbol: "BSESN",
    display: "81,364",
    changePct: 0.71,
    spark: series(12, 26, 1.9),
    blurb:
      "The older Indian benchmark — 30 companies on the BSE. It usually tells the same story as the NIFTY.",
  },
  {
    id: "spx",
    label: "S&P 500",
    symbol: "SPX",
    display: "5,620",
    changePct: 0.41,
    spark: series(13, 26, 1.2),
    blurb:
      "The 500 biggest US companies. When people say \u201cthe market\u201d, they usually mean this.",
  },
  {
    id: "gold",
    label: "Gold",
    symbol: "XAU",
    display: "₹1,04,280",
    changePct: -0.32,
    spark: series(14, 26, -1.1),
    blurb:
      "Priced per 10 grams in India. It tends to rise when people want somewhere safe to sit.",
  },
  {
    id: "btc",
    label: "Bitcoin",
    symbol: "BTC",
    display: "$117,940",
    changePct: 1.28,
    spark: series(15, 26, 2.8),
    blurb:
      "The largest cryptocurrency. Moves on flows into spot ETFs as much as on sentiment now.",
  },
  {
    id: "brent",
    label: "Brent Crude",
    symbol: "BRENT",
    display: "$67.84",
    changePct: -2.1,
    spark: series(16, 26, -2.6),
    blurb:
      "The global oil benchmark. India imports most of its crude, so this feeds straight into inflation.",
  },
];

/** Price lines for followed topics, keyed by topic id. */
export const TOPIC_QUOTES: Record<string, Quote> = {
  nvda: {
    id: "nvda",
    label: "Nvidia",
    symbol: "NVDA",
    display: "$184.20",
    changePct: 4.2,
    spark: series(21, 24, 3.4),
  },
  aapl: {
    id: "aapl",
    label: "Apple",
    symbol: "AAPL",
    display: "$232.71",
    changePct: 0.36,
    spark: series(22, 24, 0.7),
  },
  tsla: {
    id: "tsla",
    label: "Tesla",
    symbol: "TSLA",
    display: "$341.08",
    changePct: -1.44,
    spark: series(23, 24, -1.8),
  },
  reliance: {
    id: "reliance",
    label: "Reliance",
    symbol: "RELIANCE",
    display: "₹1,486",
    changePct: 1.9,
    spark: series(24, 24, 2.1),
  },
  hdfcbank: {
    id: "hdfcbank",
    label: "HDFC Bank",
    symbol: "HDFCBANK",
    display: "₹1,972",
    changePct: 1.7,
    spark: series(25, 24, 1.6),
  },
  nifty: {
    id: "nifty",
    label: "NIFTY 50",
    symbol: "NSEI",
    display: "24,842",
    changePct: 0.84,
    spark: series(11, 24, 2.2),
  },
  "us-markets": {
    id: "us-markets",
    label: "S&P 500",
    symbol: "SPX",
    display: "5,620",
    changePct: 0.41,
    spark: series(13, 24, 1.2),
  },
  gold: {
    id: "gold",
    label: "Gold",
    symbol: "XAU",
    display: "₹1,04,280",
    changePct: -0.32,
    spark: series(14, 24, -1.1),
  },
  oil: {
    id: "oil",
    label: "Brent Crude",
    symbol: "BRENT",
    display: "$67.84",
    changePct: -2.1,
    spark: series(16, 24, -2.6),
  },
  btc: {
    id: "btc",
    label: "Bitcoin",
    symbol: "BTC",
    display: "$117,940",
    changePct: 1.28,
    spark: series(15, 24, 2.8),
  },
  semis: {
    id: "semis",
    label: "Semiconductors",
    symbol: "SOX",
    display: "5,411",
    changePct: 2.6,
    spark: series(26, 24, 2.4),
  },
  banks: {
    id: "banks",
    label: "Bank NIFTY",
    symbol: "BANKNIFTY",
    display: "54,109",
    changePct: 1.42,
    spark: series(27, 24, 1.7),
  },
  rupee: {
    id: "rupee",
    label: "USD / INR",
    symbol: "USDINR",
    display: "₹87.41",
    changePct: -0.18,
    spark: series(28, 24, -0.6),
  },
};
