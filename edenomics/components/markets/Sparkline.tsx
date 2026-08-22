"use client";

import { useId, useMemo, useRef } from "react";
import { motion, useInView, useReducedMotion } from "motion/react";

/**
 * A small line chart that draws itself once on entry.
 *
 * Values are normalised 0–1. The path is memoised because these render in
 * long lists, and the draw-on uses pathLength so it costs nothing to animate.
 */
export function Sparkline({
  values,
  positive,
  width = 96,
  height = 32,
  strokeWidth = 1.5,
  area = false,
  stretch = false,
  label,
  className = "",
}: {
  values: number[];
  positive: boolean;
  width?: number;
  height?: number;
  strokeWidth?: number;
  area?: boolean;
  /** Fill the container in both axes instead of preserving the aspect ratio. */
  stretch?: boolean;
  /** Screen-reader description — charts without one are decoration. */
  label?: string;
  className?: string;
}) {
  const ref = useRef<SVGSVGElement>(null);
  const inView = useInView(ref, { once: true, margin: "-24px" });
  const reduceMotion = useReducedMotion();
  const gradientId = useId();

  const { line, fill } = useMemo(() => {
    const pad = strokeWidth;
    const usableHeight = height - pad * 2;
    const step = values.length > 1 ? width / (values.length - 1) : width;
    const points = values.map((v, i) => {
      const x = i * step;
      const y = pad + (1 - v) * usableHeight;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    });
    return {
      line: `M${points.join(" L")}`,
      fill: `M${points.join(" L")} L${width},${height} L0,${height} Z`,
    };
  }, [values, width, height, strokeWidth]);

  const color = positive ? "var(--color-up)" : "var(--color-down)";

  return (
    <svg
      ref={ref}
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      fill="none"
      preserveAspectRatio={stretch ? "none" : undefined}
      className={`overflow-visible ${className}`}
      role={label ? "img" : "presentation"}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    >
      {area && (
        <>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity="0.22" />
              <stop offset="100%" stopColor={color} stopOpacity="0" />
            </linearGradient>
          </defs>
          <motion.path
            d={fill}
            fill={`url(#${gradientId})`}
            initial={{ opacity: 0 }}
            animate={{ opacity: inView ? 1 : 0 }}
            transition={reduceMotion ? { duration: 0 } : { duration: 0.5, delay: 0.35 }}
          />
        </>
      )}
      <motion.path
        d={line}
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        // Keeps the line an even weight when the viewBox is stretched.
        vectorEffect={stretch ? "non-scaling-stroke" : undefined}
        initial={{ pathLength: 0 }}
        animate={{ pathLength: inView ? 1 : 0 }}
        transition={
          reduceMotion ? { duration: 0 } : { duration: 0.9, ease: [0.22, 1, 0.36, 1] }
        }
      />
    </svg>
  );
}
