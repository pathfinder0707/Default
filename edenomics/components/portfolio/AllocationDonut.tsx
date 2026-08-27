"use client";

import { motion, useReducedMotion } from "motion/react";
import { ASSET_CLASSES } from "@/lib/game/portfolio";

/**
 * The allocation, as a ring. Segments are drawn with dash offsets rather than
 * arc paths so each one can animate its own length independently as the
 * sliders move.
 */
export function AllocationDonut({
  allocation,
  size = 200,
}: {
  allocation: Record<string, number>;
  size?: number;
}) {
  const reduceMotion = useReducedMotion();
  const stroke = 26;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const total = Object.values(allocation).reduce((sum, v) => sum + v, 0) || 1;

  // Prefix sums rather than a running accumulator: six assets makes the extra
  // work free, and nothing is mutated while rendering.
  const shares = ASSET_CLASSES.map((asset) => (allocation[asset.id] ?? 0) / total);
  const segments = ASSET_CLASSES.map((asset, index) => ({
    asset,
    share: shares[index],
    offset: shares.slice(0, index).reduce((sum, share) => sum + share, 0),
  })).filter((segment) => segment.share > 0.001);

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className="-rotate-90"
      role="img"
      aria-label={`Allocation: ${segments
        .map((s) => `${s.asset.label} ${Math.round(s.share * 100)}%`)
        .join(", ")}`}
    >
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="rgba(255,255,255,0.06)"
        strokeWidth={stroke}
      />
      {segments.map(({ asset, share, offset: start }) => (
        <motion.circle
          key={asset.id}
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={asset.tint}
          strokeWidth={stroke}
          strokeLinecap="butt"
          initial={false}
          animate={{
            strokeDasharray: `${share * circumference} ${circumference}`,
            strokeDashoffset: -start * circumference,
          }}
          transition={reduceMotion ? { duration: 0 } : { duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
        />
      ))}
    </svg>
  );
}
