"use client";

import { motion, useReducedMotion } from "motion/react";
import { Flame } from "lucide-react";
import { COMBO_STEPS, comboMultiplier } from "@/lib/game/rounds";

/**
 * The combo. Five pips, one per consecutive correct answer, and a multiplier
 * that grows with them — so a clean run is worth roughly double a scrappy one
 * without any round being worth more on its own.
 */
export function ComboMeter({ combo }: { combo: number }) {
  const reduceMotion = useReducedMotion();
  const multiplier = comboMultiplier(combo);
  const maxed = combo >= COMBO_STEPS.length - 1;

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-1" aria-hidden>
        {COMBO_STEPS.map((_, index) => {
          const lit = index < combo;
          return (
            <motion.span
              key={index}
              animate={
                reduceMotion ? undefined : { scale: lit ? 1 : 0.75, opacity: lit ? 1 : 0.3 }
              }
              transition={{ type: "spring", stiffness: 520, damping: 22 }}
              className={`h-2 w-5 rounded-full ${lit ? "bg-xp" : "bg-white/20"}`}
            />
          );
        })}
      </div>

      <motion.span
        key={multiplier}
        initial={reduceMotion ? false : { scale: 0.7, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 500, damping: 20 }}
        className={`tabular relative inline-flex items-center gap-1 overflow-hidden rounded-full px-2.5 py-1 text-[0.8125rem] font-bold ${
          combo > 0 ? "bg-xp/15 text-xp" : "bg-white/[0.06] text-faint"
        }`}
      >
        {combo > 0 && <Flame size={13} aria-hidden />}
        {multiplier}×{maxed && <span className="sheen absolute inset-0" aria-hidden />}
      </motion.span>

      <span className="sr-only">
        Combo {combo} of {COMBO_STEPS.length - 1}, scoring {multiplier} times
      </span>
    </div>
  );
}
