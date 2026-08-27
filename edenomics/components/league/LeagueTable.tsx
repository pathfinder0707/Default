"use client";

import { motion, useReducedMotion } from "motion/react";
import { ChevronUp, ChevronDown, Flame } from "lucide-react";
import { Container, SectionHeading } from "@/components/layout/Section";
import { Reveal } from "@/components/ui/Reveal";
import {
  LEAGUE_NAME,
  PROMOTION_SPOTS,
  RELEGATION_SPOTS,
  standings,
} from "@/lib/game/league";
import { usePlayer } from "@/lib/state/player";
import { formatXp } from "@/lib/game/format";

/**
 * The weekly league. Rows animate to their new position when a run lands, so
 * you watch yourself move rather than being told you did.
 */
export function LeagueTable() {
  const player = usePlayer();
  const reduceMotion = useReducedMotion();
  const table = standings({ xp: player.xp, streak: player.streak });
  const yourRank = table.findIndex((row) => row.isYou) + 1;
  const toPromotion = yourRank > PROMOTION_SPOTS ? table[PROMOTION_SPOTS - 1].xp - player.xp : 0;

  return (
    <section id="league" className="py-14 sm:py-20">
      <Container>
        <SectionHeading
          eyebrow={LEAGUE_NAME}
          title={
            <>
              Nine people.
              <br />
              <span className="text-muted">One week. No money.</span>
            </>
          }
          description="The only thing at stake is a place in next week's bracket. Top three go up, bottom two go down, and nothing can be bought."
          action={
            <div className="text-left sm:text-right">
              <p className="tabular text-2xl font-bold">#{yourRank}</p>
              <p className="label mt-1">
                {toPromotion > 0
                  ? `${formatXp(toPromotion)} XP to promotion`
                  : "in the promotion zone"}
              </p>
            </div>
          }
          className="mb-9"
        />

        <Reveal>
          <ol className="piece divide-line grid divide-y overflow-hidden rounded-3xl">
            {table.map((row, index) => {
              const rank = index + 1;
              const promoting = rank <= PROMOTION_SPOTS;
              const relegating = rank > table.length - RELEGATION_SPOTS;

              return (
                <motion.li
                  key={row.id}
                  layout={!reduceMotion}
                  transition={{ type: "spring", stiffness: 400, damping: 34 }}
                  className={`flex items-center gap-3 px-4 py-3.5 sm:gap-4 sm:px-6 ${
                    row.isYou ? "bg-brand/[0.09]" : ""
                  }`}
                >
                  <span
                    className={`tabular flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-[0.8125rem] font-bold ${
                      promoting
                        ? "bg-correct/20 text-correct"
                        : relegating
                          ? "bg-wrong/15 text-wrong"
                          : "bg-white/[0.06] text-faint"
                    }`}
                  >
                    {rank}
                  </span>

                  <span
                    className={`min-w-0 flex-1 truncate font-semibold ${
                      row.isYou ? "text-brand" : ""
                    }`}
                  >
                    {row.name}
                  </span>

                  <span className="text-faint hidden items-center gap-1.5 text-[0.8125rem] sm:flex">
                    <Flame size={13} className={row.streak >= 7 ? "text-streak" : ""} aria-hidden />
                    <span className="tabular">{row.streak}</span>
                  </span>

                  <span className="tabular w-20 shrink-0 text-right font-bold sm:w-24">
                    {formatXp(row.xp)}
                  </span>

                  <span className="w-4 shrink-0" aria-hidden>
                    {promoting && <ChevronUp size={16} className="text-correct" />}
                    {relegating && <ChevronDown size={16} className="text-wrong" />}
                  </span>
                </motion.li>
              );
            })}
          </ol>
        </Reveal>

        <Reveal delay={0.06}>
          <p className="text-faint mt-4 text-center text-[0.8125rem]">
            Rivals are illustrative. Finish a run and watch your row move.
          </p>
        </Reveal>
      </Container>
    </section>
  );
}
