"use client";

import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ArrowRight, Play, Timer } from "lucide-react";
import type { Round, RoundOutcome } from "@/lib/game/types";
import { RUN, comboMultiplier } from "@/lib/game/rounds";
import { usePlayer } from "@/lib/state/player";
import { Button } from "@/components/ui/Button";
import { ComboMeter } from "@/components/game/ComboMeter";
import { Teach } from "@/components/game/Teach";
import { RunResult, type RoundScore } from "@/components/game/RunResult";
import { ChartCall } from "@/components/game/rounds/ChartCall";
import { Magnitude } from "@/components/game/rounds/Magnitude";
import { CauseEffect } from "@/components/game/rounds/CauseEffect";
import { Identify } from "@/components/game/rounds/Identify";
import { BullBear } from "@/components/game/rounds/BullBear";
import { haptics } from "@/lib/haptics";

type Phase = "intro" | "playing" | "done";

function RoundBody({
  round,
  onResolve,
}: {
  round: Round;
  onResolve: (outcome: RoundOutcome) => void;
}) {
  switch (round.kind) {
    case "chart-call":
      return <ChartCall round={round} onResolve={onResolve} />;
    case "magnitude":
      return <Magnitude round={round} onResolve={onResolve} />;
    case "cause-effect":
      return <CauseEffect round={round} onResolve={onResolve} />;
    case "identify":
      return <Identify round={round} onResolve={onResolve} />;
    case "bull-bear":
      return <BullBear round={round} onResolve={onResolve} />;
  }
}

/**
 * One day's run: five rounds, a combo that carries between them, and a single
 * write to the player store at the end.
 *
 * The whole thing lives inline on the page rather than behind a route — the
 * point of the product is that you can start playing before you have decided
 * whether you want to.
 */
