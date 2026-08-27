"use client";

/**
 * Tiny haptic taps on devices that support them. Purely additive — the game
 * reads identically without it, and it stays silent where the API is missing
 * or the user has asked for reduced motion.
 */
function buzz(pattern: number | number[]) {
  if (typeof window === "undefined") return;
  if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
  try {
    window.navigator.vibrate?.(pattern);
  } catch {
    // Unsupported or blocked by the browser — nothing to do.
  }
}

export const haptics = {
  tap: () => buzz(8),
  correct: () => buzz([12, 40, 22]),
  wrong: () => buzz(28),
  levelUp: () => buzz([16, 50, 16, 50, 40]),
};
