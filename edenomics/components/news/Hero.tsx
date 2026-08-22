"use client";

import { motion, useReducedMotion } from "motion/react";
import { ArrowRight } from "lucide-react";
import { Container } from "@/components/layout/Section";
import { ButtonLink } from "@/components/ui/Button";
import { Delta } from "@/components/markets/Delta";
import { STORIES, totalReadTime } from "@/lib/data/stories";
import { EXCHANGES } from "@/lib/data/exchanges";
import { sessionStatus, longDate } from "@/lib/market-clock";
import { useMounted } from "@/lib/hooks/useMounted";
import { timeAgo } from "@/lib/format";

/**
 * Deliberately not a SaaS hero. There is no product mockup and no promise —
 * the panel on the right is the actual brief, so the value is legible before
 * anyone scrolls or signs up.
 */
export function Hero() {
  const mounted = useMounted();
  const reduceMotion = useReducedMotion();

  const mumbai = EXCHANGES.find((e) => e.id === "mumbai")!;
  const newYork = EXCHANGES.find((e) => e.id === "new-york")!;

  const lead = STORIES[0];

  function jumpToStory(id: string) {
    document.getElementById(`story-${id}`)?.scrollIntoView({ block: "center" });
  }

  return (
    <section id="top" className="grain relative overflow-hidden pt-28 pb-14 sm:pt-32 lg:pt-36 lg:pb-16">
      {/* One soft light source, top right. No stacked gradients. */}
      <div
        aria-hidden
        className="pointer-events-none absolute -top-40 right-[-10%] h-[520px] w-[720px] rounded-full opacity-[0.16] blur-[120px]"
        style={{
          background:
            "radial-gradient(closest-side, var(--color-accent), transparent 70%)",
        }}
      />

      <Container className="relative">
        <div className="grid items-start gap-12 lg:grid-cols-12 lg:gap-10 xl:gap-16">
          <div className="lg:col-span-7">
            <div className="mb-7 flex min-h-5 items-center gap-3 text-[0.6875rem]">
              {mounted ? (
                <motion.div
                  initial={reduceMotion ? false : { opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.4 }}
                  className="flex flex-wrap items-center gap-x-3 gap-y-1 font-mono tracking-wide"
                >
                  <span className="text-muted">{longDate()}</span>
                  <span className="bg-line h-3 w-px" aria-hidden />
                  <SessionPip label={mumbai.city} status={sessionStatus(mumbai).label} />
                  <span className="bg-line h-3 w-px max-sm:hidden" aria-hidden />
                  <SessionPip
                    label={newYork.city}
                    status={sessionStatus(newYork).label}
                    className="max-sm:hidden"
                  />
                </motion.div>
              ) : (
                <span className="skeleton h-3 w-64 rounded" />
              )}
            </div>

            <h1 className="display text-[2.85rem] leading-[1.02] sm:text-[4rem] lg:text-[4.6rem]">
              Know what <em className="text-accent not-italic">matters</em>
              <br />
              in money.
            </h1>

            <p className="text-muted mt-6 max-w-[46ch] text-[1.0625rem] leading-relaxed sm:text-lg">
              Markets, companies and financial news — distilled into a few minutes a day.
              No tickers you don&rsquo;t follow, no tables you won&rsquo;t read.
            </p>

            <div className="mt-9 flex flex-wrap items-center gap-3">
              <ButtonLink href="#today" size="lg">
                See today&rsquo;s brief
                <ArrowRight size={16} aria-hidden />
              </ButtonLink>
              <ButtonLink href="#watchlist" size="lg" variant="secondary">
                Build my watchlist
              </ButtonLink>
            </div>

            <p className="text-faint mt-8 font-mono text-[0.6875rem] tracking-wide">
              {STORIES.length} stories · {totalReadTime()} · updated {timeAgo(lead.minutesAgo)}
            </p>
          </div>

          {/*
            The brief itself, as a contents page. Hidden on phones, where the
            swipeable brief sits directly below and says the same thing.
          */}
          <motion.div
            initial={reduceMotion ? false : { opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="max-md:hidden lg:col-span-5"
          >
            <div className="border-line bg-elevated/70 rounded-2xl border backdrop-blur-sm">
              <div className="border-line flex items-baseline justify-between border-b px-5 py-4">
                <h2 className="text-[0.9375rem] font-medium">Today&rsquo;s brief</h2>
                <span className="text-faint font-mono text-[0.6875rem]">
                  {totalReadTime()}
                </span>
              </div>

              <ol className="p-2">
                {STORIES.map((story, index) => (
                  <motion.li
                    key={story.id}
                    initial={reduceMotion ? false : { opacity: 0, x: -6 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{
                      duration: 0.45,
                      delay: 0.25 + index * 0.06,
                      ease: [0.22, 1, 0.36, 1],
                    }}
                  >
                    <button
                      type="button"
                      onClick={() => jumpToStory(story.id)}
                      className="group flex w-full items-start gap-3.5 rounded-xl px-3 py-3 text-left transition-colors duration-200 hover:bg-white/[0.04]"
                    >
                      <span className="text-faint group-hover:text-accent mt-px font-mono text-[0.6875rem] tabular-nums transition-colors">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block text-[0.875rem] leading-snug">
                          {story.headline}
                        </span>
                        <span className="text-faint mt-1 block font-mono text-[0.625rem] tracking-wide uppercase">
                          {story.category}
                        </span>
                      </span>
                      {story.assets[0] && (
                        <Delta
                          value={story.assets[0].changePct}
                          size="sm"
                          showIcon={false}
                          className="mt-px"
                        />
                      )}
                    </button>
                  </motion.li>
                ))}
              </ol>

              <div className="border-line border-t px-5 py-3.5">
                <p className="text-faint font-serif text-[0.9375rem] italic">
                  Everything else can wait.
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </Container>
    </section>
  );
}

function SessionPip({
  label,
  status,
  className = "",
}: {
  label: string;
  status: string;
  className?: string;
}) {
  const isOpen = status.startsWith("Open");
  return (
    <span className={`text-faint flex items-center gap-1.5 ${className}`}>
      <span
        aria-hidden
        className={`h-1.5 w-1.5 rounded-full ${isOpen ? "bg-up" : "bg-faint"}`}
      />
      {label} · {status}
    </span>
  );
}
