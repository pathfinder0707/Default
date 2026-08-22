"use client";

import { greeting, longDate } from "@/lib/market-clock";
import { useMounted } from "@/lib/hooks/useMounted";

/**
 * Client-only because it reads the visitor's clock. Until it mounts the
 * heading holds its space with a skeleton so nothing jumps.
 */
export function BriefGreeting({ count }: { count: number }) {
  const mounted = useMounted();

  return (
    <div>
      <p className="eyebrow mb-3">Daily brief</p>
      <h2 className="display text-[2.1rem] leading-[1.05] sm:text-[2.8rem] lg:text-[3.2rem]">
        {mounted ? (
          greeting()
        ) : (
          <span className="skeleton inline-block h-[0.8em] w-[7ch] rounded align-middle" />
        )}
        .
        <br />
        <span className="text-muted">
          Here are the {count} things that moved money today.
        </span>
      </h2>
    </div>
  );
}

export function BriefDateline() {
  const mounted = useMounted();
  return (
    <span className="text-faint font-mono text-[0.6875rem] tracking-wide">
      {mounted ? longDate() : " "}
    </span>
  );
}
