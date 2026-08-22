import type { FeedUpdate } from "@/lib/types";

/**
 * Updates keyed to followed topics. Every topic has at least one so the
 * personalised feed responds immediately when someone changes their picks.
 *
 * The bar for appearing here is higher than for the brief: an update should
 * be something the follower would want a notification about.
 */
export const FEED_UPDATES: FeedUpdate[] = [
  {
    id: "f-nvda",
    topicId: "nvda",
    headline: "New AI chip orders came in ahead of expectations",
    detail:
      "Data-centre revenue beat estimates by roughly $2.4bn and next-quarter guidance moved up with it.",
    whyItMoved:
      "The market had already priced in a beat, so the guidance did the work. Raising the forward number tells investors demand is not a one-quarter spike.",
    changePct: 4.2,
    minutesAgo: 42,
  },
  {
    id: "f-nvda-2",
    topicId: "nvda",
    headline: "Two suppliers raised their own outlooks within the hour",
    detail:
      "Memory and networking partners followed with higher guidance, which usually confirms the order book is real.",
    whyItMoved:
      "Supplier confirmations are harder to manage than a single company's forecast — several firms raising together is a stronger demand signal than one.",
    changePct: 2.6,
    minutesAgo: 30,
  },
  {
    id: "f-gold",
    topicId: "gold",
    headline: "Gold eased after seven straight weeks of gains",
    detail:
      "Prices slipped 0.32% as the dollar firmed and traders took profit ahead of next week's inflation print.",
    whyItMoved:
      "Gold pays no interest, so it competes with cash. A stronger dollar and higher real yields make holding it costlier, and profit-taking after a long run is normal rather than a signal.",
    changePct: -0.32,
    minutesAgo: 64,
  },
  {
    id: "f-ai",
    topicId: "ai",
    headline: "Cloud providers lifted 2026 capex plans again",
    detail:
      "Combined planned spending across the four largest buyers now sits near $420bn for the year.",
    whyItMoved:
      "AI revenue is still small next to the spending. Investors are watching whether that gap narrows — capex rising faster than revenue is the risk everyone is quietly tracking.",
    minutesAgo: 88,
  },
  {
    id: "f-nifty",
    topicId: "nifty",
    headline: "NIFTY closed at a three-week high on banking strength",
    detail:
      "The index added 0.84%, with lenders contributing more than half the move after the RBI's softer language.",
    whyItMoved:
      "Financials are roughly a third of the index by weight, so when banks move, the headline number moves whether or not anything else changed.",
    changePct: 0.84,
    minutesAgo: 51,
  },
  {
    id: "f-rates",
    topicId: "rates",
    headline: "The RBI kept rates at 5.50% but softened its stance",
    detail:
      "The policy language shifted to 'accommodative', which markets read as a cut moving closer.",
    whyItMoved:
      "Rate decisions are usually priced in advance. The stance is the part that tells you about the next meeting, so that is what traders react to.",
    minutesAgo: 96,
  },
  {
    id: "f-aapl",
    topicId: "aapl",
    headline: "Apple's services revenue set another quarterly record",
    detail:
      "Services grew 13% year on year and now carries close to half the company's gross profit.",
    whyItMoved:
      "Services earn much higher margins than hardware and recur every month, so investors value that revenue more highly than an equivalent iPhone sale.",
    changePct: 0.36,
    minutesAgo: 132,
  },
  {
    id: "f-tsla",
    topicId: "tsla",
    headline: "Tesla trimmed prices across two European markets",
    detail:
      "Shares fell 1.44% as the cuts landed shortly before the quarter's delivery window closes.",
    whyItMoved:
      "Price cuts buy volume at the cost of margin. Late in a quarter they usually suggest demand needed help, which is what worries analysts more than the discount itself.",
    changePct: -1.44,
    minutesAgo: 141,
  },
  {
    id: "f-reliance",
    topicId: "reliance",
    headline: "A ₹75,000 crore capex plan landed better than expected",
    detail:
      "Shares rose 1.9% as management detailed a three-year push into new energy and data centres.",
    whyItMoved:
      "Heavy spending normally pressures the stock. Investors gave this one the benefit of the doubt because the last two build-outs eventually became the growth engine.",
    changePct: 1.9,
    minutesAgo: 210,
  },
  {
    id: "f-hdfcbank",
    topicId: "hdfcbank",
    headline: "HDFC Bank led lenders higher after the policy update",
    detail:
      "The stock added 1.7%, with deposit growth running slightly ahead of the sector.",
    whyItMoved:
      "Cheaper funding widens the gap between what a bank pays for deposits and earns on loans. That gap is most of a lender's profit.",
    changePct: 1.7,
    minutesAgo: 92,
  },
  {
    id: "f-btc",
    topicId: "btc",
    headline: "Spot ETFs took in $410m over four sessions",
    detail:
      "Bitcoin added 1.28% on the longest run of inflows since May.",
    whyItMoved:
      "ETF money tends to arrive on a schedule rather than a whim, so a steady inflow run says more about demand than a single sharp move.",
    changePct: 1.28,
    minutesAgo: 178,
  },
  {
    id: "f-oil",
    topicId: "oil",
    headline: "Brent fell under $68 on OPEC+ supply signals",
    detail:
      "Delegates indicated the group will keep unwinding production cuts through the fourth quarter.",
    whyItMoved:
      "More supply with unchanged demand means a lower clearing price. The signal matters before the barrels arrive because traders position ahead of it.",
    changePct: -2.1,
    minutesAgo: 155,
  },
  {
    id: "f-semis",
    topicId: "semis",
    headline: "The semiconductor index closed up 2.6%",
    detail:
      "Gains were broad rather than concentrated, with memory names outpacing logic.",
    whyItMoved:
      "A broad move suggests investors are buying the sector's demand outlook rather than one company's results.",
    changePct: 2.6,
    minutesAgo: 46,
  },
  {
    id: "f-banks",
    topicId: "banks",
    headline: "Bank NIFTY added 1.42%, its best day in five weeks",
    detail:
      "Private lenders led, with state banks joining in the final hour.",
    whyItMoved:
      "Rate expectations moved, and banks are the most direct way to trade that view on the Indian market.",
    changePct: 1.42,
    minutesAgo: 78,
  },
  {
    id: "f-inflation",
    topicId: "inflation",
    headline: "India's CPI came in at 3.1%, a fourth month inside target",
    detail:
      "Food prices did most of the cooling; core inflation was broadly unchanged.",
    whyItMoved:
      "Central banks watch core inflation because food and fuel swing on weather and geopolitics. A soft headline with sticky core gives them less room than it looks.",
    minutesAgo: 220,
  },
  {
    id: "f-us-markets",
    topicId: "us-markets",
    headline: "The S&P 500 closed 0.41% higher, led by technology",
    detail:
      "Breadth was narrow — six sectors finished lower even as the index rose.",
    whyItMoved:
      "When a handful of large companies carry an index, the headline number can look healthier than the average stock inside it.",
    changePct: 0.41,
    minutesAgo: 120,
  },
  {
    id: "f-rupee",
    topicId: "rupee",
    headline: "The rupee firmed to ₹87.41 as crude fell",
    detail:
      "A softer oil price reduces the dollars India needs to buy each month.",
    whyItMoved:
      "India imports most of its crude, so the oil bill is one of the largest recurring sources of dollar demand. Cheaper oil eases that pressure.",
    changePct: -0.18,
    minutesAgo: 165,
  },
];

/** Updates for the topics a user follows, newest first. */
export function updatesForTopics(topicIds: string[], limit = 4): FeedUpdate[] {
  const followed = new Set(topicIds);
  return FEED_UPDATES.filter((u) => followed.has(u.topicId))
    .sort((a, b) => a.minutesAgo - b.minutesAgo)
    .slice(0, limit);
}
