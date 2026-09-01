"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useMotionValue, useReducedMotion, useTransform } from "motion/react";
import type { Claim } from "@/lib/game/claims";
import { CONCEPT_BY_ID, SUITS } from "@/lib/game/concepts";
import { MAX_CONFIDENCE, MIN_CONFIDENCE } from "@/lib/game/scoring";
import { sfx } from "@/lib/sound";
import { haptics } from "@/lib/haptics";

/** Drag past this and the card is thrown. */
const COMMIT_AT = 104;
/** Full conviction. The card hits a wall here, so 99% has a physical edge. */
const MAX_DRAG = 236;

export function confidenceFromX(x: number): number {
  const t = Math.min(1, Math.abs(x) / MAX_DRAG);
  return MIN_CONFIDENCE + t * (MAX_CONFIDENCE - MIN_CONFIDENCE);
}

/**
 * The card.
 *
 * The whole game is in this gesture: you don't choose an answer from a list,
 * you shove the card toward the side you believe — and how far you shove it is
 * how sure you are. Confidence stops being a number you type and becomes
 * something your hand commits to, which is exactly the feeling the scoring
 * rule then holds you to.
 *
 * The bar underneath is not a fallback bolted on afterwards: it is the same
 * move, available precisely, for anyone not using a pointer.
 */
