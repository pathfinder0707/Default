/**
 * Every shape the game renders.
 *
 * A "run" is one day's play: five rounds, each a different kind of question,
 * scored with a combo that carries across them. Rounds are data, not
 * components — adding a sixth kind means adding a variant here and a renderer,
 * nothing else.
 */

export type RoundKind =
  | "chart-call"
  | "magnitude"
  | "cause-effect"
  | "identify"
  | "bull-bear";

/** Which skill node a round feeds mastery into. */
export type SkillId =
  | "markets"
  | "rates"
  | "inflation"
  | "bonds"
  | "earnings"
  | "valuation"
  | "moats"
  | "oil"
  | "gold"
  | "currency"
  | "bitcoin"
  | "diversify"
  | "compounding"
  | "fees";

interface RoundBase {
  id: string;
  kind: RoundKind;
  /** Shown on the round chip — "Chart call", "Order of magnitude". */
  kindLabel: string;
  skill: SkillId;
  /** Base award before the combo multiplier. */
  xp: number;
  /** The lesson. Shown however the round is answered. */
  teaches: string;
  /** Share of players who got it right today. */
  solvedPct: number;
}

export interface ChoiceOption {
  id: string;
  label: string;
  /** Revealed under each option after answering. */
  note: string;
}

/** Read a price move, then find out what actually caused it. */
export interface ChartCallRound extends RoundBase {
  kind: "chart-call";
  asset: string;
  ticker: string;
  setup: string;
  /** Normalised 0–1. The first `revealAt` points are shown before answering. */
  series: number[];
  revealAt: number;
  options: ChoiceOption[];
  correctId: string;
  /** The move the chart actually made, for the reveal caption. */
  outcome: string;
}

/** Estimate a number on a log slider. Scale intuition, not arithmetic. */
export interface MagnitudeRound extends RoundBase {
  kind: "magnitude";
  question: string;
  /** Slider bounds and the truth, in the same unit. */
  min: number;
  max: number;
  answer: number;
  unit: string;
  /** Renders 1.2e12 as "$1.2T". */
  format: "usd" | "inr" | "plain" | "percent";
  /** Within this ratio of the answer counts as correct (0.35 = ±35%). */
  tolerance: number;
  anchor: string;
}

/** Put a transmission chain in order. Teaches mechanism, not vocabulary. */
export interface CauseEffectRound extends RoundBase {
  kind: "cause-effect";
  trigger: string;
  /** Presented shuffled; `order` is the correct sequence of ids. */
  steps: { id: string; label: string }[];
  order: string[];
}

/** Guess the company. Extra clues cost XP. */
export interface IdentifyRound extends RoundBase {
  kind: "identify";
  clues: string[];
  options: ChoiceOption[];
  correctId: string;
}

/** One scenario, three sectors, one winner. */
export interface BullBearRound extends RoundBase {
  kind: "bull-bear";
  scenario: string;
  options: ChoiceOption[];
  correctId: string;
}

export type Round =
  | ChartCallRound
  | MagnitudeRound
  | CauseEffectRound
  | IdentifyRound
  | BullBearRound;

/** A node in the skill constellation. */
export interface Skill {
  id: SkillId;
  label: string;
  blurb: string;
  /** Layout position on the map, 0–100 in both axes. */
  x: number;
  y: number;
  /** Nodes that must be started before this one unlocks. */
  requires: SkillId[];
  /** Branch, used for colour and grouping. */
  branch: "core" | "macro" | "companies" | "hard-assets" | "personal";
  /** Asset class this node unlocks in the portfolio lab, if any. */
  unlocks?: string;
}

export interface AssetClass {
  id: string;
  label: string;
  blurb: string;
  /** Illustrative annual figures, in percent. */
  expectedReturn: number;
  volatility: number;
  /** Skill that must be mastered before this can be allocated to. */
  requires: SkillId | null;
  tint: string;
}

export interface Scenario {
  id: string;
  label: string;
  detail: string;
  /** Return by asset-class id, in percent, during this scenario. */
  moves: Record<string, number>;
}

export interface LeaguePlayer {
  id: string;
  name: string;
  xp: number;
  streak: number;
  /** True for the row representing the visitor. */
  isYou?: boolean;
}

export interface Badge {
  id: string;
  label: string;
  detail: string;
  /** Decides whether the badge is lit, from live player state. */
  earned: (state: { xp: number; streak: number; runsDone: number; bestCombo: number }) => boolean;
}

/** What a round hands back when it is answered. */
export interface RoundOutcome {
  correct: boolean;
  /** Fraction of the round's base XP earned, before the combo multiplier. */
  xpScale: number;
}
