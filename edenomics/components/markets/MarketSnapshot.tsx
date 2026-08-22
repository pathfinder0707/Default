"use client";

import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Info } from "lucide-react";
import { Container } from "@/components/layout/Section";
import { Reveal } from "@/components/ui/Reveal";
import { AnimatedNumber } from "@/components/ui/AnimatedNumber";
import { Delta } from "@/components/markets/Delta";
import { Sparkline } from "@/components/markets/Sparkline";
import { SNAPSHOT } from "@/lib/data/markets";
import { formatPct } from "@/lib/format";

/**
 * Six numbers, no table.
 *
 * Selecting a line explains what it actually is in one sentence — the
 * beginner's exit ramp — instead of burying a glossary somewhere else.
 */
export function MarketSnapshot() {
  const [selected, setSelected] = useState<string | null>(null);
  const reduceMotion = useReducedMotion();
  const active = SNAPSHOT.find((q) => q.id === selected);

  return (
    <section id="markets" className="py-12 sm:py-14 lg:py-16">
      <Container>
        <Reveal
          as="header"
          className="mb-6 flex flex-wrap items-end justify-between gap-4"
        >
          <div>
            <p className="eyebrow mb-3">Markets at a glance</p>
            <h2 className="display text-[1.75rem] leading-tight sm:text-[2.1rem]">
              The whole board, in six lines.
            </h2>
          </div>
          <p className="text-faint hidden max-w-xs text-right text-[0.8125rem] leading-relaxed sm:block">
            Select any line to see what it actually measures.
          </p>
        </Reveal>

        <Reveal>
          <div className="border-line bg-surface overflow-hidden rounded-2xl border">
            <div className="rail flex overflow-x-auto lg:grid lg:grid-cols-6 lg:overflow-visible">
              {SNAPSHOT.map((quote) => {
                const isActive = selected === quote.id;
                return (
                  <button
                    key={quote.id}
                    type="button"
                    onClick={() => setSelected(isActive ? null : quote.id)}
                    aria-pressed={isActive}
                    className={`border-line relative w-[46vw] shrink-0 border-r px-4 py-4 text-left transition-colors duration-200 last:border-r-0 sm:w-[32vw] sm:px-5 lg:w-auto ${
                      isActive ? "bg-white/[0.05]" : "hover:bg-white/[0.03]"
                    }`}
                  >
                    {isActive && (
                      <motion.span
                        layoutId={reduceMotion ? undefined : "market-underline"}
                        className="bg-accent absolute inset-x-0 top-0 h-px"
                        transition={{ type: "spring", stiffness: 400, damping: 34 }}
                      />
                    )}
                    <span className="text-muted block text-[0.75rem]">{quote.label}</span>
                    <AnimatedNumber
                      display={quote.display}
                      className="tabular mt-2 block text-[1.15rem] leading-none"
                    />
                    <span className="mt-2 flex items-end justify-between gap-2">
                      <Delta value={quote.changePct} size="sm" />
                      <Sparkline
                        values={quote.spark}
                        positive={quote.changePct >= 0}
                        width={52}
                        height={20}
                        strokeWidth={1.3}
                        label={`${quote.label} today, ${formatPct(quote.changePct)}`}
                      />
                    </span>
                  </button>
                );
              })}
            </div>

            <AnimatePresence initial={false}>
              {active && (
                <motion.div
                  key={active.id}
                  initial={reduceMotion ? undefined : { height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={reduceMotion ? undefined : { height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                  className="border-line overflow-hidden border-t"
                >
                  <p className="text-muted flex items-start gap-2.5 px-5 py-4 text-[0.875rem] leading-relaxed">
                    <Info size={15} className="text-accent mt-px shrink-0" aria-hidden />
                    <span>
                      <span className="text-fg">{active.label}</span> — {active.blurb}
                    </span>
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </Reveal>

        <p className="text-faint mt-4 text-[0.8125rem] sm:hidden">
          Scroll sideways for the rest. Tap a line to see what it measures.
        </p>
      </Container>
    </section>
  );
}
