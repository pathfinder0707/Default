"use client";

import { useEffect, useRef } from "react";
import { animate, useInView, useReducedMotion } from "motion/react";

/**
 * Counts a pre-formatted price up to its final value the first time it
 * scrolls into view.
 *
 * The display string is treated as a template: only its digits are replaced,
 * so currency symbols, decimal points and grouping — including Indian
 * grouping like ₹1,04,280 — survive untouched. The count starts at the
 * smallest number with the same digit count, which keeps the width stable and
 * avoids layout shift mid-animation.
 *
 * Frames are written straight to the DOM node rather than through state: a
 * counter re-rendering React sixty times a second buys nothing, and the
 * server-rendered markup already holds the final value for anyone without JS.
 */
export function AnimatedNumber({
  display,
  className = "",
  duration = 1.1,
}: {
  display: string;
  className?: string;
  duration?: number;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-40px" });
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    if (reduceMotion) {
      // Restore the real figure in case a previous pass parked it at the
      // starting value before the media query resolved.
      node.textContent = display;
      return;
    }

    const digits = display.replace(/\D/g, "");
    const target = Number(digits);
    const from = Math.pow(10, digits.length - 1);
    if (!digits.length || digits.length > 15 || target <= from) return;

    const paint = (value: number) => {
      const next = String(Math.round(value)).padStart(digits.length, "0");
      let cursor = 0;
      node.textContent = display.replace(/\d/g, () => next[cursor++] ?? "0");
    };

    if (!inView) {
      // Hold at the starting value until the number is actually on screen.
      paint(from);
      return;
    }

    const controls = animate(from, target, {
      duration,
      ease: [0.22, 1, 0.36, 1],
      onUpdate: paint,
      onComplete: () => {
        node.textContent = display;
      },
    });

    return () => {
      controls.stop();
      node.textContent = display;
    };
  }, [inView, reduceMotion, display, duration]);

  return (
    <span ref={ref} className={className}>
      {display}
    </span>
  );
}
