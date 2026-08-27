"use client";

import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ArrowDown, Check, RotateCcw, X } from "lucide-react";
import type { CauseEffectRound, RoundOutcome } from "@/lib/game/types";
import { Button } from "@/components/ui/Button";
import { haptics } from "@/lib/haptics";

/**
 * Put the chain in order. Ordering beats multiple choice here because the
 * lesson *is* the sequence — knowing that rates hit borrowing before they hit
 * prices is the whole point, and a four-option list would give it away.
 */
export function CauseEffect({
  round,
  onResolve,
}: {
  round: CauseEffectRound;
  onResolve: (outcome: RoundOutcome) => void;
}) {
  const [picked, setPicked] = useState<string[]>([]);
  const [checked, setChecked] = useState(false);
  const reduceMotion = useReducedMotion();

  const remaining = round.steps.filter((step) => !picked.includes(step.id));
  const full = picked.length === round.steps.length;
  const correct = checked && picked.every((id, i) => id === round.order[i]);

  function pick(id: string) {
    if (checked) return;
    setPicked((current) => [...current, id]);
    haptics.tap();
  }

  function undo() {
    if (checked) return;
    setPicked((current) => current.slice(0, -1));
    haptics.tap();
  }

  function check() {
    const isRight = picked.every((id, i) => id === round.order[i]);
    setChecked(true);
    if (isRight) haptics.correct();
    else haptics.wrong();
    onResolve({ correct: isRight, xpScale: isRight ? 1 : 0.25 });
  }

  const label = (id: string) => round.steps.find((s) => s.id === id)?.label ?? "";

  return (
    <div>
      <div className="border-brand/30 bg-brand/[0.07] rounded-2xl border p-4">
        <p className="label mb-1">The trigger</p>
        <p className="font-display text-xl leading-snug font-bold sm:text-2xl">
          {round.trigger}
        </p>
      </div>

      <p className="mt-6 font-semibold">Put what follows in order.</p>
      <p className="text-faint mt-1 text-[0.8125rem]">
        Tap the steps in the sequence they actually happen.
      </p>

      {/* The sequence being built */}
      <ol className="mt-4 grid gap-2.5">
        {round.order.map((_, slot) => {
          const id = picked[slot];
          const slotCorrect = checked && id === round.order[slot];

          return (
            <li key={slot}>
              <motion.div
                layout={!reduceMotion}
                transition={{ type: "spring", stiffness: 420, damping: 34 }}
                className={`flex items-center gap-3.5 rounded-2xl border p-3.5 transition-colors ${
                  !id
                    ? "border-line/70 bg-surface/40 border-dashed"
                    : checked
                      ? slotCorrect
                        ? "border-correct/60 bg-correct/[0.1]"
                        : "border-wrong/60 bg-wrong/[0.09]"
                      : "piece"
                }`}
              >
                <span
                  aria-hidden
                  className={`tabular flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-[0.8125rem] font-bold ${
                    checked
                      ? slotCorrect
                        ? "bg-correct text-void"
                        : "bg-wrong text-void"
                      : "bg-lifted text-muted"
                  }`}
                >
                  {checked ? (
                    slotCorrect ? (
                      <Check size={15} strokeWidth={3.5} />
                    ) : (
                      <X size={15} strokeWidth={3.5} />
                    )
                  ) : (
                    slot + 1
                  )}
                </span>
                <span
                  className={`text-[0.9375rem] leading-snug ${id ? "" : "text-faint italic"}`}
                >
                  {id ? label(id) : "…"}
                </span>
              </motion.div>
            </li>
          );
        })}
      </ol>

      {/* What is left to place */}
      <AnimatePresence initial={false}>
        {remaining.length > 0 && !checked && (
          <motion.div
            initial={reduceMotion ? false : { opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={reduceMotion ? undefined : { opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="text-faint mt-5 mb-2 flex items-center justify-center">
              <ArrowDown size={16} aria-hidden />
            </div>
            <ul className="grid gap-2.5">
              {remaining.map((step) => (
                <motion.li key={step.id} layout={!reduceMotion}>
                  <button
                    type="button"
                    onClick={() => pick(step.id)}
                    className="piece piece-hover w-full rounded-2xl p-3.5 text-left text-[0.9375rem] leading-snug"
                  >
                    {step.label}
                  </button>
                </motion.li>
              ))}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>

      {!checked && (
        <div className="mt-5 flex items-center gap-3">
          <Button onClick={check} disabled={!full} size="md">
            Check the chain
          </Button>
          {picked.length > 0 && (
            <button
              type="button"
              onClick={undo}
              className="text-muted hover:text-fg inline-flex items-center gap-1.5 text-[0.8125rem] transition-colors"
            >
              <RotateCcw size={14} aria-hidden />
              Undo
            </button>
          )}
        </div>
      )}

      {checked && !correct && (
        <p className="text-muted mt-4 text-[0.875rem]">
          The right order is{" "}
          {round.order.map((id, i) => (
            <span key={id}>
              {i > 0 && " → "}
              <span className="text-fg font-semibold">{label(id).toLowerCase()}</span>
            </span>
          ))}
          .
        </p>
      )}
    </div>
  );
}
