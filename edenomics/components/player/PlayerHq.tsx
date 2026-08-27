"use client";

import { Flame, Snowflake, Zap } from "lucide-react";
import { Container, SectionHeading } from "@/components/layout/Section";
import { Reveal } from "@/components/ui/Reveal";
import { AnimatedNumber } from "@/components/ui/AnimatedNumber";
import { LevelRing } from "@/components/player/LevelRing";
import { StreakCalendar } from "@/components/player/StreakCalendar";
import { BadgeShelf } from "@/components/player/BadgeShelf";
import { usePlayer } from "@/lib/state/player";
import { levelFor, levelTitle } from "@/lib/game/league";
import { formatXp } from "@/lib/game/format";

/**
 * Everything the player has to show for themselves, in one place. It reads
 * live from the same store the run writes to, so finishing a run moves the
 * ring, the calendar and the badge shelf at once.
 */
export function PlayerHq() {
  const player = usePlayer();
  const { level, into, span } = levelFor(player.xp);

  return (
    <section id="progress" className="py-14 sm:py-20">
      <Container>
        <SectionHeading
          eyebrow="Your record"
          title={
            <>
              Proof you&rsquo;re
              <br />
              <span className="text-brand">getting better.</span>
            </>
          }
          description="Not a dashboard of your money — a record of what you understand. The only number here you cannot fake is the streak."
          className="mb-9"
        />

        <div className="grid gap-4 lg:grid-cols-12">
          {/* Level */}
          <Reveal className="lg:col-span-4">
            <div className="piece flex h-full flex-col items-center rounded-3xl p-6 text-center">
              <LevelRing level={level} progress={into / span} />
              <p className="font-display mt-4 text-xl font-bold">{levelTitle(level)}</p>
              <p className="tabular text-faint mt-1 text-[0.8125rem]">
                {formatXp(into)} / {formatXp(span)} XP to level {level + 1}
              </p>

              <div className="border-line mt-6 flex w-full items-center justify-between border-t pt-5">
                <span className="text-muted flex items-center gap-2 text-[0.8125rem]">
                  <Zap size={15} className="text-xp" aria-hidden />
                  Total XP
                </span>
                <span className="tabular text-lg font-bold">
                  <AnimatedNumber value={player.xp} format={formatXp} />
                </span>
              </div>
            </div>
          </Reveal>

          {/* Streak */}
          <Reveal delay={0.06} className="lg:col-span-4">
            <div className="piece flex h-full flex-col rounded-3xl p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-display text-lg font-bold">Streak</h3>
                  <div className="mt-2 flex items-baseline gap-2">
                    <Flame size={28} className="text-streak translate-y-1" aria-hidden />
                    <span className="tabular text-5xl leading-none font-bold">
                      {player.streak}
                    </span>
                    <span className="text-muted text-sm">days</span>
                  </div>
                </div>

                <span
                  className="border-brand/30 bg-brand/10 text-brand flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[0.75rem] font-semibold"
                  title="Freezes cover a day you miss, automatically."
                >
                  <Snowflake size={13} aria-hidden />
                  {player.freezes} freezes
                </span>
              </div>

              <div className="mt-6">
                <StreakCalendar streak={player.streak} />
              </div>

              <p className="text-muted border-line mt-auto border-t pt-5 text-[0.8125rem] leading-relaxed">
                Miss a day and a freeze covers it automatically. The streak is meant to
                pull you back, not punish you.
              </p>
            </div>
          </Reveal>

          {/* Badges */}
          <Reveal delay={0.12} className="lg:col-span-4">
            <div className="piece h-full rounded-3xl p-6">
              <BadgeShelf
                state={{
                  xp: player.xp,
                  streak: player.streak,
                  runsDone: player.runsCompleted,
                  bestCombo: player.bestCombo,
                }}
              />
              <p className="text-muted border-line mt-6 border-t pt-5 text-[0.8125rem] leading-relaxed">
                Badges mark things you did, not things you bought. There is nothing to
                purchase anywhere in Edenomics.
              </p>
            </div>
          </Reveal>
        </div>
      </Container>
    </section>
  );
}
