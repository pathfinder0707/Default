"use client";

import { useEffect, useState } from "react";

/**
 * Tracks which section the reader is in, so the header and the mobile tab bar
 * highlight the same thing.
 *
 * Measured against a line a third of the way down the viewport rather than by
 * intersection ratio: with an IntersectionObserver, scrolling through a
 * stretch of page that belongs to no navigable section leaves the last match
 * stuck on screen. Comparing positions always has an answer.
 */
export function useScrollSpy(sectionIds: readonly string[], fallback = sectionIds[0]): string {
  const [active, setActive] = useState(fallback);

  useEffect(() => {
    let frame = 0;

    const update = () => {
      frame = 0;
      const line = window.innerHeight * 0.32;
      let best = fallback;

      for (const id of sectionIds) {
        const element = document.getElementById(id);
        if (!element) continue;
        const { top, bottom } = element.getBoundingClientRect();
        if (top <= line && bottom > line) {
          best = id;
          break;
        }
        // Otherwise remember the last section that has already passed the line.
        if (top <= line) best = id;
      }

      // The final section can be too short to ever reach the line.
      const atBottom =
        window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2;
      if (atBottom) best = sectionIds[sectionIds.length - 1];

      setActive((current) => (current === best ? current : best));
    };

    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };

    // Kick off in a frame rather than inline, so the first paint is untouched.
    frame = requestAnimationFrame(update);
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);

    return () => {
      if (frame) cancelAnimationFrame(frame);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, [sectionIds, fallback]);

  return active;
}
