"use client";

import { motion, useReducedMotion } from "motion/react";
import { Flame, Trophy, Zap } from "lucide-react";
import { Container } from "@/components/layout/Section";
import { DailyRun } from "@/components/game/DailyRun";
import { usePlayer } from "@/lib/state/player";
import { levelFor, levelTitle, standings } from "@/lib/game/league";
import { formatXp } from "@/lib/game/format";

/**
 * The hero is the game.
 *
 * No screenshot, no promise, no "get started" — the run is right there and
 * playable before anyone has decided whether they want it. Everything to the
 * left of it is just enough framing to explain what they are looking at.
 */
export function Hero() {
  const player = usePlayer();
  const reduceMotion = useReducedMotion();
  const { level } = levelFor(player.xp);
  const rank = standings({ xp: player.xp, streak: player.streak }).findIndex((r) => r.isYou) + 1;

  return (
    <section id="play" className="grain clip-decor relative pt-24 pb-14 sm:pt-28 lg:pt-32">
      {/* Two light sources, one per brand hue. Nothing else glows on the page. */}
      <div
        aria-hidden
        className="pointer-events-none absolute -top-32 -left-24 h-[460px] w-[560px] rounded-full opacity-[0.17] blur-[120px]"
        style={{ background: "radial-gradient(closest-side, var(--color-brand), transparent 70%)" }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -top-20 right-0 h-[420px] w-[520px] rounded-full opacity-[0.13] blur-[120px]"
        style={{ background: "radial-gradient(closest-side, var(--color-xp), transparent 70%)" }}
      />

      <Container className="relative">
        <div className="grid gap-10 lg:grid-cols-12 lg:items-start lg:gap-10">
          <div className="lg:col-span-6 xl:col-span-5">
            <motion.div
              initial={reduceMotion ? false : { opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
            >
              <span className="border-line inline-flex items-center gap-2 rounded-full border bg-white/[0.04] px-3 py-1.5 text-[0.75rem] font-semibold">
                <span className="bg-correct h-1.5 w-1.5 rounded-full" aria-hidden />
                Today&rsquo;s run is live
              </span>

              <h1 className="display mt-5 text-[2.9rem] sm:text-[4rem] lg:text-[4.3rem]">
                The market
                <br />
                is the <span className="text-brand">level.</span>
              </h1>

              <p className="text-muted mt-6 max-w-[44ch] text-[1.0625rem] leading-relaxed">
                Five rounds a day, about three minutes. One rule: you score by knowing{" "}
                <span className="text-fg font-semibold">why</span> a price moved — never by
                guessing which way it went.
              </p>

              <ul className="mt-8 flex flex-wrap gap-2.5">
                <li className="piece flex items-center gap-2 rounded-xl px-3 py-2">
                  <Flame size={16} className="text-streak" aria-hidden />
                  <span className="tabular text-[0.875rem] font-bold">{player.streak}</span>
                  <span className="text-faint text-[0.8125rem]">day streak</span>
                </li>
                <li className="piece flex items-center gap-2 rounded-xl px-3 py-2">
                  <Zap size={16} className="text-xp" aria-hidden />
                  <span className="text-[0.875rem] font-bold">
                    Lvl {level}
                    <span className="text-faint ml-1.5 font-normal">{levelTitle(level)}</span>
                  </span>
                </li>
                <li className="piece flex items-center gap-2 rounded-xl px-3 py-2">
                  <Trophy size={16} className="text-brand" aria-hidden />
                  <span className="tabular text-[0.875rem] font-bold">#{rank}</span>
                  <span className="text-faint text-[0.8125rem]">Silver league</span>
                </li>
              </ul>

              <p className="text-faint mt-7 text-[0.8125rem] leading-relaxed">
                {formatXp(player.xp)} XP banked · no account needed · nothing to buy, ever
              </p>
            </motion.div>
          </div>

          <motion.div
            initial={reduceMotion ? false : { opacity: 0, y: 28, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="lg:col-span-6 xl:col-span-7"
          >
            <DailyRun />
          </motion.div>
        </div>
      </Container>
    </section>
  );
}
