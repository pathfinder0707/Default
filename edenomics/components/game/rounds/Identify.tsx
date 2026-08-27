"use client";

import { useState } from "react";
import { motion } from "motion/react";
import { Lightbulb } from "lucide-react";
import type { IdentifyRound, RoundOutcome } from "@/lib/game/types";
import { ChoiceGrid } from "@/components/game/ChoiceGrid";
import { haptics } from "@/lib/haptics";

const FREE_CLUES = 2;
/** Each extra clue costs this share of the round's XP. */
const CLUE_COST = 0.18;

export function Identify({
  round,
  onResolve,
}: {
  round: IdentifyRound;
  onResolve: (outcome: RoundOutcome) => void;
}) {
  const [chosenId, setChosenId] = useState<string | null>(null);
  const [cluesShown, setCluesShown] = useState(FREE_CLUES);

  const penalty = (cluesShown - FREE_CLUES) * CLUE_COST;
  const remaining = round.clues.length - cluesShown;

  function choose(id: string) {
    if (chosenId) return;
    setChosenId(id);
    const correct = id === round.correctId;
    if (correct) haptics.correct();
    else haptics.wrong();
    onResolve({
      correct,
      xpScale: correct ? Math.max(0.3, 1 - penalty) : 0.25,
    });
  }

  return (
    <div>
      <ul className="grid gap-2.5">
        {round.clues.slice(0, cluesShown).map((clue, index) => (
          <motion.li
            key={clue}
            initial={index < FREE_CLUES ? false : { opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
            className="piece flex items-start gap-3 rounded-2xl p-3.5"
          >
            <span className="bg-lifted text-muted tabular flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-[0.75rem] font-bold">
              {index + 1}
            </span>
            <span className="text-[0.9375rem] leading-snug">{clue}</span>
          </motion.li>
        ))}
      </ul>

      {remaining > 0 && !chosenId && (
        <button
          type="button"
          onClick={() => {
            setCluesShown((c) => c + 1);
            haptics.tap();
          }}
          className="text-muted hover:text-fg mt-3 inline-flex items-center gap-2 text-[0.8125rem] transition-colors"
        >
          <Lightbulb size={15} className="text-xp" aria-hidden />
          Reveal clue {cluesShown + 1}
          <span className="tabular text-faint">−{Math.round(CLUE_COST * 100)}% XP</span>
        </button>
      )}

      {penalty > 0 && (
        <p className="text-faint tabular mt-3 text-[0.75rem]">
          This round is now worth {Math.round(Math.max(0.3, 1 - penalty) * 100)}% of its XP.
        </p>
      )}

      <p className="mt-6 font-semibold">Which company is it?</p>

      <ChoiceGrid
        options={round.options}
        chosenId={chosenId}
        correctId={round.correctId}
        onChoose={choose}
      />
    </div>
  );
}
