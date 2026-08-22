"use client";

import { motion, useReducedMotion } from "motion/react";
import { Check, Flame, Timer } from "lucide-react";
import { useProgress } from "@/lib/state/progress";
import { useMounted } from "@/lib/hooks/useMounted";

const XP_PER_LEVEL = 200;
const DAY_LABELS = ["M", "T", "W", "T", "F", "S", "S"];

/**
 * The habit surface: a streak, a level and a one-minute promise.
 *
 * Kept deliberately quiet — a streak is a reason to come back, not a slot
 * machine, so nothing here flashes or counts down.
 */
export function StreakPanel() {
  const { streak, xp, earnedToday, streakExtended } = useProgress();
  const mounted = useMounted();
  const reduceMotion = useReducedMotion();

  const level = Math.floor(xp / XP_PER_LEVEL) + 1;
  const intoLevel = xp % XP_PER_LEVEL;
  const progress = intoLevel / XP_PER_LEVEL;

  // Monday-indexed position of today, so the filled run ends on the right day.
  const todayIndex = mounted ? (new Date().getDay() + 6) % 7 : -1;

  return (
    <div className="border-line bg-elevated flex h-full flex-col rounded-2xl border p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="eyebrow mb-3">Your streak</p>
          <div className="flex items-baseline gap-2.5">
            <Flame size={26} className="text-accent translate-y-1" aria-hidden />
            <motion.span
              key={streak}
              initial={reduceMotion ? false : { opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              className="tabular text-[2.5rem] leading-none"
            >
              {streak}
            </motion.span>
            <span className="text-muted text-sm">day{streak === 1 ? "" : "s"}</span>
          </div>
        </div>

        {streakExtended && (
          <motion.span
            initial={reduceMotion ? false : { opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-up bg-up/10 inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[0.6875rem]"
          >
            <Check size={12} aria-hidden />
            Extended
          </motion.span>
        )}
      </div>

      <ul className="mt-6 flex gap-1.5" aria-label="This week">
        {DAY_LABELS.map((label, index) => {
          const isToday = index === todayIndex;
          const isDone = todayIndex >= 0 && (index < todayIndex || (isToday && streakExtended));
          return (
            <li key={`${label}-${index}`} className="flex flex-1 flex-col items-center gap-1.5">
              <span
                className={`h-8 w-full rounded-md transition-colors duration-300 ${
                  isDone
                    ? "bg-accent/70"
                    : isToday
                      ? "ring-accent/60 bg-white/[0.04] ring-1"
                      : "bg-white/[0.04]"
                }`}
              />
              <span className={`text-[0.625rem] ${isToday ? "text-accent" : "text-faint"}`}>
                {label}
              </span>
            </li>
          );
        })}
      </ul>

      <div className="mt-7">
        <div className="mb-2 flex items-baseline justify-between">
          <span className="text-[0.8125rem]">Level {level}</span>
          <span className="text-faint tabular text-[0.6875rem]">
            {intoLevel} / {XP_PER_LEVEL} XP
          </span>
        </div>
        <div
          className="h-1.5 w-full overflow-hidden rounded-full bg-white/[0.06]"
          role="progressbar"
          aria-valuenow={intoLevel}
          aria-valuemin={0}
          aria-valuemax={XP_PER_LEVEL}
          aria-label={`Progress to level ${level + 1}`}
        >
          <motion.div
            className="bg-accent h-full rounded-full"
            initial={false}
            animate={{ width: `${progress * 100}%` }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          />
        </div>
        {earnedToday > 0 && (
          <p className="text-accent mt-2 tabular text-[0.6875rem]">
            +{earnedToday} XP today
          </p>
        )}
      </div>

      <div className="border-line mt-auto flex items-center gap-2 border-t pt-5">
        <Timer size={14} className="text-faint" aria-hidden />
        <span className="text-muted text-[0.8125rem]">Today&rsquo;s challenge</span>
        <span className="text-faint ml-auto font-mono text-[0.6875rem]">1 min</span>
      </div>
    </div>
  );
}