export function DailyRun() {
  const player = usePlayer();

  const [phase, setPhase] = useState<Phase>("intro");
  const [index, setIndex] = useState(0);
  const [combo, setCombo] = useState(0);
  const [bestCombo, setBestCombo] = useState(0);
  const [scores, setScores] = useState<RoundScore[]>([]);
  const [resolved, setResolved] = useState<{ correct: boolean; xp: number } | null>(null);
  const [xpAtStart, setXpAtStart] = useState(player.xp);
  const reduceMotion = useReducedMotion();

  const round = RUN[index];
  const earned = scores.reduce((total, score) => total + score.xp, 0);
  const isLast = index === RUN.length - 1;

  const start = useCallback(() => {
    setXpAtStart(player.xp);
    setPhase("playing");
    setIndex(0);
    setCombo(0);
    setBestCombo(0);
    setScores([]);
    setResolved(null);
    haptics.tap();
  }, [player.xp]);

  function resolve(outcome: RoundOutcome) {
    // The multiplier is the one you had walking in, so a combo pays off on the
    // round after you earn it rather than the one that earned it.
    const xp = Math.round(round.xp * outcome.xpScale * comboMultiplier(combo));
    setResolved({ correct: outcome.correct, xp });
    setScores((current) => [...current, { roundId: round.id, correct: outcome.correct, xp }]);

    const nextCombo = outcome.correct ? combo + 1 : 0;
    setCombo(nextCombo);
    setBestCombo((best) => Math.max(best, nextCombo));
  }

  const advance = useCallback(() => {
    if (!resolved) return;

    if (isLast) {
      const finalScores = scores;
      const skillsHit = finalScores
        .filter((score) => score.correct)
        .map((score) => RUN.find((r) => r.id === score.roundId)!.skill);

      player.completeRun({
        xpEarned: finalScores.reduce((total, s) => total + s.xp, 0),
        bestCombo,
        skillsHit,
      });
      setPhase("done");
      haptics.levelUp();
      return;
    }

    setIndex((current) => current + 1);
    setResolved(null);
    haptics.tap();
  }, [resolved, isLast, scores, bestCombo, player]);

  // Enter moves the run on, so a whole session can be played without a mouse.
  useEffect(() => {
    if (phase !== "playing" || !resolved) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Enter") {
        event.preventDefault();
        advance();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [phase, resolved, advance]);

  return (
    <div className="piece relative overflow-hidden rounded-3xl p-5 sm:p-7">
      <AnimatePresence mode="wait" initial={false}>
        {phase === "intro" && (
          <motion.div
            key="intro"
            initial={reduceMotion ? false : { opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={reduceMotion ? undefined : { opacity: 0, y: -12 }}
            transition={{ duration: 0.28 }}
          >
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="label">Today&rsquo;s run</p>
                <h2 className="display mt-1.5 text-3xl sm:text-4xl">Five rounds.</h2>
              </div>
              <span className="text-faint flex shrink-0 items-center gap-1.5 text-[0.8125rem]">
                <Timer size={15} aria-hidden />3 min
              </span>
            </div>

            <ul className="mt-6 grid gap-2">
              {RUN.map((item, i) => (
                <li
                  key={item.id}
                  className="border-line flex items-center gap-3 rounded-xl border bg-black/20 px-3.5 py-2.5"
                >
                  <span className="bg-lifted text-muted tabular flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-[0.75rem] font-bold">
                    {i + 1}
                  </span>
                  <span className="text-[0.9375rem] font-medium">{item.kindLabel}</span>
                  <span className="tabular text-xp ml-auto text-[0.8125rem]">
                    {item.xp} XP
                  </span>
                </li>
              ))}
            </ul>

            <Button onClick={start} size="lg" className="mt-6 w-full">
              <Play size={18} fill="currentColor" aria-hidden />
              {player.playedToday ? "Play again for practice" : "Start today's run"}
            </Button>

            <p className="text-faint mt-3 text-center text-[0.8125rem]">
              {player.playedToday
                ? "Streak already banked today — this one is just for the XP."
                : "No wrong answer costs you anything but the combo."}
            </p>
          </motion.div>
        )}

        {phase === "playing" && (
          <motion.div
            key="playing"
            initial={reduceMotion ? false : { opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.25 }}
          >
            <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="bg-brand/15 text-brand rounded-full px-3 py-1 text-[0.75rem] font-bold tracking-wide uppercase">
                  {round.kindLabel}
                </span>
                <span className="tabular text-faint text-[0.8125rem]">
                  {index + 1}/{RUN.length}
                </span>
              </div>
              <ComboMeter combo={combo} />
            </header>

            <div className="mb-6 flex gap-1.5" aria-hidden>
              {RUN.map((item, i) => (
                <span
                  key={item.id}
                  className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
                    i < index ? "bg-brand" : i === index ? "bg-brand/60" : "bg-white/10"
                  }`}
                />
              ))}
            </div>

            <AnimatePresence mode="wait" initial={false}>
              <motion.div
                key={round.id}
                initial={reduceMotion ? false : { opacity: 0, x: 24 }}
                animate={{ opacity: 1, x: 0 }}
                exit={reduceMotion ? undefined : { opacity: 0, x: -24 }}
                transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
              >
                <RoundBody round={round} onResolve={resolve} />
              </motion.div>
            </AnimatePresence>

            {resolved && (
              <>
                <Teach
                  correct={resolved.correct}
                  text={round.teaches}
                  solvedPct={round.solvedPct}
                  xpAwarded={resolved.xp}
                />
                <Button onClick={advance} size="lg" className="mt-5 w-full">
                  {isLast ? "See your run" : "Next round"}
                  <ArrowRight size={18} aria-hidden />
                </Button>
              </>
            )}
          </motion.div>
        )}

        {phase === "done" && (
          <motion.div
            key="done"
            initial={reduceMotion ? false : { opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
          >
            <RunResult
              scores={scores}
              earned={earned}
              streak={player.streak}
              xpBefore={xpAtStart}
              onReplay={start}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
