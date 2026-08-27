"use client";

import { useMemo, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import type { MagnitudeRound, RoundOutcome } from "@/lib/game/types";
import { Button } from "@/components/ui/Button";
import { formatCompact } from "@/lib/game/format";
import { haptics } from "@/lib/haptics";

const STEPS = 1000;

/**
 * Estimate a number on a logarithmic slider.
 *
 * Log rather than linear on purpose: the interesting question is whether you
 * are in the right *order of magnitude*, and a linear track would spend 90% of
 * its width on values nobody would guess.
 */
export function Magnitude({
  round,
  onResolve,
}: {
  round: MagnitudeRound;
  onResolve: (outcome: RoundOutcome) => void;
}) {
  const logMin = Math.log(round.min);
  const logMax = Math.log(round.max);

  const toValue = (t: number) => Math.exp(logMin + (logMax - logMin) * (t / STEPS));
  const toPosition = (value: number) =>
    ((Math.log(value) - logMin) / (logMax - logMin)) * 100;

  const [position, setPosition] = useState(Math.round(STEPS * 0.45));
  const [submitted, setSubmitted] = useState(false);
  const reduceMotion = useReducedMotion();

  const guess = toValue(position);

  const ticks = useMemo(() => {
    return [0, 0.25, 0.5, 0.75, 1].map((t) => ({
      at: t * 100,
      label: formatCompact(toValue(t * STEPS), round.format),
    }));
    // toValue is derived from the round's own bounds, which never change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [round.min, round.max, round.format]);

  const ratio = guess / round.answer;
  const logError = Math.abs(Math.log(ratio));
  const correct = logError <= Math.log(1 + round.tolerance);

  function submit() {
    setSubmitted(true);
    if (correct) haptics.correct();
    else haptics.wrong();
    // Partial credit falls off with the size of the error, not linearly with
    // the number — being 3× out should not score the same as being 300× out.
    const scale = correct ? 1 : Math.max(0.2, 1 - logError / Math.log(60));
    onResolve({ correct, xpScale: scale });
  }

  const missLabel = ratio >= 1 ? "too high" : "too low";
  const missFactor = ratio >= 1 ? ratio : 1 / ratio;

  return (
    <div>
      <p className="font-display text-2xl leading-snug font-bold sm:text-3xl">
        {round.question}
      </p>
      <p className="text-faint mt-2 text-[0.875rem]">{round.anchor}</p>

      <div className="mt-8 text-center">
        <motion.span
          key={submitted ? "final" : "live"}
          className={`tabular block text-5xl font-bold sm:text-6xl ${
            submitted ? (correct ? "text-correct" : "text-wrong") : "text-brand"
          }`}
        >
          {formatCompact(guess, round.format)}
        </motion.span>
        <span className="label mt-2 block">your estimate · {round.unit}</span>
      </div>

      <div className="mt-6">
        <label className="sr-only" htmlFor={`magnitude-${round.id}`}>
          {round.question}
        </label>
        <input
          id={`magnitude-${round.id}`}
          type="range"
          min={0}
          max={STEPS}
          value={position}
          disabled={submitted}
          onChange={(e) => setPosition(Number(e.target.value))}
          className="slider"
          aria-valuetext={formatCompact(guess, round.format)}
        />

        <div className="relative mt-1 h-9">
          {ticks.map((tick) => (
            <span
              key={tick.at}
              className="tabular text-faint absolute -translate-x-1/2 text-[0.6875rem]"
              style={{ left: `${tick.at}%` }}
            >
              {tick.label}
            </span>
          ))}

          {submitted && (
            <motion.span
              initial={reduceMotion ? false : { opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: [0.34, 1.56, 0.64, 1] }}
              className="absolute top-4 -translate-x-1/2 whitespace-nowrap"
              style={{ left: `${Math.min(97, Math.max(3, toPosition(round.answer)))}%` }}
            >
              <span className="bg-correct text-void tabular rounded-lg px-2 py-0.5 text-[0.75rem] font-bold">
                {formatCompact(round.answer, round.format)}
              </span>
            </motion.span>
          )}
        </div>
      </div>

      {!submitted ? (
        <Button onClick={submit} size="lg" className="mt-8 w-full">
          Lock in this estimate
        </Button>
      ) : (
        <p className="text-muted mt-8 text-center text-[0.9375rem]">
          {correct ? (
            <>
              Inside the band — the real figure is{" "}
              <span className="text-fg font-semibold">
                {formatCompact(round.answer, round.format)}
              </span>
              .
            </>
          ) : (
            <>
              You were{" "}
              <span className="text-fg tabular font-semibold">
                {missFactor.toFixed(missFactor >= 10 ? 0 : 1)}×
              </span>{" "}
              {missLabel}. The real figure is{" "}
              <span className="text-fg font-semibold">
                {formatCompact(round.answer, round.format)}
              </span>
              .
            </>
          )}
        </p>
      )}
    </div>
  );
}
