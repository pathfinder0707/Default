/**
 * Shared shapes for every piece of content on the homepage.
 *
 * Everything the UI renders comes from these types, so swapping the mock
 * modules in `lib/data` for a real API means implementing the same shapes —
 * no component needs to change.
 */

export type TopicKind =
  | "stock"
  | "index"
  | "crypto"
  | "commodity"
  | "sector"
  | "theme"
  | "macro"
  | "region";

/** Something a user can follow: a company, an index, or an idea. */
export interface Topic {
  id: string;
  label: string;
  kind: TopicKind;
  /** Ticker where one exists — companies and indices have them, "AI" does not. */
  symbol?: string;
  /** One line explaining what following this actually gets you. */
  blurb: string;
}

export type Direction = "up" | "down" | "flat";

/** A price line, used by the market strip and the watchlist rail. */
export interface Quote {
  id: string;
  label: string;
  symbol: string;
  /** Pre-formatted so currency and locale rules live with the data. */
  display: string;
  changePct: number;
  /** ~24 normalised points, 0–1, for the sparkline. */
  spark: number[];
  /** Plain-English answer to "what even is this?", shown on demand. */
  blurb?: string;
}

export type Sentiment = "bullish" | "bearish" | "mixed";

/** A ticker badge attached to a story. */
export interface StoryAsset {
  topicId: string;
  symbol: string;
  changePct: number;
}

export interface Story {
  id: string;
  /** Editorial section — "AI & Semis", "Rates", "Energy". */
  category: string;
  /** Drives the "35 sec" read estimate. */
  readSeconds: number;
  headline: string;
  /** One sentence. The whole event, without opening an article. */
  summary: string;
  assets: StoryAsset[];
  sentiment: Sentiment;
  /** Progressive disclosure: the context a beginner is missing. */
  whyItMatters: string;
  source: string;
  /** Minutes ago, so the page always reads as "today". */
  minutesAgo: number;
  /** Only the lead story draws a chart. */
  chart?: number[];
}

/** An update in the personalised feed, tied to a followed topic. */
export interface FeedUpdate {
  id: string;
  topicId: string;
  headline: string;
  detail: string;
  whyItMoved: string;
  /** Absent for themes like "AI" that have no single price. */
  changePct?: number;
  minutesAgo: number;
}

export interface ExchangeMarket {
  id: string;
  city: string;
  country: string;
  indexName: string;
  indexValue: string;
  changePct: number;
  lat: number;
  lng: number;
  /** IANA zone, used to derive open/closed state from the visitor's clock. */
  timeZone: string;
  /** Local trading hours, 24h decimal (9.25 = 09:15). */
  opens: number;
  closes: number;
}

export type ChallengeKind = "prediction" | "company" | "bull-bear";

export interface ChallengeOption {
  id: string;
  label: string;
  /** Shown under the option once the user has answered. */
  note: string;
}

export interface Challenge {
  id: string;
  kind: ChallengeKind;
  /** "Market prediction", "Guess the company", "Bull or bear". */
  kindLabel: string;
  prompt: string;
  /** Revealed one at a time in the guess-the-company round. */
  clues?: string[];
  options: ChallengeOption[];
  correctId: string;
  /** The actual lesson — shown whether the answer was right or wrong. */
  explanation: string;
  xp: number;
  /** Share of players who got it right today, for the social nudge. */
  solvedPct: number;
}
