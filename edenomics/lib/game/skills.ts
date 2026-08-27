import type { Skill, SkillId } from "@/lib/game/types";

/**
 * The skill constellation.
 *
 * Coordinates are hand-placed on a 0–100 grid rather than force-directed: a
 * map you can learn the shape of is worth more than one that is mathematically
 * tidy, and the branches need to read as branches.
 */
export const SKILLS: Skill[] = [
  {
    id: "markets",
    label: "How markets work",
    blurb: "Price is a negotiation about the future, not a measurement of the present.",
    x: 50,
    y: 50,
    requires: [],
    branch: "core",
  },

  // Macro — up and left.
  {
    id: "rates",
    label: "Interest rates",
    blurb: "The price of money. It sets the price of everything else.",
    x: 30,
    y: 30,
    requires: ["markets"],
    branch: "macro",
  },
  {
    id: "inflation",
    label: "Inflation",
    blurb: "Why the same salary buys less each year, and who it hurts most.",
    x: 14,
    y: 18,
    requires: ["rates"],
    branch: "macro",
  },
  {
    id: "bonds",
    label: "Bonds",
    blurb: "Lending, not owning. Boring on purpose — and that is the point.",
    x: 16,
    y: 43,
    requires: ["rates"],
    branch: "macro",
    unlocks: "bonds",
  },

  // Companies — up and right.
  {
    id: "earnings",
    label: "Earnings",
    blurb: "What a company actually made, and how often that differs from the headline.",
    x: 70,
    y: 30,
    requires: ["markets"],
    branch: "companies",
  },
  {
    id: "valuation",
    label: "Valuation",
    blurb: "What a business costs versus what it earns. Where most mistakes live.",
    x: 86,
    y: 19,
    requires: ["earnings"],
    branch: "companies",
    unlocks: "stocks",
  },
  {
    id: "moats",
    label: "Moats",
    blurb: "Why some companies keep their profits and others give them away.",
    x: 87,
    y: 44,
    requires: ["earnings"],
    branch: "companies",
  },

  // Hard assets — down and right.
  {
    id: "oil",
    label: "Oil",
    blurb: "The input almost every other price is quietly built on.",
    x: 72,
    y: 71,
    requires: ["markets"],
    branch: "hard-assets",
  },
  {
    id: "gold",
    label: "Gold",
    blurb: "Pays nothing, promises nothing, and people still want it. Understand why.",
    x: 87,
    y: 82,
    requires: ["oil"],
    branch: "hard-assets",
    unlocks: "gold",
  },
  {
    id: "currency",
    label: "Currency",
    blurb: "The rupee line that silently changes the price of everything imported.",
    x: 58,
    y: 86,
    requires: ["oil"],
    branch: "hard-assets",
  },
  {
    id: "bitcoin",
    label: "Bitcoin",
    blurb: "What it is, what it isn't, and what actually moves it now.",
    x: 74,
    y: 96,
    requires: ["currency"],
    branch: "hard-assets",
    unlocks: "crypto",
  },

  // Personal — down and left.
  {
    id: "diversify",
    label: "Diversification",
    blurb: "The only thing in finance that is genuinely free.",
    x: 30,
    y: 70,
    requires: ["markets"],
    branch: "personal",
    unlocks: "index",
  },
  {
    id: "compounding",
    label: "Compounding",
    blurb: "Small and early beats large and late, by more than feels possible.",
    x: 14,
    y: 79,
    requires: ["diversify"],
    branch: "personal",
  },
  {
    id: "fees",
    label: "Fees",
    blurb: "The one number you control, and the one that quietly wins.",
    x: 32,
    y: 94,
    requires: ["diversify"],
    branch: "personal",
  },
];

export const SKILL_BY_ID = new Map(SKILLS.map((s) => [s.id, s]));

/** Edges of the constellation, derived from `requires`. */
export const SKILL_EDGES: { from: SkillId; to: SkillId }[] = SKILLS.flatMap((skill) =>
  skill.requires.map((from) => ({ from, to: skill.id })),
);

export const BRANCH_TINTS: Record<Skill["branch"], string> = {
  core: "#f4f2ff",
  macro: "#3ddce8",
  companies: "#ffc845",
  "hard-assets": "#ff7a5c",
  personal: "#8fe04a",
};

export const BRANCH_LABELS: Record<Skill["branch"], string> = {
  core: "Foundations",
  macro: "Macro",
  companies: "Companies",
  "hard-assets": "Hard assets",
  personal: "Your money",
};

/**
 * Mastery a returning player starts with, so the map is never blank.
 *
 * Diversification is already banked (index funds are unlocked in the lab) and
 * valuation sits just short of the line — so one good magnitude round visibly
 * unlocks single stocks. The whole loop is legible in a single session.
 */
export const STARTING_MASTERY: Partial<Record<SkillId, number>> = {
  markets: 100,
  rates: 80,
  earnings: 65,
  valuation: 88,
  diversify: 100,
  oil: 40,
  inflation: 30,
  moats: 20,
};

/** Children of a node, for the "leads to" list. */
export function childrenOf(id: SkillId): Skill[] {
  return SKILLS.filter((skill) => skill.requires.includes(id));
}

/** A node is playable once every prerequisite has any mastery at all. */
export function isUnlocked(skill: Skill, mastery: Partial<Record<SkillId, number>>): boolean {
  return skill.requires.every((id) => (mastery[id] ?? 0) > 0);
}
