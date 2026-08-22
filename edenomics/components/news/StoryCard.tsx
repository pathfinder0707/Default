"use client";

import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Check, ChevronDown, Heart, Share2 } from "lucide-react";
import type { Story } from "@/lib/types";
import { readTime, timeAgo } from "@/lib/format";
import { Delta } from "@/components/markets/Delta";
import { Sparkline } from "@/components/markets/Sparkline";
import { useWatchlist } from "@/lib/state/watchlist";

const sentimentTone = {
  bullish: { label: "Bullish", dot: "bg-up" },
  bearish: { label: "Bearish", dot: "bg-down" },
  mixed: { label: "Mixed", dot: "bg-accent" },
} as const;

/**
 * The unit the whole brief is built from.
 *
 * Everything above the fold of the card answers "what happened"; "Why it
 * matters" holds the context a beginner needs and stays folded away for
 * everyone who already knows. That is the progressive-disclosure contract.
 */
export function StoryCard({
  story,
  variant = "standard",
  className = "",
}: {
  story: Story;
  variant?: "lead" | "standard";
  className?: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const [shared, setShared] = useState(false);
  const { isFollowing, toggle } = useWatchlist();
  const reduceMotion = useReducedMotion();

  const isLead = variant === "lead";
  const primary = story.assets[0];
  const following = primary ? isFollowing(primary.topicId) : false;
  const tone = sentimentTone[story.sentiment];
  const bodyId = `why-${story.id}`;

  async function share() {
    const url =
      typeof window === "undefined"
        ? ""
        : `${window.location.origin}${window.location.pathname}#story-${story.id}`;
    try {
      if (navigator.share) {
        await navigator.share({ title: story.headline, text: story.summary, url });
        return;
      }
      await navigator.clipboard.writeText(url);
      setShared(true);
      window.setTimeout(() => setShared(false), 1800);
    } catch {
      // The user dismissed the share sheet, or the clipboard was blocked.
    }
  }

  return (
    <motion.article
      id={`story-${story.id}`}
      whileHover={reduceMotion ? undefined : { y: -3 }}
      transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
      className={`group border-line bg-elevated/60 hover:border-line-strong flex scroll-mt-28 flex-col rounded-2xl border transition-colors duration-300 hover:bg-elevated ${
        isLead ? "p-6 sm:p-8" : "p-5 sm:p-6"
      } ${className}`}
    >
      <div className="mb-4 flex items-center gap-3">
        <span className="text-faint font-mono text-[0.625rem] tracking-[0.12em] uppercase">
          {story.category}
        </span>
        <span className="bg-line h-3 w-px" aria-hidden />
        <span className="text-faint font-mono text-[0.625rem] tracking-wide">
          {readTime(story.readSeconds)}
        </span>
        <span className="ml-auto flex items-center gap-1.5">
          <span className={`h-1.5 w-1.5 rounded-full ${tone.dot}`} aria-hidden />
          <span className="text-faint font-mono text-[0.625rem] tracking-[0.12em] uppercase">
            {tone.label}
          </span>
        </span>
      </div>

      {isLead ? (
        <h3 className="display text-[1.9rem] leading-[1.08] sm:text-[2.4rem]">
          {story.headline}
        </h3>
      ) : (
        <h3 className="text-[1.0625rem] leading-snug font-medium sm:text-[1.125rem]">
          {story.headline}
        </h3>
      )}

      <p
        className={`text-muted mt-3 leading-relaxed ${
          isLead ? "max-w-[58ch] text-[1rem]" : "text-[0.875rem]"
        }`}
      >
        {story.summary}
      </p>

      {isLead && story.chart && (
        <div className="border-line mt-6 flex min-h-[110px] flex-1 items-stretch rounded-xl border bg-black/20 p-4">
          <Sparkline
            values={story.chart}
            positive={primary ? primary.changePct >= 0 : true}
            width={560}
            height={92}
            strokeWidth={2}
            area
            stretch
            label={`${primary?.symbol ?? story.category} intraday price, ending ${
              primary ? `${primary.changePct}%` : "flat"
            } on the day`}
            className="h-full min-h-[80px] w-full"
          />
        </div>
      )}

      <div className="mt-5 flex flex-wrap items-center gap-2">
        {story.assets.map((asset) => (
          <span
            key={asset.symbol}
            className="border-line bg-raised inline-flex items-center gap-2 rounded-lg border px-2.5 py-1.5"
          >
            <span className="tabular text-fg text-[0.75rem]">{asset.symbol}</span>
            <Delta value={asset.changePct} size="sm" showIcon={false} />
          </span>
        ))}
      </div>

      <div className="mt-auto pt-5">
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
          aria-controls={bodyId}
          className="text-accent hover:text-fg inline-flex items-center gap-1.5 text-[0.8125rem] transition-colors"
        >
          Why it matters
          <motion.span
            animate={{ rotate: expanded ? 180 : 0 }}
            transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
            className="inline-flex"
          >
            <ChevronDown size={14} aria-hidden />
          </motion.span>
        </button>

        <AnimatePresence initial={false}>
          {expanded && (
            <motion.div
              id={bodyId}
              key="why"
              initial={reduceMotion ? undefined : { height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={reduceMotion ? undefined : { height: 0, opacity: 0 }}
              transition={{ duration: 0.34, ease: [0.22, 1, 0.36, 1] }}
              className="overflow-hidden"
            >
              <p className="border-accent/40 text-muted mt-4 border-l-2 pl-4 text-[0.875rem] leading-relaxed">
                {story.whyItMatters}
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="border-line mt-5 flex items-center gap-1 border-t pt-4">
          {primary && (
            <button
              type="button"
              onClick={() => toggle(primary.topicId)}
              aria-pressed={following}
              className={`inline-flex h-8 items-center gap-1.5 rounded-full px-2.5 text-[0.75rem] transition-colors ${
                following
                  ? "text-accent bg-accent/10"
                  : "text-muted hover:text-fg hover:bg-white/[0.05]"
              }`}
            >
              <Heart
                size={13}
                aria-hidden
                fill={following ? "currentColor" : "none"}
                strokeWidth={1.9}
              />
              {following ? "Following" : "Follow"}
            </button>
          )}

          <button
            type="button"
            onClick={share}
            className="text-muted hover:text-fg inline-flex h-8 items-center gap-1.5 rounded-full px-2.5 text-[0.75rem] transition-colors hover:bg-white/[0.05]"
          >
            {shared ? <Check size={13} aria-hidden /> : <Share2 size={13} aria-hidden />}
            {shared ? "Link copied" : "Share"}
          </button>

          <span className="text-faint ml-auto font-mono text-[0.625rem] tracking-wide">
            {story.source} · {timeAgo(story.minutesAgo)}
          </span>
        </div>
      </div>
    </motion.article>
  );
}
