"use client";

/** Short taps where the device supports them. Silent everywhere else. */
function buzz(pattern: number | number[]) {
  if (typeof window === "undefined") return;
  if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
  try {
    window.navigator.vibrate?.(pattern);
  } catch {
    // Unsupported or blocked.
  }
}

export const haptics = {
  notch: () => buzz(4),
  throwCard: () => buzz(14),
  good: () => buzz([10, 40, 20]),
  bad: () => buzz([30, 45, 30]),
  done: () => buzz([12, 50, 12, 50, 36]),
};