export function PlayCard({
  claim,
  index,
  total,
  onCommit,
}: {
  claim: Claim;
  index: number;
  total: number;
  onCommit: (side: "true" | "false", confidence: number) => void;
}) {
  const x = useMotionValue(0);
  const reduceMotion = useReducedMotion();
  const sliderRef = useRef<HTMLInputElement>(null);
  const lastNotch = useRef(0);
  const [thrown, setThrown] = useState<null | "true" | "false">(null);

  const concept = CONCEPT_BY_ID.get(claim.concept)!;
  const suit = SUITS[concept.suit];

  const rotate = useTransform(x, [-MAX_DRAG, 0, MAX_DRAG], [-13, 0, 13]);
  const trueGlow = useTransform(x, [0, COMMIT_AT, MAX_DRAG], [0, 0.5, 1]);
  const falseGlow = useTransform(x, [0, -COMMIT_AT, -MAX_DRAG], [0, 0.5, 1]);
  // The edge labels never vanish completely — a blank card hides the choice.
  const trueLabel = useTransform(x, [0, MAX_DRAG], [0.3, 1]);
  const falseLabel = useTransform(x, [0, -MAX_DRAG], [0.3, 1]);
  const percentText = useTransform(x, (value) =>
    Math.abs(value) < 6 ? "—" : `${Math.round(confidenceFromX(value) * 100)}%`,
  );
  const percentOpacity = useTransform(x, [-40, -8, 8, 40], [1, 0.35, 0.35, 1]);

  // Keep the precise control in step with the gesture, and click as conviction
  // climbs so the certainty can be heard as well as seen.
  useEffect(() => {
    const unsubscribe = x.on("change", (value) => {
      const confidence = confidenceFromX(value);
      const percent = Math.round(confidence * 100);
      if (sliderRef.current && Math.abs(value) > 6) {
        sliderRef.current.value = String(percent);
      }
      const notch = Math.floor(percent / 5);
      if (notch !== lastNotch.current && Math.abs(value) > 10) {
        lastNotch.current = notch;
        sfx.notch((confidence - MIN_CONFIDENCE) / (MAX_CONFIDENCE - MIN_CONFIDENCE));
        haptics.notch();
      }
    });
    return unsubscribe;
  }, [x]);

  function throwCard(side: "true" | "false", confidence: number) {
    if (thrown) return;
    setThrown(side);
    sfx.whoosh();
    haptics.throwCard();
    // Let the flight read before the verdict lands on top of it.
    window.setTimeout(() => onCommit(side, confidence), reduceMotion ? 0 : 260);
  }

  function commitFromBar(side: "true" | "false") {
    const percent = Number(sliderRef.current?.value ?? 75);
    x.set((side === "true" ? 1 : -1) * MAX_DRAG);
    throwCard(side, Math.min(MAX_CONFIDENCE, Math.max(MIN_CONFIDENCE, percent / 100)));
  }

  return (
    <div className="flex w-full flex-col items-center">
      <motion.div
        drag={thrown ? false : "x"}
        dragConstraints={{ left: -MAX_DRAG, right: MAX_DRAG }}
        dragElastic={0.08}
        dragMomentum={false}
        onDragStart={() => sfx.lift()}
        onDragEnd={(_, info) => {
          const past = Math.abs(info.offset.x) > COMMIT_AT;
          const flung = Math.abs(info.velocity.x) > 640;
          if (past || flung) {
            throwCard(info.offset.x > 0 ? "true" : "false", confidenceFromX(x.get()));
          } else {
            sfx.tap();
          }
        }}
        dragSnapToOrigin={!thrown}
        style={{ x, rotate }}
        animate={
          thrown
            ? {
                x: thrown === "true" ? 620 : -620,
                y: -60,
                rotate: thrown === "true" ? 34 : -34,
                opacity: 0,
              }
            : undefined
        }
        transition={
          thrown
            ? { duration: reduceMotion ? 0 : 0.3, ease: [0.4, 0, 1, 1] }
            : { type: "spring", stiffness: 420, damping: 34 }
        }
        whileDrag={{ scale: 1.03, cursor: "grabbing" }}
        className="card-face relative flex h-[min(50vh,404px)] w-[min(86vw,344px)] cursor-grab lg:h-[440px] lg:w-[368px] touch-none flex-col rounded-[22px] p-5 select-none sm:p-6"
      >
        {/* The side you are leaning toward bleeds into the card stock. */}
        <motion.span
          aria-hidden
          style={{ opacity: trueGlow }}
          className="pointer-events-none absolute inset-0 rounded-[22px]"
        >
          <span className="bg-jade absolute inset-0 rounded-[22px] opacity-[0.18]" />
          <span className="ring-jade absolute inset-0 rounded-[22px] ring-[3px] ring-inset" />
        </motion.span>
        <motion.span
          aria-hidden
          style={{ opacity: falseGlow }}
          className="pointer-events-none absolute inset-0 rounded-[22px]"
        >
          <span className="bg-crimson absolute inset-0 rounded-[22px] opacity-[0.16]" />
          <span className="ring-crimson absolute inset-0 rounded-[22px] ring-[3px] ring-inset" />
        </motion.span>

        {/* Corner index, the way a real card carries it. */}
        <div className="relative flex items-start justify-between">
          <span className="flex items-center gap-1.5">
            <span className="display text-[1.35rem] leading-none" style={{ color: suit.tint === "#eae4d6" ? "#151f1b" : suit.tint }}>
              {concept.rank}
            </span>
            <span className="text-[1.05rem] leading-none" style={{ color: suit.tint === "#eae4d6" ? "#151f1b" : suit.tint }}>
              {suit.glyph}
            </span>
          </span>
          <span className="text-ink-soft font-mono text-[0.625rem] tracking-[0.18em]">
            {String(index + 1).padStart(2, "0")} / {String(total).padStart(2, "0")}
          </span>
        </div>

        <p className="text-ink-soft relative mt-4 font-mono text-[0.5625rem] tracking-[0.2em] uppercase">
          {suit.label}
        </p>

        <div className="relative flex flex-1 items-center">
          <p className="display text-ink text-[1.55rem] leading-[1.14] sm:text-[1.78rem]">
            {claim.statement}
          </p>
        </div>

        <div className="relative">
          <div className="text-ink-soft flex items-end justify-between font-mono text-[0.6875rem] tracking-[0.16em]">
            <motion.span style={{ opacity: falseLabel }} className="text-crimson font-bold">
              ◀ FALSE
            </motion.span>
            <motion.span style={{ opacity: trueLabel }} className="text-jade font-bold">
              TRUE ▶
            </motion.span>
          </div>

          <motion.p
            style={{ opacity: percentOpacity }}
            className="display text-ink mt-2 text-center text-[2.6rem] leading-none"
          >
            {percentText}
          </motion.p>
          <p className="text-ink-soft mt-1 text-center font-mono text-[0.5625rem] tracking-[0.2em] uppercase">
            how sure
          </p>
        </div>
      </motion.div>

      {/* The precise path. Same move, no pointer required. */}
      <div className="mt-6 w-[min(92vw,420px)]">
        <div className="mb-1.5 flex items-center justify-between">
          <label htmlFor={`sure-${claim.id}`} className="label">
            How sure are you?
          </label>
          <span className="text-faint font-mono text-[0.625rem]">drag the card, or use this</span>
        </div>
        <input
          ref={sliderRef}
          id={`sure-${claim.id}`}
          type="range"
          min={50}
          max={99}
          defaultValue={75}
          disabled={thrown !== null}
          onChange={(event) => {
            const percent = Number(event.target.value);
            sfx.notch((percent - 50) / 49);
          }}
          className="conviction-slider"
        />
        <div className="mt-1 flex gap-2.5">
          <button
            type="button"
            disabled={thrown !== null}
            onClick={() => commitFromBar("false")}
            className="rail rail-hover text-crimson flex-1 rounded-2xl py-3 font-mono text-[0.8125rem] font-bold tracking-[0.14em] disabled:opacity-40"
          >
            FALSE
          </button>
          <button
            type="button"
            disabled={thrown !== null}
            onClick={() => commitFromBar("true")}
            className="rail rail-hover text-jade flex-1 rounded-2xl py-3 font-mono text-[0.8125rem] font-bold tracking-[0.14em] disabled:opacity-40"
          >
            TRUE
          </button>
        </div>
      </div>
    </div>
  );
}
