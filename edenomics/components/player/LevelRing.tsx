"use client";

import { motion, useReducedMotion } from "motion/react";

/**
 * Level as a ring rather than a bar. It reads as a badge you carry rather than
 * a task you are completing, which is the right feeling for a level.
 */
export function LevelRing({
  level,
  progress,
  size = 132,
}: {
  level: number;
  /** 0–1 through the current level. */
  progress: number;
  size?: number;
}) {
  const reduceMotion = useReducedMotion();
  const stroke = 9;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90" aria-hidden>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={stroke}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--color-xp)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          whileInView={{ strokeDashoffset: circumference * (1 - progress) }}
          viewport={{ once: true, margin: "-40px" }}
          transition={reduceMotion ? { duration: 0 } : { duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>

      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="label text-[0.5625rem]">Level</span>
        <span className="tabular text-4xl leading-none font-bold">{level}</span>
      </div>
    </div>
  );
}
