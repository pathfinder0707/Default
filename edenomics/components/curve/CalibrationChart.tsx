"use client";

import { motion, useReducedMotion } from "motion/react";
import type { CalibrationBucket } from "@/lib/game/scoring";

const X_MIN = 50;
const Y_MIN = 30;

const toX = (percent: number) => ((percent - X_MIN) / (100 - X_MIN)) * 100;
const toY = (percent: number) => 100 - ((percent - Y_MIN) / (100 - Y_MIN)) * 100;

/**
 * Stated confidence against how often you were actually right.
 *
 * The dashed diagonal is perfect calibration — say 80%, be right 80% of the
 * time. Almost everyone sits below it, and seeing your own dots sag under the
 * line is a more convincing argument about overconfidence than any amount of
 * being told.
 */
export function CalibrationChart({ buckets }: { buckets: CalibrationBucket[] }) {
  const reduceMotion = useReducedMotion();
  const plotted = buckets.filter((bucket) => bucket.count > 0);

  const path = plotted
    .map(
      (bucket, index) =>
        `${index === 0 ? "M" : "L"}${toX(bucket.stated * 100).toFixed(1)},${toY(bucket.actual * 100).toFixed(1)}`,
    )
    .join(" ");

  const summary = plotted
    .map(
      (b) =>
        `at ${Math.round(b.from * 100)}–${Math.round(b.to * 100)}% you were right ${Math.round(b.actual * 100)}% of the time across ${b.count} calls`,
    )
    .join("; ");

  return (
    <figure className="w-full">
      <div className="relative">
        <svg
          viewBox="-2 -2 104 104"
          className="w-full"
          role="img"
          aria-label={`Calibration curve. Perfect calibration is the diagonal. Your record: ${summary}.`}
        >
          {/* Grid */}
          {[60, 70, 80, 90, 100].map((tick) => (
            <g key={`x${tick}`}>
              <line
                x1={toX(tick)}
                y1={0}
                x2={toX(tick)}
                y2={100}
                stroke="var(--color-line)"
                strokeWidth={0.35}
              />
            </g>
          ))}
          {[40, 60, 80, 100].map((tick) => (
            <line
              key={`y${tick}`}
              x1={0}
              y1={toY(tick)}
              x2={100}
              y2={toY(tick)}
              stroke="var(--color-line)"
              strokeWidth={0.35}
            />
          ))}

          {/* Perfect calibration */}
          <motion.line
            x1={toX(50)}
            y1={toY(50)}
            x2={toX(100)}
            y2={toY(100)}
            stroke="var(--color-brass)"
            strokeWidth={0.8}
            strokeDasharray="3 2.5"
            strokeOpacity={0.75}
            initial={reduceMotion ? false : { pathLength: 0 }}
            whileInView={{ pathLength: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
          />

          {/* Your curve */}
          {plotted.length > 1 && (
            <motion.path
              d={path}
              fill="none"
              stroke="var(--color-jade)"
              strokeWidth={1.3}
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={reduceMotion ? false : { pathLength: 0 }}
              whileInView={{ pathLength: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 1.1, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
            />
          )}

          {plotted.map((bucket, index) => (
            <motion.circle
              key={bucket.from}
              cx={toX(bucket.stated * 100)}
              cy={toY(bucket.actual * 100)}
              r={2 + Math.min(3.2, Math.sqrt(bucket.count) * 0.9)}
              fill="var(--color-jade)"
              stroke="var(--color-felt)"
              strokeWidth={0.8}
              initial={reduceMotion ? false : { scale: 0, opacity: 0 }}
              whileInView={{ scale: 1, opacity: 1 }}
              viewport={{ once: true }}
              transition={{
                delay: 0.5 + index * 0.09,
                type: "spring",
                stiffness: 400,
                damping: 18,
              }}
            />
          ))}
        </svg>

        <span className="label absolute top-1 right-1 text-[0.5rem]">perfect</span>
      </div>

      <figcaption className="mt-3 flex items-center justify-between">
        <span className="label">50% sure →</span>
        <span className="label">→ 99% sure</span>
      </figcaption>
      <p className="text-faint mt-1 text-center font-mono text-[0.625rem] tracking-wide">
        vertical: how often you were actually right
      </p>
    </figure>
  );
}
