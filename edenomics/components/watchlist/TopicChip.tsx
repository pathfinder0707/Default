"use client";

import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Check, Plus } from "lucide-react";
import type { Topic } from "@/lib/types";

export function TopicChip({
  topic,
  selected,
  onToggle,
}: {
  topic: Topic;
  selected: boolean;
  onToggle: () => void;
}) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.button
      type="button"
      onClick={onToggle}
      aria-pressed={selected}
      title={topic.blurb}
      whileTap={reduceMotion ? undefined : { scale: 0.96 }}
      transition={{ duration: 0.18 }}
      className={`inline-flex items-center gap-1.5 rounded-full border py-2 pr-3.5 pl-3 text-[0.8125rem] transition-colors duration-200 ${
        selected
          ? "border-accent/60 bg-accent/[0.12] text-accent"
          : "border-line text-muted hover:border-line-strong hover:text-fg hover:bg-white/[0.04]"
      }`}
    >
      <AnimatePresence mode="wait" initial={false}>
        <motion.span
          key={selected ? "on" : "off"}
          initial={reduceMotion ? false : { opacity: 0, rotate: -90, scale: 0.6 }}
          animate={{ opacity: 1, rotate: 0, scale: 1 }}
          exit={reduceMotion ? undefined : { opacity: 0, scale: 0.6 }}
          transition={{ duration: 0.18 }}
          className="inline-flex"
        >
          {selected ? <Check size={13} aria-hidden /> : <Plus size={13} aria-hidden />}
        </motion.span>
      </AnimatePresence>
      {topic.label}
    </motion.button>
  );
}
