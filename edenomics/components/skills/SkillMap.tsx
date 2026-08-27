"use client";

import { useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { Check, Lock, Sparkles } from "lucide-react";
import { Container, SectionHeading } from "@/components/layout/Section";
import { Reveal } from "@/components/ui/Reveal";
import { ButtonLink } from "@/components/ui/Button";
import {
  BRANCH_LABELS,
  BRANCH_TINTS,
  SKILLS,
  SKILL_BY_ID,
  SKILL_EDGES,
  childrenOf,
  isUnlocked,
} from "@/lib/game/skills";
import { ASSET_CLASSES } from "@/lib/game/portfolio";
import { usePlayer } from "@/lib/state/player";
import type { SkillId } from "@/lib/game/types";

/**
 * The constellation.
 *
 * Edges live in SVG so they can curve and glow; the nodes are HTML on top, so
 * their labels stay a fixed size however small the map gets, and each one is a
 * real button — hoverable, tabbable, and answerable from the keyboard.
 */
export function SkillMap() {
  const player = usePlayer();
  const [selected, setSelected] = useState<SkillId>("markets");
  const reduceMotion = useReducedMotion();

  const skill = SKILL_BY_ID.get(selected)!;
  const mastery = player.mastery[selected] ?? 0;
  const unlocked = isUnlocked(skill, player.mastery);
  const unlockedAsset = skill.unlocks
    ? ASSET_CLASSES.find((asset) => asset.id === skill.unlocks)
    : undefined;

  const mastered = SKILLS.filter((s) => (player.mastery[s.id] ?? 0) >= 100).length;
  const started = SKILLS.filter((s) => (player.mastery[s.id] ?? 0) > 0).length;

  return (
    <section id="skills" className="py-14 sm:py-20">
      <Container>
        <SectionHeading
          eyebrow="Skill map"
          title={
            <>
              Fourteen ideas.
              <br />
              <span className="text-muted">That&rsquo;s the whole of it.</span>
            </>
          }
          description="Finance looks enormous because it is explained badly. Underneath there are about fourteen ideas, and each one unlocks the next. Rounds you win feed the node they belong to."
          action={
            <div className="tabular text-left sm:text-right">
              <p className="text-2xl font-bold">
                {started}
                <span className="text-faint">/{SKILLS.length}</span>
              </p>
              <p className="label mt-1">started · {mastered} mastered</p>
            </div>
          }
          className="mb-9"
        />

        <div className="grid gap-4 lg:grid-cols-12">
          <Reveal className="lg:col-span-7">
            <div className="piece relative overflow-hidden rounded-3xl p-3 sm:p-5">
              <div className="relative aspect-square w-full">
                {/* Edges */}
                <svg
                  viewBox="0 0 100 100"
                  className="absolute inset-0 h-full w-full"
                  aria-hidden
                >
                  {SKILL_EDGES.map(({ from, to }) => {
                    const a = SKILL_BY_ID.get(from)!;
                    const b = SKILL_BY_ID.get(to)!;
                    const live = (player.mastery[to] ?? 0) > 0;
                    const focused = selected === from || selected === to;

                    return (
                      <line
                        key={`${from}-${to}`}
                        x1={a.x}
                        y1={a.y}
                        x2={b.x}
                        y2={b.y}
                        stroke={focused || live ? BRANCH_TINTS[b.branch] : "#ffffff"}
                        strokeOpacity={focused ? 0.75 : live ? 0.32 : 0.09}
                        strokeWidth={focused ? 0.7 : 0.45}
                        strokeLinecap="round"
                        className="transition-all duration-300"
                      />
                    );
                  })}
                </svg>

                {/* Nodes */}
                {SKILLS.map((node, index) => {
                  const nodeMastery = player.mastery[node.id] ?? 0;
                  const nodeUnlocked = isUnlocked(node, player.mastery);
                  const isSelected = selected === node.id;
                  const tint = BRANCH_TINTS[node.branch];

                  return (
                    <motion.button
                      key={node.id}
                      type="button"
                      onClick={() => setSelected(node.id)}
                      onMouseEnter={() => setSelected(node.id)}
                      onFocus={() => setSelected(node.id)}
                      aria-pressed={isSelected}
                      initial={reduceMotion ? false : { scale: 0, opacity: 0 }}
                      whileInView={{ scale: 1, opacity: 1 }}
                      viewport={{ once: true }}
                      transition={{
                        delay: index * 0.035,
                        type: "spring",
                        stiffness: 320,
                        damping: 20,
                      }}
                      className="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center"
                      style={{ left: `${node.x}%`, top: `${node.y}%` }}
                    >
                      <span
                        className={`relative flex items-center justify-center overflow-hidden rounded-full border-2 transition-all duration-200 ${
                          isSelected ? "scale-110" : "hover:scale-105"
                        }`}
                        style={{
                          width: node.branch === "core" ? 52 : 40,
                          height: node.branch === "core" ? 52 : 40,
                          borderColor: nodeUnlocked ? tint : "rgba(255,255,255,0.16)",
                          backgroundColor: "var(--color-surface)",
                          boxShadow: isSelected ? `0 0 0 6px ${tint}22` : undefined,
                        }}
                      >
                        {/* Mastery fills the node from the bottom. */}
                        <motion.span
                          className="absolute inset-x-0 bottom-0"
                          style={{ backgroundColor: tint, opacity: 0.85 }}
                          initial={{ height: 0 }}
                          whileInView={{ height: `${nodeMastery}%` }}
                          viewport={{ once: true }}
                          transition={
                            reduceMotion
                              ? { duration: 0 }
                              : { duration: 0.9, delay: 0.3 + index * 0.03 }
                          }
                        />
                        <span className="relative">
                          {!nodeUnlocked ? (
                            <Lock size={14} className="text-faint" aria-hidden />
                          ) : nodeMastery >= 100 ? (
                            <Check size={16} className="text-void" strokeWidth={3.5} aria-hidden />
                          ) : null}
                        </span>
                      </span>

                      <span
                        className={`mt-1.5 max-w-[84px] text-center text-[0.625rem] leading-tight font-semibold transition-colors sm:max-w-[104px] sm:text-[0.6875rem] ${
                          isSelected ? "text-fg" : nodeUnlocked ? "text-muted" : "text-faint"
                        } ${isSelected ? "" : "max-sm:hidden"}`}
                        // Labels sit on top of the edges; a dark halo keeps
                        // them readable wherever a line passes behind.
                        style={{ textShadow: "0 1px 4px var(--color-void), 0 0 8px var(--color-void)" }}
                      >
                        {node.label}
                      </span>
                    </motion.button>
                  );
                })}
              </div>

              {/* Branch legend */}
              <ul className="border-line mt-2 flex flex-wrap items-center justify-center gap-x-4 gap-y-2 border-t pt-4">
                {(Object.keys(BRANCH_LABELS) as (keyof typeof BRANCH_LABELS)[]).map((branch) => (
                  <li key={branch} className="flex items-center gap-1.5">
                    <span
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: BRANCH_TINTS[branch] }}
                      aria-hidden
                    />
                    <span className="text-faint text-[0.6875rem]">{BRANCH_LABELS[branch]}</span>
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>

          {/* Detail */}
          <Reveal delay={0.08} className="lg:col-span-5">
            <div className="piece flex h-full flex-col rounded-3xl p-6">
              <span
                className="mb-3 inline-flex w-fit items-center gap-2 rounded-full px-2.5 py-1 text-[0.6875rem] font-bold tracking-wide uppercase"
                style={{
                  color: BRANCH_TINTS[skill.branch],
                  backgroundColor: `${BRANCH_TINTS[skill.branch]}1a`,
                }}
              >
                {BRANCH_LABELS[skill.branch]}
              </span>

              <h3 className="font-display text-2xl font-bold">{skill.label}</h3>
              <p className="text-muted mt-3 text-[0.9375rem] leading-relaxed">{skill.blurb}</p>

              <div className="mt-6">
                <div className="mb-2 flex items-baseline justify-between text-[0.8125rem]">
                  <span className="text-muted">Mastery</span>
                  <span className="tabular font-semibold">{Math.round(mastery)}%</span>
                </div>
                <div
                  className="h-2.5 w-full overflow-hidden rounded-full bg-white/[0.08]"
                  role="progressbar"
                  aria-valuenow={Math.round(mastery)}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`${skill.label} mastery`}
                >
                  <motion.div
                    className="h-full rounded-full"
                    style={{ backgroundColor: BRANCH_TINTS[skill.branch] }}
                    initial={false}
                    animate={{ width: `${mastery}%` }}
                    transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                  />
                </div>
              </div>

              {unlockedAsset && (
                <div className="border-line mt-6 rounded-2xl border bg-black/25 p-4">
                  <p className="label mb-1.5">Unlocks</p>
                  <p className="flex items-center gap-2 text-[0.9375rem] font-semibold">
                    <Sparkles size={15} className="text-xp" aria-hidden />
                    {unlockedAsset.label} in the lab
                  </p>
                  <p className="text-faint mt-1.5 text-[0.8125rem] leading-relaxed">
                    {mastery >= 100
                      ? "Unlocked — you can allocate to it."
                      : `Master this node to allocate to ${unlockedAsset.label.toLowerCase()}.`}
                  </p>
                </div>
              )}

              {!unlocked && (
                <p className="text-faint mt-6 flex items-start gap-2 text-[0.8125rem] leading-relaxed">
                  <Lock size={14} className="mt-0.5 shrink-0" aria-hidden />
                  Locked until you have started{" "}
                  {skill.requires.map((id) => SKILL_BY_ID.get(id)?.label).join(" and ")}.
                </p>
              )}

              {childrenOf(selected).length > 0 && (
                <div className="mt-6">
                  <p className="label mb-2.5">Leads to</p>
                  <ul className="grid gap-1.5">
                    {childrenOf(selected).map((child) => (
                      <li key={child.id}>
                        <button
                          type="button"
                          onClick={() => setSelected(child.id)}
                          className="border-line hover:border-line-strong flex w-full items-center gap-2.5 rounded-xl border bg-black/20 px-3 py-2 text-left transition-colors"
                        >
                          <span
                            className="h-2 w-2 shrink-0 rounded-full"
                            style={{ backgroundColor: BRANCH_TINTS[child.branch] }}
                            aria-hidden
                          />
                          <span className="text-[0.875rem] font-medium">{child.label}</span>
                          <span className="tabular text-faint ml-auto text-[0.75rem]">
                            {Math.round(player.mastery[child.id] ?? 0)}%
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <ButtonLink href="#play" variant="secondary" size="md" className="mt-auto w-full">
                Practise this in a run
              </ButtonLink>
            </div>
          </Reveal>
        </div>
      </Container>
    </section>
  );
}
