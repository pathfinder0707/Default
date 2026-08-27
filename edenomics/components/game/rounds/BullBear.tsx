"use client";

import { useState } from "react";
import type { BullBearRound, RoundOutcome } from "@/lib/game/types";
import { ChoiceGrid } from "@/components/game/ChoiceGrid";
import { haptics } from "@/lib/haptics";

export function BullBear({
  round,
  onResolve,
}: {
  round: BullBearRound;
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
      <div className="border-streak/30 bg-streak/[0.07] rounded-2xl border p-4">
        <p className="font-display text-xl leading-snug font-bold sm:text-2xl">
          {round.scenario}
        </p>
      </div>

      <p className="mt-6 font-semibold">Which of these gains the most?</p>

      <ChoiceGrid
        options={round.options}
        chosenId={chosenId}
        correctId={round.correctId}
        onChoose={choose}
      />
    </div>
  );
}
