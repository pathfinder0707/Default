"use client";

import { useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { Check, Copy, Flame, RotateCcw, X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Confetti } from "@/components/game/Confetti";
import { AnimatedNumber } from "@/components/ui/AnimatedNumber";
import { PERFECT_RUN_XP, RUN } from "@/lib/game/rounds";
import { levelFor, levelTitle } from "@/lib/game/league";
import { formatXp } from "@/lib/game/format";

export interface RoundScore {
  roundId: string;
  correct: boolean;
  xp: number;
}

export function RunResult({
  scores,
  earned,
  streak,
  xpBefore,
  onReplay,
}: {
  scores: RoundScore[];
  earned: number;
  streak: number;
  xpBefore: number;
  onReplay: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const reduceMotion = useReducedMotion();

  const right = scores.filter((s) => s.correct).length;
  const before = levelFor(xpBefore);
  const after = levelFor(xpBefore + earned);
  const levelledUp = after.level > before.level;

  const grid = scores.map((s) => (s.correct ? "🟩" : "🟥")).join("");

  async function share() {
    const text = [
      "Edenomics · daily run",
      `${grid}  ${right}/${scores.length} · ${formatXp(earned)} XP`,
      `🔥 ${streak} day streak`,
    ].join("\n");

    try {
      if (navigator.share) {
        await navigator.share({ text });
        return;
      }
      await navigator.clipboard.writeText(text);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1900);
    } catch {
      // Share sheet dismissed, or the clipboard was blocked.
    }
  }

  return (
    <div className="relative overflow-hidden">
      <Confetti fire={right >= 3} />

      <div className="relative px-1 py-2 text-center">
        <motion.p
          initial={reduceMotion ? false : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="label"
        >
          Run complete
        </motion.p>

        <motion.div
          initial={reduceMotion ? false : { scale: 0.7, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 300, damping: 18, delay: 0.08 }}
          className="mt-3"
        >
          <span className="text-xp tabular block text-6xl font-bold sm:text-7xl">
            +<AnimatedNumber value={earned} format={formatXp} />
          </span>
          <span className="label mt-1 block">
            XP · best possible was {formatXp(PERFECT_RUN_XP)}
          </span>
        </motion.div>

        {/* Per-round result strip */}
        <div className="mt-7 flex justify-center gap-2">
          {scores.map((score, index) => {
            const round = RUN.find((r) => r.id === score.roundId);
            return (
              <motion.div
                key={score.roundId}
                initial={reduceMotion ? false : { scale: 0, rotate: -20 }}
                animate={{ scale: 1, rotate: 0 }}
                transition={{
                  type: "spring",
                  stiffness: 420,
                  damping: 18,
                  delay: 0.2 + index * 0.07,
                }}
                title={round?.kindLabel}
                className={`flex h-11 w-11 items-center justify-center rounded-xl ${
                  score.correct ? "bg-correct/20 text-correct" : "bg-wrong/20 text-wrong"
                }`}
              >
                {score.correct ? (
                  <Check size={20} strokeWidth={3} aria-hidden />
                ) : (
                  <X size={20} strokeWidth={3} aria-hidden />
                )}
                <span className="sr-only">
                  {round?.kindLabel}: {score.correct ? "correct" : "missed"}
                </span>
              </motion.div>
            );
          })}
        </div>

        <p className="text-muted mt-4 text-[0.9375rem]">
          {right} of {scores.length} rounds ·{" "}
          <span className="text-streak inline-flex items-center gap-1 font-semibold">
            <Flame size={14} aria-hidden />
            {streak} day streak
          </span>
        </p>

        {/* Level bar */}
        <div className="mx-auto mt-7 max-w-sm">
          <div className="mb-2 flex items-baseline justify-between text-[0.8125rem]">
            <span className="font-semibold">
              Level {after.level}
              <span className="text-faint ml-1.5 font-normal">{levelTitle(after.level)}</span>
            </span>
            <span className="tabular text-faint">
              {formatXp(after.into)} / {formatXp(after.span)}
            </span>
          </div>
          <div
            className="h-2.5 w-full overflow-hidden rounded-full bg-white/[0.08]"
            role="progressbar"
            aria-valuenow={after.into}
            aria-valuemin={0}
            aria-valuemax={after.span}
            aria-label={`Progress to level ${after.level + 1}`}
          >
            <motion.div
              className="bg-xp h-full rounded-full"
              initial={{ width: `${(before.into / before.span) * 100}%` }}
              animate={{ width: `${(after.into / after.span) * 100}%` }}
              transition={reduceMotion ? { duration: 0 } : { duration: 1.1, delay: 0.4 }}
            />
          </div>

          {levelledUp && (
            <motion.p
              initial={reduceMotion ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.3 }}
              className="text-xp mt-2 text-[0.8125rem] font-semibold"
            >
              Level up — you&rsquo;re a {levelTitle(after.level)} now.
            </motion.p>
          )}
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Button onClick={share} size="lg">
            {copied ? <Check size={17} aria-hidden /> : <Copy size={17} aria-hidden />}
            {copied ? "Copied" : "Share your run"}
          </Button>
          <Button onClick={onReplay} variant="secondary" size="lg">
            <RotateCcw size={16} aria-hidden />
            Play again
          </Button>
        </div>

        <p className="text-faint mt-6 text-[0.8125rem]">
          Five new rounds land tomorrow morning. Your streak holds if you play before midnight.
        </p>
      </div>
    </div>
  );
}
