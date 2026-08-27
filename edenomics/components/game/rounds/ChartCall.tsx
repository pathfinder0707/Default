"use client";

import { useState } from "react";
import { motion } from "motion/react";
import type { ChartCallRound, RoundOutcome } from "@/lib/game/types";
import { ChoiceGrid } from "@/components/game/ChoiceGrid";
import { RunChart } from "@/components/game/RunChart";
import { haptics } from "@/lib/haptics";

export function ChartCall({
  round,
  onResolve,
}: {
  round: ChartCallRound;
  onResolve: (outcome: RoundOutcome) => void;
}) {
  const [chosenId, setChosenId] = useState<string | null>(null);

  function choose(id: string) {
    if (chosenId) return;
    setChosenId(id);
    const correct = id === round.correctId;
    if (correct) haptics.correct();
    else haptics.wrong();
    onResolve({ correct, xpScale: correct ? 1 : 0.25 });
  }

  return (
    <div>
      <p className="text-muted mb-4 text-[0.9375rem] leading-relaxed">{round.setup}</p>

      <div className="mb-2 flex items-baseline justify-between">
        <span className="font-display text-lg font-bold">{round.asset}</span>
        <span className="tabular text-faint text-[0.8125rem]">{round.ticker}</span>
      </div>

      <RunChart
        values={round.series}
        revealAt={round.revealAt}
        revealed={chosenId !== null}
        label={`${round.asset} price after its earnings release`}
      />

      {chosenId && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.9 }}
          className="text-faint mt-3 text-center text-[0.8125rem]"
        >
          {round.outcome}
        </motion.p>
      )}

      <p className="mt-6 font-semibold">What happened after the dashed line?</p>

      <ChoiceGrid
        options={round.options}
        chosenId={chosenId}
        correctId={round.correctId}
        onChoose={choose}
      />
    </div>
  );
}
