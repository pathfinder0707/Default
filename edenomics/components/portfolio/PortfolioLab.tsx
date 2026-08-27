"use client";

import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { AlertTriangle, Lock } from "lucide-react";
import { Container, SectionHeading } from "@/components/layout/Section";
import { Reveal } from "@/components/ui/Reveal";
import { Button } from "@/components/ui/Button";
import { AllocationDonut } from "@/components/portfolio/AllocationDonut";
import {
  ASSET_CLASSES,
  SCENARIOS,
  STARTING_BALANCE,
  portfolioStats,
  scenarioReturn,
} from "@/lib/game/portfolio";
import { SKILL_BY_ID } from "@/lib/game/skills";
import { usePlayer } from "@/lib/state/player";
import { formatInr, formatSignedPct } from "@/lib/game/format";
import { haptics } from "@/lib/haptics";

/**
 * Play money, real constraints.
 *
 * The rule that makes this teach rather than entertain: an asset class stays
 * locked until you have mastered its node. Every brokerage app on earth is
 * arranged the other way round — buy first, understand later.
 */
export function PortfolioLab() {
  const player = usePlayer();
  const [stressed, setStressed] = useState<string | null>(null);
  const reduceMotion = useReducedMotion();

  const allocation = player.allocation;
  const total = Object.values(allocation).reduce((sum, v) => sum + v, 0) || 1;
  const stats = portfolioStats(allocation);
  const scenario = SCENARIOS.find((s) => s.id === stressed) ?? null;
  const shockReturn = scenario ? scenarioReturn(allocation, scenario) : null;

  const isUnlocked = (assetId: string) => {
    const asset = ASSET_CLASSES.find((a) => a.id === assetId)!;
    if (!asset.requires) return true;
    return (player.mastery[asset.requires] ?? 0) >= 100;
  };

  function setWeight(assetId: string, weight: number) {
    player.setAllocation({ ...allocation, [assetId]: weight });
    setStressed(null);
  }

  const concentrated = ASSET_CLASSES.find(
    (asset) => (allocation[asset.id] ?? 0) / total > 0.6,
  );

  return (
    <section id="lab" className="py-14 sm:py-20">
      <Container>
        <SectionHeading
          eyebrow="Portfolio lab"
          title={
            <>
              Ten lakh of play money.
              <br />
              <span className="text-muted">Unlocked one idea at a time.</span>
            </>
          }
          description="You can only allocate to something the game has already taught you. Master the node, unlock the asset — which is the opposite order to every brokerage app you have ever opened."
          className="mb-9"
        />

        <div className="grid gap-4 lg:grid-cols-12">
          {/* Sliders */}
          <Reveal className="lg:col-span-7">
            <div className="piece h-full rounded-3xl p-5 sm:p-6">
              <ul className="grid gap-3">
                {ASSET_CLASSES.map((asset) => {
                  const unlocked = isUnlocked(asset.id);
                  const weight = allocation[asset.id] ?? 0;
                  const share = (weight / total) * 100;
                  const gate = asset.requires ? SKILL_BY_ID.get(asset.requires) : null;

                  return (
                    <li
                      key={asset.id}
                      className={`border-line rounded-2xl border p-4 transition-opacity ${
                        unlocked ? "bg-black/20" : "bg-black/10 opacity-70"
                      }`}
                    >
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                        <span
                          className="h-3 w-3 shrink-0 rounded-full"
                          style={{ backgroundColor: asset.tint }}
                          aria-hidden
                        />
                        <span className="font-semibold">{asset.label}</span>

                        {unlocked ? (
                          <span className="tabular ml-auto text-lg font-bold">
                            {share.toFixed(0)}%
                          </span>
                        ) : (
                          <span className="text-faint ml-auto flex items-center gap-1.5 text-[0.75rem]">
                            <Lock size={12} aria-hidden />
                            Master {gate?.label}
                          </span>
                        )}
                      </div>

                      <p className="text-faint mt-1 text-[0.8125rem] leading-relaxed">
                        {asset.blurb}
                      </p>

                      <div className="mt-3 flex items-center gap-3">
                        <input
                          type="range"
                          min={0}
                          max={100}
                          step={5}
                          value={weight}
                          disabled={!unlocked}
                          onChange={(e) => setWeight(asset.id, Number(e.target.value))}
                          onPointerUp={() => haptics.tap()}
                          className="slider !h-8"
                          aria-label={`${asset.label} allocation`}
                          aria-valuetext={`${share.toFixed(0)} percent`}
                        />
                        <span className="tabular text-faint w-24 shrink-0 text-right text-[0.75rem]">
                          {asset.volatility === 0
                            ? "no swing"
                            : `±${asset.volatility}% swing`}
                        </span>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          </Reveal>

          {/* Read-out */}
          <Reveal delay={0.08} className="lg:col-span-5">
            <div className="piece flex h-full flex-col items-center rounded-3xl p-6">
              <div className="relative">
                <AllocationDonut allocation={allocation} />
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <AnimatePresence mode="wait" initial={false}>
                    {shockReturn === null ? (
                      <motion.div
                        key="normal"
                        initial={reduceMotion ? false : { opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={reduceMotion ? undefined : { opacity: 0, scale: 0.9 }}
                        className="text-center"
                      >
                        <span className="label block text-[0.5625rem]">Expected</span>
                        <span className="tabular block text-3xl font-bold">
                          {stats.expectedReturn.toFixed(1)}%
                        </span>
                        <span className="text-faint text-[0.6875rem]">a year</span>
                      </motion.div>
                    ) : (
                      <motion.div
                        key="shocked"
                        initial={reduceMotion ? false : { opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={reduceMotion ? undefined : { opacity: 0, scale: 0.9 }}
                        className="text-center"
                      >
                        <span className="label block text-[0.5625rem]">{scenario?.label}</span>
                        <span
                          className={`tabular block text-3xl font-bold ${
                            shockReturn >= 0 ? "text-correct" : "text-wrong"
                          }`}
                        >
                          {formatSignedPct(shockReturn)}
                        </span>
                        <span className="text-faint tabular text-[0.6875rem]">
                          {formatInr(STARTING_BALANCE * (1 + shockReturn / 100))}
                        </span>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>

              <div className="mt-6 grid w-full grid-cols-2 gap-3">
                <div className="border-line rounded-xl border bg-black/20 p-3 text-center">
                  <span className="label block text-[0.5625rem]">Swing</span>
                  <span className="tabular mt-1 block text-lg font-bold">
                    ±{stats.volatility.toFixed(0)}%
                  </span>
                </div>
                <div className="border-line rounded-xl border bg-black/20 p-3 text-center">
                  <span className="label block text-[0.5625rem]">Balance</span>
                  <span className="tabular mt-1 block text-lg font-bold">
                    {formatInr(STARTING_BALANCE)}
                  </span>
                </div>
              </div>

              {concentrated && (
                <p className="text-streak border-streak/30 bg-streak/[0.08] mt-4 flex w-full items-start gap-2 rounded-xl border p-3 text-[0.8125rem] leading-relaxed">
                  <AlertTriangle size={15} className="mt-0.5 shrink-0" aria-hidden />
                  <span>
                    Over 60% in {concentrated.label.toLowerCase()}. That is a bet on one
                    thing, not a portfolio.
                  </span>
                </p>
              )}

              <div className="mt-6 w-full">
                <p className="label mb-2.5">Stress test it</p>
                <div className="grid gap-2">
                  {SCENARIOS.map((item) => (
                    <Button
                      key={item.id}
                      variant={stressed === item.id ? "primary" : "secondary"}
                      size="sm"
                      className="w-full justify-between"
                      onClick={() => {
                        setStressed(stressed === item.id ? null : item.id);
                        haptics.tap();
                      }}
                    >
                      <span>{item.label}</span>
                      <span className="tabular text-[0.75rem] opacity-70">
                        {formatSignedPct(scenarioReturn(allocation, item), 0)}
                      </span>
                    </Button>
                  ))}
                </div>
                {scenario && (
                  <p className="text-faint mt-3 text-[0.8125rem] leading-relaxed">
                    {scenario.detail}
                  </p>
                )}
              </div>
            </div>
          </Reveal>
        </div>

        <Reveal delay={0.12}>
          <p className="text-faint mx-auto mt-6 max-w-2xl text-center text-[0.8125rem] leading-relaxed">
            Figures are illustrative and the money is not real. There is no leverage here
            and nothing settles faster than a week — a game that rewarded quick trading
            would be teaching the wrong lesson.
          </p>
        </Reveal>
      </Container>
    </section>
  );
}
