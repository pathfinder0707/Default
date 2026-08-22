import type { Challenge } from "@/lib/types";

/**
 * Today's three-question run. The rules: every question teaches one real
 * concept, the explanation appears whether or not the answer was right, and
 * nothing rewards guessing quickly. This is a daily habit, not a casino.
 */
export const CHALLENGES: Challenge[] = [
  {
    id: "rate-cut",
    kind: "prediction",
    kindLabel: "Market prediction",
    prompt: "The RBI cuts interest rates. What usually happens to bank stocks first?",
    options: [
      {
        id: "rise",
        label: "Bank stocks rise",
        note: "Cheaper funding and more borrowing — the usual first reaction.",
      },
      {
        id: "fall",
        label: "Bank stocks fall",
        note: "Can happen later if lending margins compress, but rarely on day one.",
      },
      {
        id: "nothing",
        label: "Nothing changes",
        note: "Rate expectations move bank valuations more than almost anything else.",
      },
    ],
    correctId: "rise",
    explanation:
      "Banks make money on the gap between what they pay for deposits and what they earn on loans. A rate cut lowers their funding cost and tends to bring more borrowers in, so the first reaction is usually positive. The catch is that loan rates fall too — if they fall faster than deposit rates, that same cut squeezes margins a few quarters later.",
    xp: 20,
    solvedPct: 68,
  },
  {
    id: "guess-netflix",
    kind: "company",
    kindLabel: "Guess the company",
    prompt: "Four clues. Which company is this?",
    clues: [
      "Founded in 1997, in California",
      "Started by posting DVDs through the mail",
      "Nearly sold itself to Blockbuster for $50m in 2000",
      "Now spends roughly $17bn a year on content",
    ],
    options: [
      { id: "netflix", label: "Netflix", note: "The DVD-by-mail origin is the giveaway." },
      { id: "spotify", label: "Spotify", note: "Founded 2006 in Stockholm, audio only." },
      { id: "disney", label: "Disney", note: "Founded 1923 — streaming came much later." },
      { id: "amazon", label: "Amazon", note: "1994, and it started with books, not DVDs." },
    ],
    correctId: "netflix",
    explanation:
      "Netflix is the standard example of a company that replaced its own business before someone else did — mail-order DVDs to streaming, then streaming to original production. Blockbuster turned down the chance to buy it and filed for bankruptcy ten years later. It is worth remembering when a company's current business looks unbeatable.",
    xp: 25,
    solvedPct: 81,
  },
  {
    id: "oil-shock",
    kind: "bull-bear",
    kindLabel: "Bull or bear",
    prompt: "Oil prices suddenly jump 15%. Which sector most likely benefits?",
    options: [
      {
        id: "energy",
        label: "Oil producers",
        note: "They sell the barrel — a higher price lands straight in revenue.",
      },
      {
        id: "airlines",
        label: "Airlines",
        note: "Fuel is one of their largest costs, so this hurts.",
      },
      {
        id: "paints",
        label: "Paint makers",
        note: "Crude derivatives are a key raw material — margins get squeezed.",
      },
    ],
    correctId: "energy",
    explanation:
      "A price shock moves money rather than destroying it: producers gain roughly what heavy users lose. Airlines, paint and chemical makers and logistics firms all buy crude or its derivatives, so their costs rise immediately while their prices usually adjust slowly. That lag is where the pain shows up.",
    xp: 20,
    solvedPct: 74,
  },
];

export const TOTAL_XP_AVAILABLE = CHALLENGES.reduce((sum, c) => sum + c.xp, 0);
