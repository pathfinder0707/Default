"use client";

import { motion, useReducedMotion } from "motion/react";
import { Award, Lock } from "lucide-react";
import { BADGES } from "@/lib/game/league";

export function BadgeShelf({
  state,
}: {
  state: { xp: number; streak: number; runsDone: number; bestCombo: number };
}) {
  const reduceMotion = useReducedMotion();
  const earnedCount = BADGES.filter((badge) => badge.earned(state)).length;

  return (
    <div>
      <div className="mb-4 flex items-baseline justify-between">
        <h3 className="font-display text-lg font-bold">Badges</h3>
        <span className="tabular text-faint text-[0.8125rem]">
          {earnedCount}/{BADGES.length}
        </span>
      </div>

      <ul className="grid grid-cols-3 gap-2.5">
        {BADGES.map((badge, index) => {
          const earned = badge.earned(state);
          return (
            <li key={badge.id}>
              <motion.div
                initial={reduceMotion ? false : { scale: 0.8, opacity: 0 }}
                whileInView={{ scale: 1, opacity: 1 }}
                viewport={{ once: true }}
                transition={{
                  delay: index * 0.04,
                  type: "spring",
                  stiffness: 380,
                  damping: 22,
                }}
                title={badge.detail}
                className={`flex h-full flex-col items-center gap-1.5 rounded-2xl border p-3 text-center ${
                  earned
                    ? "border-xp/40 bg-xp/[0.08]"
                    : "border-line bg-white/[0.02] opacity-55"
                }`}
              >
                {earned ? (
                  <Award size={20} className="text-xp" aria-hidden />
                ) : (
                  <Lock size={18} className="text-faint" aria-hidden />
                )}
                <span
                  className={`text-[0.6875rem] leading-tight font-semibold ${
                    earned ? "text-fg" : "text-faint"
                  }`}
                >
                  {badge.label}
                </span>
              </motion.div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
