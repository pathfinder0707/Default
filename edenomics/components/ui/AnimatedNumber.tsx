"use client";

import { useEffect, useRef } from "react";
import { animate, useInView, useReducedMotion } from "motion/react";

/**
 * Counts up to a value the first time it scrolls into view, and re-counts
 * whenever the value changes — which is most of the point in a game, where
 * XP and balances move constantly.
 *
 * Frames are written straight to the DOM node. A counter that re-renders React
 * sixty times a second buys nothing, and the server-rendered markup already
 * holds the final value for anyone without JS.
 */
export function AnimatedNumber({
  value,
  format = (n) => Math.round(n).toLocaleString("en-IN"),
  className = "",
  duration = 0.9,
}: {
  value: number;
  format?: (n: number) => string;
  className?: string;
  duration?: number;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const previous = useRef(value);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    if (reduceMotion || !inView) {
      node.textContent = format(value);
      previous.current = value;
      return;
    }

    // Count from zero on first sight, then from the last value on every change.
    const from = previous.current === value ? 0 : previous.current;
    previous.current = value;

    const controls = animate(from, value, {
      duration,
      ease: [0.22, 1, 0.36, 1],
      onUpdate: (v) => {
        node.textContent = format(v);
      },
      onComplete: () => {
        node.textContent = format(value);
      },
    });

    return () => controls.stop();
  }, [inView, reduceMotion, value, format, duration]);

  return (
    <span ref={ref} className={className}>
      {format(value)}
    </span>
  );
}
