import type { Topic } from "@/lib/types";
import { topicMonogram } from "@/lib/data/topics";

/**
 * A ticker badge stands in for a company logo. Tint is keyed to the kind of
 * thing being followed, which gives the feed a quiet visual taxonomy without
 * needing icons for sixteen different topics.
 */
const tints: Record<Topic["kind"], string> = {
  stock: "bg-[#1d2230] text-[#a9b6d6]",
  index: "bg-[#22201a] text-[#d4bd8a]",
  region: "bg-[#22201a] text-[#d4bd8a]",
  crypto: "bg-[#2a2118] text-[#e0ab72]",
  commodity: "bg-[#26221a] text-[#d8c68d]",
  sector: "bg-[#1a2426] text-[#93bfc4]",
  theme: "bg-[#231d2b] text-[#bda7d6]",
  macro: "bg-[#1e2422] text-[#9dc4b3]",
};

export function Monogram({
  topic,
  size = 36,
  className = "",
}: {
  topic: Topic;
  size?: number;
  className?: string;
}) {
  return (
    <span
      aria-hidden
      style={{ width: size, height: size, fontSize: size * 0.33 }}
      className={`inline-flex shrink-0 items-center justify-center rounded-[10px] font-mono font-medium tracking-tight ring-1 ring-white/[0.06] ${tints[topic.kind]} ${className}`}
    >
      {topicMonogram(topic)}
    </span>
  );
}
