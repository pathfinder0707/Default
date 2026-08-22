"use client";

import { motion, useReducedMotion } from "motion/react";
import type { ReactNode } from "react";

/**
 * The house entrance animation: a short rise and fade, once, when a block
 * first comes into view. Transform and opacity only, so it never triggers
 * layout work.
 *
 * Reduced motion collapses the duration to zero rather than swapping in a
 * plain element. Switching element types mid-flight leaves Motion's inline
 * opacity behind — React does not clean up styles it never set — which
 * strands the block invisible. Same element, no travel, no delay.
 */
export function Reveal({
  children,
  delay = 0,
  y = 16,
  className,
  as = "div",
}: {
  children: ReactNode;
  delay?: number;
  y?: number;
  className?: string;
  as?: "div" | "section" | "li" | "article" | "header";
}) {
  const reduceMotion = useReducedMotion();
  const Component = motion[as];

  return (
    <Component
      className={className}
      initial={{ opacity: 0, y: reduceMotion ? 0 : y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-64px" }}
      transition={
        reduceMotion
          ? { duration: 0 }
          : { duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }
      }
    >
      {children}
    </Component>
  );
}
