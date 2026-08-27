"use client";

import { motion, useReducedMotion } from "motion/react";
import { useMounted } from "@/lib/hooks/useMounted";

const DAY_INITIALS = ["S", "M", "T", "W", "T", "F", "S"];

/**
 * The last fourteen days. Today is ringed, past days in the streak are filled,
 * and anything beyond the streak stays empty — so the picture matches the
 * number without needing a legend.
 */
export function StreakCalendar({ streak }: { streak: number }) {
  const mounted = useMounted();
  const reduceMotion = useReducedMotion();

  // Rendered blank until mounted: the grid depends on what day it is locally,
  // which the server cannot know.
  const todayIndex = mounted ? new Date().getDay() : -1;

  return (
    <div>
      <div className="grid grid-cols-7 gap-1.5">
        {Array.from({ length: 14 }, (_, cell) => {
          // Cell 13 is today; count backwards from there.
          const daysAgo = 13 - cell;
          const inStreak = mounted && daysAgo < streak;
          const isToday = cell === 13;
          const weekday = todayIndex >= 0 ? (todayIndex - daysAgo + 70) % 7 : -1;

          return (
            <motion.div
              key={cell}
              initial={reduceMotion ? false : { scale: 0.6, opacity: 0 }}
              whileInView={{ scale: 1, opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: cell * 0.018, type: "spring", stiffness: 400, damping: 24 }}
              className={`flex aspect-square items-center justify-center rounded-lg text-[0.625rem] font-bold transition-colors ${
                inStreak ? "bg-streak text-void" : "bg-white/[0.05]"
              } ${isToday ? "ring-fg/70 ring-offset-void ring-2 ring-offset-2" : ""}`}
            >
              <span className={inStreak ? "" : "text-faint"}>
                {weekday >= 0 ? DAY_INITIALS[weekday] : ""}
              </span>
            </motion.div>
          );
        })}
      </div>
      <p className="text-faint mt-3 text-[0.75rem]">
        Last fourteen days. Today is the ringed square.
      </p>
    </div>
  );
}
