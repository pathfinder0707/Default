"use client";

import { motion, useReducedMotion } from "motion/react";
import { ArrowRight, Sparkles } from "lucide-react";
import type { Claim } from "@/lib/game/claims";
import { CONCEPT_BY_ID, SUITS } from "@/lib/game/concepts";
import { COIN_FLIP_SCORE } from "@/lib/game/scoring";

/**
 * What the card was actually worth.
 *
 * The stamp lands first, then the number, then the reason. The order matters:
 * you feel the result before you are told why, which is the moment the lesson
 * has your attention.
 */
export function Verdict({
  claim,
  side,
  confidence,
  points,
  correct,
  isLast,
  onNext,
}: {
  claim: Claim;
  side: "true" | "false";
  confidence: number;
  points: number;
  correct: boolean;
  isLast: boolean;
  onNext: () => void;
}) {
  const reduceMotion = useReducedMotion();
  const concept = CONCEPT_BY_ID.get(claim.concept)!;
  const suit = SUITS[concept.suit];
  const percent = Math.round(confidence * 100);
  const hedged = percent <= 58;

  return (
    <motion.div
      initial={reduceMotion ? false : { opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.34, ease: [0.22, 1, 0.36, 1] }}
      className="flex w-[min(92vw,460px)] flex-col items-center"
    >
      {/* The stamp */}
      <motion.div
        initial={reduceMotion ? false : { scale: 2.4, opacity: 0, rotate: -22 }}
        animate={{ scale: 1, opacity: 1, rotate: -7 }}
        transition={{ type: "spring", stiffness: 260, damping: 15 }}
        className={`rounded-2xl border-[3px] px-6 py-2.5 ${
          claim.isTrue ? "border-jade text-jade" : "border-crimson text-crimson"
        }`}
      >
        <span className="display text-[2rem] leading-none tracking-[0.06em]">
          {claim.isTrue ? "TRUE" : "FALSE"}
        </span>
      </motion.div>

      {/* What it cost or paid */}
      <motion.p
        initial={reduceMotion ? false : { opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.18, type: "spring", stiffness: 300, damping: 20 }}
        className={`display mt-5 text-[3.4rem] leading-none ${
          points >= COIN_FLIP_SCORE ? "text-brass" : "text-crimson"
        }`}
      >
        {points > 0 ? "+" : ""}
        {points}
      </motion.p>

      <motion.p
        initial={reduceMotion ? false : { opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="text-muted mt-2 text-center text-[0.875rem]"
      >
        You said{" "}
        <span className="text-cream tabular font-semibold">
          {percent}% {side === "true" ? "true" : "false"}
        </span>
        {correct ? (
          hedged ? (
            <> — right, but you barely committed.</>
          ) : (
            <> — and you were right.</>
          )
        ) : percent >= 85 ? (
          <> — and you were sure. That is what it costs.</>
        ) : (
          <> — wrong, but you left yourself room.</>
        )}
      </motion.p>

      {/* Why */}
      <motion.div
        initial={reduceMotion ? false : { opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.38, duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
        className="rail mt-7 w-full rounded-2xl p-5"
      >
        <div className="mb-2.5 flex items-center gap-2">
          <span
            className="text-[0.95rem] leading-none"
            style={{ color: suit.tint }}
            aria-hidden
          >
            {suit.glyph}
          </span>
          <span className="label">{concept.name}</span>
        </div>
        <p className="text-body text-[0.9375rem] leading-relaxed">{claim.explanation}</p>

        <div className="border-line mt-4 flex items-center justify-between border-t pt-3.5">
          <span className="text-faint font-mono text-[0.6875rem]">
            {claim.solvedPct}% of players called this right
          </span>
          {correct && (
            <span className="text-brass flex items-center gap-1.5 font-mono text-[0.6875rem]">
              <Sparkles size={12} aria-hidden />
              {concept.rank}
              {suit.glyph} won
            </span>
          )}
        </div>
      </motion.div>

      <motion.button
        type="button"
        onClick={onNext}
        initial={reduceMotion ? false : { opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="bg-brass text-felt mt-6 inline-flex h-12 w-full items-center justify-center gap-2 rounded-2xl font-semibold shadow-[0_3px_0_var(--color-brass-deep)] transition-transform hover:brightness-110 active:translate-y-[2px] active:shadow-[0_1px_0_var(--color-brass-deep)]"
      >
        {isLast ? "See your calibration" : "Next card"}
        <ArrowRight size={17} aria-hidden />
      </motion.button>
    </motion.div>
  );
}
