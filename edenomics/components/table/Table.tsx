"use client";

import { useCallback, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { PlayCard } from "@/components/table/PlayCard";
import { Verdict } from "@/components/table/Verdict";
import { HandSummary } from "@/components/table/HandSummary";
import { HAND } from "@/lib/game/claims";
import { brierPoints, probabilityOfTrue, type Answer } from "@/lib/game/scoring";
import { usePlayer } from "@/lib/state/player";
import { sfx } from "@/lib/sound";
import { haptics } from "@/lib/haptics";

interface Resolved {
  side: "true" | "false";
  confidence: number;
  points: number;
  correct: boolean;
}

/**
 * The table. Deals seven claims, one at a time, and keeps the hand until it is
 * finished — then writes it to the record in a single go.
 */
export function Table({ onSeeCurve }: { onSeeCurve: () => void }) {
  const player = usePlayer();
  const reduceMotion = useReducedMotion();

  const [index, setIndex] = useState(0);
  const [resolved, setResolved] = useState<Resolved | null>(null);
  const [hand, setHand] = useState<Answer[]>([]);
  const [shake, setShake] = useState(0);
  const [finished, setFinished] = useState(false);

  const claim = HAND[index];
  const isLast = index === HAND.length - 1;

  const commit = useCallback(
    (side: "true" | "false", confidence: number) => {
      const current = HAND[index];
      const points = brierPoints(probabilityOfTrue(side, confidence), current.isTrue);
      const correct = (side === "true") === current.isTrue;

      setResolved({ side, confidence, points, correct });
      setHand((list) => [
        ...list,
        { claimId: current.id, side, confidence, correct, points },
      ]);

      if (correct) {
        sfx.good();
        haptics.good();
      } else {
        sfx.bad((confidence - 0.5) / 0.49);
        haptics.bad();
        // The table jolts in proportion to how sure you were. Being wrong at
        // 55% barely registers; being wrong at 95% is meant to sting.
        if (confidence > 0.72) setShake((n) => n + 1);
      }
    },
    [index],
  );

  const next = useCallback(() => {
    if (isLast) {
      const finalHand = hand;
      player.recordHand(
        finalHand,
        finalHand
          .filter((a) => a.correct)
          .map((a) => HAND.find((c) => c.id === a.claimId)!.concept),
      );
      setFinished(true);
      sfx.fanfare();
      haptics.done();
      return;
    }
    setIndex((i) => i + 1);
    setResolved(null);
    sfx.tap();
  }, [isLast, hand, player]);

  const replay = useCallback(() => {
    setIndex(0);
    setResolved(null);
    setHand([]);
    setFinished(false);
    sfx.tap();
  }, []);

  if (finished) {
    return (
      <div className="flex w-full justify-center px-4 pt-4">
        <HandSummary
          hand={hand}
          history={player.answers}
          streak={player.streak}
          onReplay={replay}
          onSeeCurve={onSeeCurve}
        />
      </div>
    );
  }

  return (
    <div
      key={shake}
      className={`flex w-full flex-col items-center px-4 ${
        shake && !reduceMotion ? "animate-shake" : ""
      }`}
    >
      <AnimatePresence mode="wait" initial={false}>
        {resolved ? (
          <motion.div key={`verdict-${claim.id}`} className="flex justify-center">
            <Verdict
              claim={claim}
              side={resolved.side}
              confidence={resolved.confidence}
              points={resolved.points}
              correct={resolved.correct}
              isLast={isLast}
              onNext={next}
            />
          </motion.div>
        ) : (
          <motion.div
            key={`card-${claim.id}`}
            initial={reduceMotion ? false : { opacity: 0, y: 30, scale: 0.94 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.34, ease: [0.22, 1, 0.36, 1] }}
            className="flex w-full flex-col items-center"
          >
            <p className="text-muted mb-4 max-w-[330px] text-center text-[0.875rem] leading-snug">
              Shove the card toward what you believe.{" "}
              <span className="text-cream font-semibold">Further means surer.</span>
            </p>

            <div className="relative flex w-full items-center justify-center">
              {index === 0 && (
                <>
                  <Chevrons side="left" />
                  <Chevrons side="right" />
                </>
              )}
              {/* The rest of the deck, waiting. */}
            <span
              aria-hidden
              className="card-back absolute top-3 h-[min(50vh,404px)] w-[min(86vw,344px)] rotate-[3.5deg] rounded-[22px] opacity-60 lg:h-[440px] lg:w-[368px]"
            />
            <span
              aria-hidden
              className="card-back absolute top-1.5 h-[min(50vh,404px)] w-[min(86vw,344px)] -rotate-[2.5deg] rounded-[22px] opacity-80 lg:h-[440px] lg:w-[368px]"
            />
              <PlayCard
                claim={claim}
                index={index}
                total={HAND.length}
                onCommit={commit}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/**
 * A breathing nudge on the first card only. It disappears for good once the
 * player has thrown one, because after that the gesture is theirs.
 */
function Chevrons({ side }: { side: "left" | "right" }) {
  const isLeft = side === "left";
  return (
    <span
      aria-hidden
      className={`pointer-events-none absolute top-1/2 hidden -translate-y-1/2 sm:flex ${
        isLeft ? "right-[calc(50%+215px)]" : "left-[calc(50%+215px)]"
      } items-center gap-1`}
    >
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className={`text-[1.5rem] leading-none ${isLeft ? "text-crimson" : "text-jade"}`}
          animate={{ opacity: [0.12, 1, 0.12] }}
          transition={{
            duration: 1.8,
            repeat: Infinity,
            delay: (isLeft ? 2 - i : i) * 0.16,
            ease: "easeInOut",
          }}
        >
          {isLeft ? "\u25c0" : "\u25b6"}
        </motion.span>
      ))}
    </span>
  );
}
