"use client";

import { motion, useReducedMotion } from "motion/react";
import { RotateCcw, Share2, Check, LineChart } from "lucide-react";
import { useState } from "react";
import { CalibrationChart } from "@/components/curve/CalibrationChart";
import { CONCEPT_BY_ID, SUITS } from "@/lib/game/concepts";
import { COIN_FLIP_SCORE, calibration, overconfidence, type Answer } from "@/lib/game/scoring";
import { HAND } from "@/lib/game/claims";

/**
 * The end of a hand. The headline number is the average Brier score, shown
 * against what a coin flip would have earned — because "beat a coin flip" is
 * the only benchmark that means anything for seven calls.
 */
export function HandSummary({
  hand,
  history,
  streak,
  onReplay,
  onSeeCurve,
}: {
  hand: Answer[];
  history: Answer[];
  streak: number;
  onReplay: () => void;
  onSeeCurve: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const reduceMotion = useReducedMotion();

  const average = hand.reduce((sum, a) => sum + a.points, 0) / hand.length;
  const right = hand.filter((a) => a.correct).length;
  const gap = overconfidence(hand);
  const won = hand.filter((a) => a.correct).map((a) => a.claimId);

  const beat = average - COIN_FLIP_SCORE;

  async function share() {
    const strip = hand
      .map((a) => (a.correct ? (a.confidence > 0.8 ? "🟩" : "🟨") : a.confidence > 0.8 ? "🟥" : "🟧"))
      .join("");
    const text = [
      "Edenomics · today's hand",
      strip,
      `${average.toFixed(0)} avg · a coin flip scores 50`,
      gap > 0.05 ? `overconfident by ${Math.round(gap * 100)} points` : "well calibrated",
    ].join("\n");
    try {
      if (navigator.share) return void (await navigator.share({ text }));
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      // Dismissed, or the clipboard was blocked.
    }
  }

  return (
    <div className="flex w-[min(92vw,470px)] flex-col items-center pb-4">
      <p className="label">Hand complete · day {streak}</p>

      <motion.p
        initial={reduceMotion ? false : { scale: 0.6, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 260, damping: 16 }}
        className={`display mt-2 text-[4.6rem] leading-none ${
          beat >= 0 ? "text-brass" : "text-crimson"
        }`}
      >
        {average.toFixed(0)}
      </motion.p>
      <p className="text-muted mt-1 text-center text-[0.875rem]">
        average score ·{" "}
        <span className={beat >= 0 ? "text-jade" : "text-crimson"}>
          {beat >= 0 ? "+" : ""}
          {beat.toFixed(0)} vs a coin flip
        </span>
      </p>

      {/* Per-card strip */}
      <div className="mt-6 flex gap-1.5">
        {hand.map((answer, index) => {
          const confident = answer.confidence > 0.8;
          return (
            <motion.div
              key={answer.claimId}
              initial={reduceMotion ? false : { scale: 0, y: -12 }}
              animate={{ scale: 1, y: 0 }}
              transition={{
                delay: 0.15 + index * 0.06,
                type: "spring",
                stiffness: 420,
                damping: 18,
              }}
              title={`${Math.round(answer.confidence * 100)}% — ${answer.correct ? "right" : "wrong"}`}
              className={`h-9 w-9 rounded-lg ${
                answer.correct
                  ? confident
                    ? "bg-jade"
                    : "bg-jade/45"
                  : confident
                    ? "bg-crimson"
                    : "bg-crimson/45"
              }`}
            >
              <span className="sr-only">
                Card {index + 1}: {Math.round(answer.confidence * 100)}% confident,{" "}
                {answer.correct ? "right" : "wrong"}
              </span>
            </motion.div>
          );
        })}
      </div>
      <p className="text-faint mt-2 font-mono text-[0.625rem] tracking-wide">
        {right}/{hand.length} right · solid means you were sure
      </p>

      {/* The lesson of the hand */}
      <div className="rail mt-7 w-full rounded-2xl p-5">
        <p className="label mb-3">Where your confidence sits</p>
        <CalibrationChart buckets={calibration([...history, ...hand])} />
        <p className="text-body mt-4 text-[0.9375rem] leading-relaxed">
          {gap > 0.08 ? (
            <>
              You are running{" "}
              <span className="text-crimson font-semibold">
                {Math.round(gap * 100)} points overconfident
              </span>
              . That is the normal human setting, and it is the single most expensive habit in
              investing — it is what turns a good idea into too large a position.
            </>
          ) : gap < -0.08 ? (
            <>
              You are{" "}
              <span className="text-jade font-semibold">
                {Math.round(-gap * 100)} points underconfident
              </span>
              . You know more than you are claiming — hedging everything to 55% costs you the
              same way overreaching does.
            </>
          ) : (
            <>
              You are <span className="text-jade font-semibold">well calibrated</span>. When you
              say 80%, it happens about 80% of the time. That is rarer than being clever.
            </>
          )}
        </p>
      </div>

      {/* Cards won */}
      {won.length > 0 && (
        <div className="mt-5 w-full">
          <p className="label mb-2.5">Won for your vault</p>
          <div className="flex flex-wrap gap-2">
            {won.map((claimId) => {
              const claim = HAND.find((c) => c.id === claimId)!;
              const concept = CONCEPT_BY_ID.get(claim.concept)!;
              const suit = SUITS[concept.suit];
              return (
                <span
                  key={claimId}
                  className="card-face flex items-center gap-1.5 rounded-lg px-2.5 py-1.5"
                >
                  <span className="display text-[0.875rem] leading-none">{concept.rank}</span>
                  <span
                    className="text-[0.8125rem] leading-none"
                    style={{ color: suit.tint === "#eae4d6" ? "#151f1b" : suit.tint }}
                  >
                    {suit.glyph}
                  </span>
                </span>
              );
            })}
          </div>
        </div>
      )}

      <div className="mt-7 flex w-full gap-2.5">
        <button
          type="button"
          onClick={onSeeCurve}
          className="rail rail-hover text-cream flex flex-1 items-center justify-center gap-2 rounded-2xl py-3.5 text-[0.875rem] font-semibold"
        >
          <LineChart size={16} aria-hidden />
          Full record
        </button>
        <button
          type="button"
          onClick={share}
          className="rail rail-hover text-cream flex flex-1 items-center justify-center gap-2 rounded-2xl py-3.5 text-[0.875rem] font-semibold"
        >
          {copied ? <Check size={16} aria-hidden /> : <Share2 size={16} aria-hidden />}
          {copied ? "Copied" : "Share"}
        </button>
      </div>

      <button
        type="button"
        onClick={onReplay}
        className="text-faint hover:text-cream mt-4 inline-flex items-center gap-1.5 text-[0.8125rem] transition-colors"
      >
        <RotateCcw size={13} aria-hidden />
        Play the hand again
      </button>

      <p className="text-faint mt-5 text-center text-[0.75rem] leading-relaxed">
        Seven new claims tomorrow. Your record is kept in this browser.
      </p>
    </div>
  );
}
