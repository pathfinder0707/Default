import type { Story } from "@/lib/types";
import { series } from "@/lib/data/series";

/**
 * Today's brief. Five stories, deliberately — the product promise is that
 * this is the whole list, not the first page of a hundred.
 *
 * The first entry is the lead and gets the large editorial treatment.
 */
export const STORIES: Story[] = [
  {
    id: "nvda-ai-demand",
    category: "AI & Semis",
    readSeconds: 40,
    headline: "Nvidia's quarter turns into a verdict on the whole AI trade",
    summary:
      "NVDA rose 4.2% after data-centre revenue came in about $2.4bn ahead of estimates and the company guided higher again.",
    assets: [
      { topicId: "nvda", symbol: "NVDA", changePct: 4.2 },
      { topicId: "semis", symbol: "SOX", changePct: 2.6 },
    ],
    sentiment: "bullish",
    whyItMatters:
      "Nvidia sells the picks and shovels for AI, so its order book is the closest thing markets have to a receipt for everyone else's AI spending. When that number beats, investors read it as proof the budgets are real and buy semiconductors, power suppliers and cloud names alongside it. When it merely meets, the same logic runs in reverse — which is why one company's guidance can set the mood for a third of the index.",
    source: "Company filing",
    minutesAgo: 42,
    chart: series(7, 42, 3.6),
  },
  {
    id: "rbi-hold-language",
    category: "Rates",
    readSeconds: 35,
    headline: "The RBI held rates, then changed one word",
    summary:
      "The repo rate stayed at 5.50%, but the stance moved from 'neutral' to 'accommodative', which markets read as a cut moving closer.",
    assets: [
      { topicId: "hdfcbank", symbol: "HDFCBANK", changePct: 1.7 },
      { topicId: "nifty", symbol: "NIFTY", changePct: 0.84 },
    ],
    sentiment: "bullish",
    whyItMatters:
      "Central banks move slowly on purpose, so the language around a decision often matters more than the decision. 'Accommodative' signals the next move is more likely to be a cut than a hike. Lower rates usually mean cheaper loans, more borrowing and better margins on lending volume — which is why bank stocks reacted before anything actually changed.",
    source: "Reserve Bank of India",
    minutesAgo: 96,
  },
  {
    id: "opec-supply",
    category: "Energy",
    readSeconds: 30,
    headline: "Oil slips under $68 as OPEC+ signals more barrels",
    summary:
      "Brent fell 2.1% after delegates indicated the group will keep unwinding production cuts through the fourth quarter.",
    assets: [{ topicId: "oil", symbol: "BRENT", changePct: -2.1 }],
    sentiment: "mixed",
    whyItMatters:
      "Cheaper crude is a tax cut for countries that import most of their energy, India included: it lowers fuel costs, eases inflation and takes pressure off the currency. It is the opposite for oil producers and energy stocks. So 'oil down' is rarely simply good or bad — it depends entirely on which side of the barrel you are standing on.",
    source: "Reuters",
    minutesAgo: 155,
  },
  {
    id: "btc-etf-flows",
    category: "Crypto",
    readSeconds: 30,
    headline: "Bitcoin grinds back toward $118k on steady ETF buying",
    summary:
      "BTC added 1.28% with spot ETFs taking in roughly $410m over four sessions, the longest inflow run since May.",
    assets: [{ topicId: "btc", symbol: "BTC", changePct: 1.28 }],
    sentiment: "bullish",
    whyItMatters:
      "Spot ETFs let pension funds and advisers hold bitcoin without touching a crypto exchange, so their flows are a rough proxy for institutional appetite. Sustained inflows tend to matter more than any single day's price, because that money usually arrives on a schedule rather than a whim — and it leaves the same way.",
    source: "Farside Investors",
    minutesAgo: 178,
  },
  {
    id: "reliance-capex",
    category: "India Inc",
    readSeconds: 35,
    headline: "Reliance is spending heavily again, and investors are fine with it",
    summary:
      "Shares rose 1.9% after the company detailed a ₹75,000 crore push into new energy and data centres over three years.",
    assets: [{ topicId: "reliance", symbol: "RELIANCE", changePct: 1.9 }],
    sentiment: "mixed",
    whyItMatters:
      "Big capital spending normally worries shareholders because it delays profits and cash returns. Investors tolerated it here because the last two Reliance build-outs — telecom and retail — eventually turned into the company's growth engines. The market is effectively paying for a track record, which is also the risk if this cycle takes longer to pay back.",
    source: "Company filing",
    minutesAgo: 210,
  },
];

/** Total read time for the whole brief, in the "2 min 20 sec" shape. */
export function totalReadTime(stories: Story[] = STORIES): string {
  const total = stories.reduce((sum, s) => sum + s.readSeconds, 0);
  const minutes = Math.floor(total / 60);
  const seconds = total % 60;
  if (!minutes) return `${seconds} sec`;
  return seconds ? `${minutes} min ${seconds} sec` : `${minutes} min`;
}
