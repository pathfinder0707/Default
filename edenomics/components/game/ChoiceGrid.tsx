"use client";

import { useEffect } from "react";
import { motion, useReducedMotion } from "motion/react";
import { Check, X } from "lucide-react";
import type { ChoiceOption } from "@/lib/game/types";

/**
 * The answer list shared by every multiple-choice round.
 *
 * After answering, each option explains itself — including the ones nobody
 * picked. Knowing why the other two were wrong is most of the lesson.
 */
export function ChoiceGrid({
  options,
  chosenId,
  correctId,
  onChoose,
}: {
  options: ChoiceOption[];
  chosenId: string | null;
  correctId: string;
  onChoose: (id: string) => void;
}) {
  const answered = chosenId !== null;
  const reduceMotion = useReducedMotion();

  // 1–4 answers the question. Faster than aiming, and it makes the whole run
  // playable from the keyboard.
  useEffect(() => {
    if (answered) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      const index = Number(event.key) - 1;
      const option = options[index];
      if (!Number.isNaN(index) && option) {
        event.preventDefault();
        onChoose(option.id);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [answered, options, onChoose]);

  return (
    <ul className="mt-6 grid gap-2.5">
      {options.map((option, index) => {
        const isChosen = chosenId === option.id;
        const isAnswer = option.id === correctId;
        const state = !answered
          ? "idle"
          : isAnswer
            ? "correct"
            : isChosen
              ? "wrong"
              : "dim";

        return (
          <li key={option.id}>
            <button
              type="button"
              onClick={() => onChoose(option.id)}
              disabled={answered}
              className={`flex w-full items-start gap-3.5 rounded-2xl border p-4 text-left transition-colors duration-300 ${
                state === "idle"
                  ? "piece piece-hover"
                  : state === "correct"
                    ? "border-correct/60 bg-correct/[0.1]"
                    : state === "wrong"
                      ? "border-wrong/60 bg-wrong/[0.09]"
                      : "border-line/60 bg-surface/50 opacity-45"
              }`}
            >
              <span
                aria-hidden
                className={`tabular mt-px flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-[0.75rem] font-bold transition-colors ${
                  state === "correct"
                    ? "bg-correct text-void"
                    : state === "wrong"
                      ? "bg-wrong text-void"
                      : "bg-lifted text-muted"
                }`}
              >
                {state === "correct" ? (
                  <Check size={14} strokeWidth={3.5} />
                ) : state === "wrong" ? (
                  <X size={14} strokeWidth={3.5} />
                ) : (
                  index + 1
                )}
              </span>

              <span className="min-w-0 flex-1">
                <span className="block font-semibold">{option.label}</span>
                {answered && (
                  <motion.span
                    initial={reduceMotion ? false : { opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.12 + index * 0.04 }}
                    className="text-faint mt-1 block text-[0.8125rem] leading-relaxed"
                  >
                    {option.note}
                  </motion.span>
                )}
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
