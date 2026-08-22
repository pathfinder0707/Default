"use client";

import { useMemo, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ArrowRight, Check, Lightbulb, RotateCcw, X } from "lucide-react";
import { CHALLENGES } from "@/lib/data/challenges";
import { useProgress } from "@/lib/state/progress";

const INITIAL_CLUES = 2;
const CLUE_COST = 5;
const MIN_XP = 10;
/** A wrong answer still taught you something, so it is worth part credit. */
const WRONG_ANSWER_SHARE = 0.4;

export function ChallengeCard() {
  const { award, solved, earnedToday } = useProgress();
  const reduceMotion = useReducedMotion();

  const [index, setIndex] = useState(0);
  const [answerId, setAnswerId] = useState<string | null>(null);
  const [cluesShown, setCluesShown] = useState(INITIAL_CLUES);
  const [awarded, setAwarded] = useState(0);
  // Captured at answer time — `solved` includes this question once it is scored.
  const [replayed, setReplayed] = useState(false);
  const [finished, setFinished] = useState(false);

  const challenge = CHALLENGES[index];
  const answered = answerId !== null;
  const isCorrect = answerId === challenge.correctId;
  const alreadySolved = solved.includes(challenge.id);

  // Extra clues cost XP, so a confident answer is worth more than a fished one.
  const availableXp = useMemo(() => {
    if (!challenge.clues) return challenge.xp;
    const spent = (cluesShown - INITIAL_CLUES) * CLUE_COST;
    return Math.max(MIN_XP, challenge.xp - spent);
  }, [challenge, cluesShown]);

  function choose(optionId: string) {
    if (answered) return;
    setAnswerId(optionId);
    setReplayed(alreadySolved);
    const correct = optionId === challenge.correctId;
    const value = correct
      ? availableXp
      : Math.round(availableXp * WRONG_ANSWER_SHARE);
    setAwarded(value);
    if (!alreadySolved) award(challenge.id, value);
  }

  function next() {
    if (index >= CHALLENGES.length - 1) {
      setFinished(true);
      return;
    }
    setIndex((i) => i + 1);
    setAnswerId(null);
    setAwarded(0);
    setReplayed(false);
    setCluesShown(INITIAL_CLUES);
  }

  function restart() {
    setIndex(0);
    setAnswerId(null);
    setAwarded(0);
    setReplayed(false);
    setCluesShown(INITIAL_CLUES);
    setFinished(false);
  }

  if (finished) {
    return (
      <div className="border-line bg-elevated flex h-full min-h-[360px] flex-col items-center justify-center rounded-2xl border p-8 text-center sm:min-h-[440px]">
        <motion.div
          initial={reduceMotion ? false : { scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="border-accent/30 bg-accent/10 relative mb-6 flex h-16 w-16 items-center justify-center rounded-full border"
        >
          <Check size={26} className="text-accent" aria-hidden />
          <span className="border-accent/40 absolute inset-0 rounded-full border animate-pulse-ring" />
        </motion.div>
        <h3 className="display text-[1.75rem]">That&rsquo;s today done.</h3>
        <p className="text-muted mt-3 max-w-sm text-[0.9375rem] leading-relaxed">
          You picked up{" "}
          <span className="text-accent tabular">+{earnedToday} XP</span> and three
          concepts that will show up again the next time markets move.
        </p>
        <p className="text-faint mt-6 font-mono text-[0.6875rem] tracking-wide">
          New questions land tomorrow morning
        </p>
        <button
          type="button"
          onClick={restart}
          className="text-muted hover:text-fg mt-6 inline-flex items-center gap-1.5 text-[0.8125rem] transition-colors"
        >
          <RotateCcw size={13} aria-hidden />
          Play through again
        </button>
      </div>
    );
  }

  return (
    <div className="border-line bg-elevated flex h-full min-h-[360px] flex-col rounded-2xl border p-6 sm:min-h-[440px] sm:p-7">
      <div className="mb-6 flex items-center gap-3">
        <span className="text-accent bg-accent/10 rounded-full px-2.5 py-1 font-mono text-[0.625rem] tracking-[0.1em] uppercase">
          {challenge.kindLabel}
        </span>
        <span className="ml-auto flex items-center gap-1.5" aria-label={`Question ${index + 1} of ${CHALLENGES.length}`}>
          {CHALLENGES.map((c, i) => (
            <span
              key={c.id}
              aria-hidden
              className={`h-1.5 rounded-full transition-all duration-300 ${
                i === index ? "bg-accent w-5" : i < index ? "bg-accent/40 w-1.5" : "w-1.5 bg-white/15"
              }`}
            />
          ))}
        </span>
      </div>

      <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={challenge.id}
          initial={reduceMotion ? false : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={reduceMotion ? undefined : { opacity: 0, y: -10 }}
          transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
          className="flex flex-1 flex-col"
        >
          <h3 className="text-[1.25rem] leading-snug font-medium sm:text-[1.4rem]">
            {challenge.prompt}
          </h3>

          {challenge.clues && (
            <ul className="mt-5 space-y-2">
              {challenge.clues.slice(0, cluesShown).map((clue, i) => (
                <motion.li
                  key={clue}
                  initial={reduceMotion || i < INITIAL_CLUES ? false : { opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3 }}
                  className="text-muted flex items-start gap-2.5 text-[0.875rem]"
                >
                  <span className="text-faint mt-1.5 h-1 w-1 shrink-0 rounded-full bg-current" aria-hidden />
                  {clue}
                </motion.li>
              ))}
            </ul>
          )}

          {challenge.clues && cluesShown < challenge.clues.length && !answered && (
            <button
              type="button"
              onClick={() => setCluesShown((c) => c + 1)}
              className="text-muted hover:text-fg mt-3 inline-flex w-fit items-center gap-1.5 text-[0.8125rem] transition-colors"
            >
              <Lightbulb size={13} aria-hidden />
              Another clue
              <span className="text-faint tabular">−{CLUE_COST} XP</span>
            </button>
          )}

          <div className="mt-6 space-y-2.5">
            {challenge.options.map((option) => {
              const isChosen = answerId === option.id;
              const isAnswer = option.id === challenge.correctId;
              const state = !answered
                ? "idle"
                : isAnswer
                  ? "correct"
                  : isChosen
                    ? "wrong"
                    : "dim";

              return (
                <motion.button
                  key={option.id}
                  type="button"
                  onClick={() => choose(option.id)}
                  disabled={answered}
                  whileHover={answered || reduceMotion ? undefined : { x: 3 }}
                  transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
                  className={`flex w-full items-start gap-3 rounded-xl border px-4 py-3.5 text-left transition-colors duration-300 ${
                    state === "idle"
                      ? "border-line hover:border-line-strong bg-raised/60 hover:bg-raised"
                      : state === "correct"
                        ? "border-up/50 bg-up/[0.08]"
                        : state === "wrong"
                          ? "border-down/50 bg-down/[0.07]"
                          : "border-line/60 opacity-45"
                  }`}
                >
                  <span
                    className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full border transition-colors ${
                      state === "correct"
                        ? "border-up bg-up text-ink"
                        : state === "wrong"
                          ? "border-down bg-down text-ink"
                          : "border-line-strong"
                    }`}
                    aria-hidden
                  >
                    {state === "correct" && <Check size={11} strokeWidth={3} />}
                    {state === "wrong" && <X size={11} strokeWidth={3} />}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-[0.9375rem]">{option.label}</span>
                    {answered && (
                      <motion.span
                        initial={reduceMotion ? false : { opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.15 }}
                        className="text-faint mt-1 block text-[0.8125rem] leading-relaxed"
                      >
                        {option.note}
                      </motion.span>
                    )}
                  </span>
                </motion.button>
              );
            })}
          </div>

          <AnimatePresence initial={false}>
            {answered && (
              <motion.div
                initial={reduceMotion ? undefined : { height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={reduceMotion ? undefined : { height: 0, opacity: 0 }}
                transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                className="overflow-hidden"
              >
                <div className="border-line mt-6 border-t pt-5">
                  <div className="mb-3 flex flex-wrap items-center gap-3">
                    <span className={`text-[0.9375rem] ${isCorrect ? "text-up" : "text-fg"}`}>
                      {isCorrect ? "Correct." : "Not quite — here's the idea."}
                    </span>
                    <motion.span
                      initial={reduceMotion ? false : { opacity: 0, y: 10, scale: 0.9 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      transition={{ duration: 0.4, delay: 0.12, ease: [0.22, 1, 0.36, 1] }}
                      className="text-accent bg-accent/10 tabular rounded-full px-2.5 py-1 text-[0.75rem]"
                    >
                      +{awarded} XP
                    </motion.span>
                    {replayed && (
                      <span className="text-faint text-[0.6875rem]">
                        already banked today
                      </span>
                    )}
                  </div>

                  <p className="text-muted text-[0.875rem] leading-relaxed">
                    {challenge.explanation}
                  </p>

                  <div className="mt-5 flex items-center justify-between gap-4">
                    <p className="text-faint text-[0.75rem]">
                      {challenge.solvedPct}% of players got this today
                    </p>
                    <button
                      type="button"
                      onClick={next}
                      className="text-accent hover:text-fg inline-flex items-center gap-1.5 text-[0.875rem] transition-colors"
                    >
                      {index >= CHALLENGES.length - 1 ? "Finish" : "Next question"}
                      <ArrowRight size={14} aria-hidden />
                    </button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
