"use client";

import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ArrowRight, Check } from "lucide-react";
import { Container } from "@/components/layout/Section";
import { Reveal } from "@/components/ui/Reveal";
import { Button } from "@/components/ui/Button";
import { TopicChip } from "@/components/watchlist/TopicChip";
import { NotificationPanel } from "@/components/watchlist/NotificationPanel";
import { TOPICS } from "@/lib/data/topics";
import { useWatchlist } from "@/lib/state/watchlist";

export function WatchlistCta() {
  const { followed, isFollowing, toggle } = useWatchlist();
  const [created, setCreated] = useState(false);
  const reduceMotion = useReducedMotion();

  return (
    <section id="watchlist" className="py-14 sm:py-18 lg:py-24">
      <Container>
        <div className="grid gap-5 lg:grid-cols-12 lg:gap-6">
          <Reveal className="lg:col-span-7">
            <div className="border-line bg-elevated flex h-full flex-col rounded-2xl border p-6 sm:p-8">
              <p className="eyebrow mb-3">Your watchlist</p>
              <h2 className="display text-[2.1rem] leading-[1.05] sm:text-[2.6rem]">
                Follow less. Know more.
              </h2>
              <p className="text-muted mt-4 max-w-lg text-[0.9375rem] leading-relaxed">
                Choose the companies, assets and topics you care about. We&rsquo;ll surface
                only the updates that actually touch them — and stay quiet the rest of
                the time.
              </p>

              <div className="mt-7 flex flex-wrap gap-2">
                {TOPICS.map((topic) => (
                  <TopicChip
                    key={topic.id}
                    topic={topic}
                    selected={isFollowing(topic.id)}
                    onToggle={() => {
                      toggle(topic.id);
                      setCreated(false);
                    }}
                  />
                ))}
              </div>

              <div className="border-line mt-8 flex flex-wrap items-center gap-4 border-t pt-6">
                <AnimatePresence mode="wait" initial={false}>
                  {created ? (
                    <motion.div
                      key="done"
                      initial={reduceMotion ? false : { opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={reduceMotion ? undefined : { opacity: 0, y: -8 }}
                      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                      className="flex flex-wrap items-center gap-3"
                    >
                      <span className="text-up bg-up/10 inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[0.8125rem]">
                        <Check size={14} aria-hidden />
                        Feed ready
                      </span>
                      <span className="text-muted text-[0.875rem]">
                        {followed.length} topic{followed.length === 1 ? "" : "s"} · about
                        three updates a day
                      </span>
                      <a
                        href="#for-you"
                        className="text-accent hover:text-fg inline-flex items-center gap-1 text-[0.875rem] transition-colors"
                      >
                        See it
                        <ArrowRight size={14} aria-hidden />
                      </a>
                    </motion.div>
                  ) : (
                    <motion.div
                      key="create"
                      initial={reduceMotion ? false : { opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={reduceMotion ? undefined : { opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="flex flex-wrap items-center gap-4"
                    >
                      <Button
                        size="lg"
                        onClick={() => setCreated(true)}
                        disabled={followed.length === 0}
                      >
                        Create my watchlist
                      </Button>
                      <span className="text-faint tabular text-[0.8125rem]">
                        {followed.length} selected
                      </span>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <p className="text-faint mt-5 text-[0.8125rem] leading-relaxed">
                Change these whenever you like — nothing is locked in, and following
                something from a headline adds it here too.
              </p>
            </div>
          </Reveal>

          <Reveal delay={0.08} className="lg:col-span-5">
            <NotificationPanel />
          </Reveal>
        </div>
      </Container>
    </section>
  );
}
