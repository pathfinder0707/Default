"use client";

import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ChevronRight } from "lucide-react";
import type { FeedUpdate, Topic } from "@/lib/types";
import { Delta } from "@/components/markets/Delta";
import { Monogram } from "@/components/ui/Monogram";
import { timeAgo } from "@/lib/format";

/** One update in the personalised feed. A list row, not a card — deliberately. */
export function FeedItem({ update, topic }: { update: FeedUpdate; topic: Topic }) {
  const [open, setOpen] = useState(false);
  const reduceMotion = useReducedMotion();
  const bodyId = `moved-${update.id}`;

  return (
    <article className="px-5 py-5 sm:px-7 sm:py-6">
      <div className="flex items-start gap-4">
        <Monogram topic={topic} size={38} />

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <h4 className="text-[0.9375rem] font-medium">{topic.label}</h4>
            {typeof update.changePct === "number" && (
              <Delta value={update.changePct} size="md" />
            )}
            <span className="text-faint ml-auto font-mono text-[0.625rem] tracking-wide">
              {timeAgo(update.minutesAgo)}
            </span>
          </div>

          <p className="mt-2 text-[0.9375rem] leading-snug">{update.headline}</p>
          <p className="text-muted mt-1.5 text-[0.8125rem] leading-relaxed">
            {update.detail}
          </p>

          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-controls={bodyId}
            className="text-accent hover:text-fg mt-3 inline-flex items-center gap-1 text-[0.8125rem] transition-colors"
          >
            Why it moved
            <motion.span
              animate={{ rotate: open ? 90 : 0 }}
              transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
              className="inline-flex"
            >
              <ChevronRight size={14} aria-hidden />
            </motion.span>
          </button>

          <AnimatePresence initial={false}>
            {open && (
              <motion.div
                id={bodyId}
                initial={reduceMotion ? undefined : { height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={reduceMotion ? undefined : { height: 0, opacity: 0 }}
                transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
                className="overflow-hidden"
              >
                <p className="border-accent/40 text-muted mt-3 border-l-2 pl-4 text-[0.8125rem] leading-relaxed">
                  {update.whyItMoved}
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </article>
  );
}
