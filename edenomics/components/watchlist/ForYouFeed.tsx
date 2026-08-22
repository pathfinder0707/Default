"use client";

import { motion, AnimatePresence } from "motion/react";
import { Plus, SlidersHorizontal } from "lucide-react";
import { Container, SectionHeading } from "@/components/layout/Section";
import { FeedItem } from "@/components/watchlist/FeedItem";
import { Monogram } from "@/components/ui/Monogram";
import { Delta } from "@/components/markets/Delta";
import { Sparkline } from "@/components/markets/Sparkline";
import { ButtonLink } from "@/components/ui/Button";
import { TOPIC_BY_ID } from "@/lib/data/topics";
import { TOPIC_QUOTES } from "@/lib/data/markets";
import { updatesForTopics } from "@/lib/data/feed";
import { useWatchlist } from "@/lib/state/watchlist";

/**
 * The counterpart to the brief: same day, but filtered to what this person
 * actually follows. The visual language shifts from editorial cards to an
 * app-like list so the two sections are never mistaken for each other.
 */
export function ForYouFeed() {
  const { followed } = useWatchlist();
  const topics = followed.map((id) => TOPIC_BY_ID.get(id)).filter((t) => t !== undefined);
  const updates = updatesForTopics(followed, 4);

  return (
    <section id="for-you" className="py-14 sm:py-18 lg:py-24">
      <Container>
        <SectionHeading
          eyebrow="Happening in your world"
          title={
            <>
              Your market.
              <br />
              <span className="text-muted">Not everyone&rsquo;s market.</span>
            </>
          }
          description="The brief is what moved money. This is what moved yours — the same day, filtered down to the companies, assets and ideas you follow."
          action={
            <ButtonLink href="#watchlist" variant="secondary" size="sm">
              <SlidersHorizontal size={14} aria-hidden />
              Following {topics.length}
            </ButtonLink>
          }
          className="mb-10"
        />

        <div className="border-line bg-surface overflow-hidden rounded-3xl border lg:grid lg:grid-cols-12">
          {/* Followed instruments */}
          <aside className="border-line flex flex-col border-b lg:col-span-4 lg:border-r lg:border-b-0">
            <div className="border-line flex items-center justify-between border-b px-5 py-3.5 sm:px-7">
              <h3 className="eyebrow">Your watchlist</h3>
              <a
                href="#watchlist"
                className="text-faint hover:text-fg inline-flex items-center gap-1 text-[0.6875rem] transition-colors"
              >
                <Plus size={12} aria-hidden />
                Add
              </a>
            </div>

            <ul className="rail flex gap-2 overflow-x-auto px-5 py-4 sm:px-7 lg:block lg:flex-1 lg:space-y-1 lg:gap-0 lg:px-3 lg:py-3">
              <AnimatePresence initial={false}>
                {topics.map((topic) => {
                  const quote = TOPIC_QUOTES[topic.id];
                  return (
                    <motion.li
                      key={topic.id}
                      layout
                      initial={{ opacity: 0, scale: 0.96 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.96 }}
                      transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
                      className="shrink-0 lg:shrink"
                    >
                      <div className="flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors hover:bg-white/[0.03]">
                        <Monogram topic={topic} size={34} />
                        <div className="min-w-0 lg:flex-1">
                          <p className="truncate text-[0.8125rem]">{topic.label}</p>
                          <p className="text-faint tabular text-[0.6875rem]">
                            {quote ? quote.display : topic.kind}
                          </p>
                        </div>
                        {quote && (
                          <div className="ml-2 hidden items-center gap-3 lg:flex">
                            <Sparkline
                              values={quote.spark}
                              positive={quote.changePct >= 0}
                              width={44}
                              height={20}
                              strokeWidth={1.3}
                            />
                            <Delta value={quote.changePct} size="sm" showIcon={false} />
                          </div>
                        )}
                      </div>
                    </motion.li>
                  );
                })}
              </AnimatePresence>

              {topics.length === 0 && (
                <li className="text-muted px-3 py-6 text-sm">
                  Nothing followed yet.{" "}
                  <a href="#watchlist" className="text-accent underline-offset-4 hover:underline">
                    Pick a few topics
                  </a>{" "}
                  and this fills up.
                </li>
              )}

              <li className="shrink-0 lg:shrink">
                <a
                  href="#watchlist"
                  className="border-line text-faint hover:border-line-strong hover:text-fg flex h-full items-center gap-3 rounded-xl border border-dashed px-3 py-2.5 text-[0.8125rem] transition-colors"
                >
                  <span className="flex h-[34px] w-[34px] items-center justify-center rounded-[10px] border border-dashed border-current/40">
                    <Plus size={14} aria-hidden />
                  </span>
                  Add a topic
                </a>
              </li>
            </ul>

            <p className="text-faint border-line mt-auto hidden border-t px-5 py-4 text-[0.75rem] leading-relaxed lg:block">
              You&rsquo;ll hear when these move. You don&rsquo;t need to check.
            </p>
          </aside>

          {/* Updates for those instruments */}
          <div className="lg:col-span-8">
            {updates.length > 0 ? (
              <div className="divide-line divide-y">
                <AnimatePresence initial={false} mode="popLayout">
                  {updates.map((update) => {
                    const topic = TOPIC_BY_ID.get(update.topicId);
                    if (!topic) return null;
                    return (
                      <motion.div
                        key={update.id}
                        layout
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -8 }}
                        transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
                      >
                        <FeedItem update={update} topic={topic} />
                      </motion.div>
                    );
                  })}
                </AnimatePresence>
              </div>
            ) : (
              <div className="flex min-h-[280px] flex-col items-center justify-center gap-4 px-8 py-16 text-center">
                <p className="font-serif text-xl">Your feed is empty — for now.</p>
                <p className="text-muted max-w-sm text-sm leading-relaxed">
                  Follow a company, a commodity or an idea and Edenomics will start
                  filtering the day down to what actually touches it.
                </p>
                <ButtonLink href="#watchlist" size="sm">
                  Choose topics
                </ButtonLink>
              </div>
            )}

            {updates.length > 0 && (
              <div className="border-line text-faint flex items-center justify-between border-t px-5 py-3.5 font-mono text-[0.6875rem] tracking-wide sm:px-7">
                <span>
                  {updates.length} update{updates.length === 1 ? "" : "s"} worth your time
                </span>
                <span className="hidden sm:block">
                  Quiet days stay quiet — we don&rsquo;t invent news
                </span>
              </div>
            )}
          </div>
        </div>
      </Container>
    </section>
  );
}
