import { COIN_FLIP_SCORE } from "@/lib/game/scoring";

/**
 * Rank comes from your average Brier score, not from how much you have
 * played. Time served earns nothing here; a coin flip parks you at 50 forever.
 */
export interface Rank {
  name: string;
  from: number;
  blurb: string;
}

export const RANKS: Rank[] = [
  { name: "Coin flipper", from: 0, blurb: "Scoring what pure chance would." },
  { name: "Hedger", from: 52, blurb: "Playing it safe. Safe scores 50." },
  { name: "Reader", from: 60, blurb: "You know some of what you know." },
  { name: "Forecaster", from: 68, blurb: "Confidence is starting to mean something." },
  { name: "Calibrated", from: 76, blurb: "When you say 80%, you're right about 80% of the time." },
  { name: "Oracle", from: 85, blurb: "Rare, and slightly suspicious." },
];

export function rankFor(averageScore: number): { rank: Rank; next: Rank | null } {
  let index = 0;
  for (let i = 0; i < RANKS.length; i++) {
    if (averageScore >= RANKS[i].from) index = i;
  }
  return { rank: RANKS[index], next: RANKS[index + 1] ?? null };
}

export interface Rival {
  id: string;
  name: string;
  score: number;
  calls: number;
  isYou?: boolean;
}

/** Illustrative table-mates. Their scores cluster where real ones do — just above a coin flip. */
export const RIVALS: Rival[] = [
  { id: "r1", name: "Meera K.", score: 79.4, calls: 214 },
  { id: "r2", name: "Devansh", score: 74.1, calls: 96 },
  { id: "r3", name: "R. Iyer", score: 71.8, calls: 340 },
  { id: "r4", name: "Tomo", score: 66.2, calls: 51 },
  { id: "r5", name: "A. Fernandes", score: 62.9, calls: 128 },
  { id: "r6", name: "Nikhil B.", score: 58.5, calls: 77 },
  { id: "r7", name: "Sana", score: 54.0, calls: 33 },
  { id: "r8", name: "Wes", score: COIN_FLIP_SCORE - 1.2, calls: 19 },
];

export function table(you: { score: number; calls: number }): Rival[] {
  return [...RIVALS, { id: "you", name: "You", score: you.score, calls: you.calls, isYou: true }]
    .sort((a, b) => b.score - a.score);
}
