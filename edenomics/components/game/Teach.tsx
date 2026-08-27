"use client";

import { motion, useReducedMotion } from "motion/react";
import { GraduationCap } from "lucide-react";

/**
 * The payoff panel. It appears whether the answer was right or wrong, because
 * the lesson is the product — the score is just what makes you come back for it.
 */
export function Teach({
  correct,
  text,
  solvedPct,
  xpAwarded,
}: {
  correct: boolean;
  text: string;
  solvedPct: number;
  xpAwarded: number;
}) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={reduceMotion ? false : { opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.42, ease: [0.22, 1, 0.36, 1] }}
      className="border-line mt-6 rounded-2xl border bg-black/25 p-5"
    >
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <span
          className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-[0.8125rem] font-semibold ${
            correct ? "bg-correct/15 text-correct" : "bg-wrong/15 text-wrong"
          }`}
        >
          {correct ? "Correct" : "Not this time"}
        </span>
        <motion.span
          initial={reduceMotion ? false : { opacity: 0, scale: 0.7, y: 8 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.1, ease: [0.34, 1.56, 0.64, 1] }}
          className="bg-xp/15 text-xp tabular rounded-full px-3 py-1 text-[0.8125rem] font-semibold"
        >
          +{xpAwarded} XP
        </motion.span>
        <span className="text-faint ml-auto text-[0.75rem]">
          {solvedPct}% got this today
        </span>
      </div>

      <p className="text-muted flex gap-3 text-[0.9375rem] leading-relaxed">
        <GraduationCap size={18} className="text-brand mt-0.5 shrink-0" aria-hidden />
        <span>{text}</span>
      </p>
    </motion.div>
  );
}
