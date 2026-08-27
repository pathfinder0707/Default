import type { Badge, LeaguePlayer } from "@/lib/game/types";

/**
 * The weekly league. Eight other players, promotion at the top three,
 * relegation at the bottom two — the visitor's row is spliced in live so the
 * table reorders the moment a run finishes.
 */
export const LEAGUE_NAME = "Silver league";
export const PROMOTION_SPOTS = 3;
export const RELEGATION_SPOTS = 2;

export const RIVALS: LeaguePlayer[] = [
  { id: "p1", name: "Meera K.", xp: 4820, streak: 31 },
  { id: "p2", name: "Devansh", xp: 4410, streak: 12 },
  { id: "p3", name: "R. Iyer", xp: 3980, streak: 19 },
  { id: "p4", name: "Tomo", xp: 3240, streak: 7 },
  { id: "p5", name: "A. Fernandes", xp: 2890, streak: 4 },
  { id: "p6", name: "Nikhil B.", xp: 2455, streak: 22 },
  { id: "p7", name: "Sana", xp: 1930, streak: 3 },
  { id: "p8", name: "Wes", xp: 1240, streak: 1 },
];

/** Rivals plus the visitor, ranked. */
export function standings(you: { xp: number; streak: number }): LeaguePlayer[] {
  return [...RIVALS, { id: "you", name: "You", xp: you.xp, streak: you.streak, isYou: true }].sort(
    (a, b) => b.xp - a.xp,
  );
}

export const BADGES: Badge[] = [
  {
    id: "opening-bell",
    label: "Opening bell",
    detail: "Finish your first run.",
    earned: (s) => s.runsDone >= 1,
  },
  {
    id: "four-figures",
    label: "Four figures",
    detail: "Bank 1,000 XP.",
    earned: (s) => s.xp >= 1000,
  },
  {
    id: "fortnight",
    label: "Fortnight",
    detail: "Hold a 14 day streak.",
    earned: (s) => s.streak >= 14,
  },
  {
    id: "full-combo",
    label: "Full combo",
    detail: "Clear all five rounds without a miss.",
    earned: (s) => s.bestCombo >= 5,
  },
  {
    id: "analyst",
    label: "Analyst",
    detail: "Reach 3,200 XP.",
    earned: (s) => s.xp >= 3200,
  },
  {
    id: "marathon",
    label: "Marathon",
    detail: "Hold a 30 day streak.",
    earned: (s) => s.streak >= 30,
  },
];

/**
 * Level curve. Each level costs 200 XP more than the last, so early levels
 * arrive fast and later ones stay meaningful.
 */
export function levelFor(xp: number): {
  level: number;
  into: number;
  span: number;
} {
  let level = 1;
  let span = 500;
  let floor = 0;

  while (xp >= floor + span) {
    floor += span;
    span += 200;
    level += 1;
  }

  return { level, into: xp - floor, span };
}

export const LEVEL_TITLES = [
  "Newcomer",
  "Reader",
  "Tracker",
  "Analyst",
  "Strategist",
  "Allocator",
  "Macro head",
  "Veteran",
];

export function levelTitle(level: number): string {
  return LEVEL_TITLES[Math.min(level - 1, LEVEL_TITLES.length - 1)];
}
