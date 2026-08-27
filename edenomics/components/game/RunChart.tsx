"use client";

import { useId, useMemo } from "react";
import { motion, useReducedMotion } from "motion/react";

/**
 * The chart-call chart. Everything up to the cut is drawn; what happened next
 * stays hidden until the answer is in, then draws itself across the gap.
 *
 * The dashed marker at the cut is doing real work — it is the moment the
 * player is being asked to stand in.
 */
export function RunChart({
  values,
  revealAt,
  revealed,
  label,
}: {
  values: number[];
  revealAt: number;
  revealed: boolean;
  label: string;
}) {
  const reduceMotion = useReducedMotion();
  const gradientId = useId();

  const width = 640;
  const height = 200;
  const pad = 10;

  const { knownPath, futurePath, areaPath, cutX, rose } = useMemo(() => {
    const step = width / (values.length - 1);
    const toPoint = (v: number, i: number) => {
      const x = i * step;
      const y = pad + (1 - v) * (height - pad * 2);
      return [x, y] as const;
    };

    const points = values.map(toPoint);
    const known = points.slice(0, revealAt + 1);
    const future = points.slice(revealAt);

    const draw = (list: readonly (readonly [number, number])[]) =>
      `M${list.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" L")}`;

    return {
      knownPath: draw(known),
      futurePath: draw(future),
      areaPath: `${draw(known)} L${known[known.length - 1][0].toFixed(1)},${height} L0,${height} Z`,
      cutX: revealAt * step,
      rose: values[values.length - 1] >= values[revealAt],
    };
  }, [values, revealAt]);

  return (
    <div className="border-line relative overflow-hidden rounded-2xl border bg-black/30 p-3">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-[180px] w-full sm:h-[210px]"
        fill="none"
        preserveAspectRatio="none"
        role="img"
        aria-label={label}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--color-brand)" stopOpacity="0.28" />
            <stop offset="100%" stopColor="var(--color-brand)" stopOpacity="0" />
          </linearGradient>
        </defs>

        <path d={areaPath} fill={`url(#${gradientId})`} />

        <path
          d={knownPath}
          stroke="var(--color-brand)"
          strokeWidth={2.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          vectorEffect="non-scaling-stroke"
        />

        <line
          x1={cutX}
          y1={0}
          x2={cutX}
          y2={height}
          stroke="var(--color-line-strong)"
          strokeWidth={1}
          strokeDasharray="4 5"
          vectorEffect="non-scaling-stroke"
        />

        <motion.path
          d={futurePath}
          stroke={rose ? "var(--color-correct)" : "var(--color-wrong)"}
          strokeWidth={2.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          vectorEffect="non-scaling-stroke"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: revealed ? 1 : 0, opacity: revealed ? 1 : 0 }}
          transition={reduceMotion ? { duration: 0 } : { duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>

      <span
        className="label absolute top-3 right-4 text-[0.625rem]"
        style={{ left: `calc(${(cutX / width) * 100}% + 1rem)` }}
        aria-hidden
      >
        {revealed ? "" : "now"}
      </span>
    </div>
  );
}
