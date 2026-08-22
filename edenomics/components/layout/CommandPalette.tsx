"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { CornerDownLeft, Search, TrendingUp } from "lucide-react";
import { TOPICS } from "@/lib/data/topics";
import { STORIES } from "@/lib/data/stories";
import { useWatchlist } from "@/lib/state/watchlist";
import { Monogram } from "@/components/ui/Monogram";

type Result =
  | { kind: "topic"; id: string; label: string; hint: string }
  | { kind: "story"; id: string; label: string; hint: string };

/**
 * Search, done as a command palette rather than a search page.
 *
 * Choosing a topic follows it — which immediately changes the personalised
 * feed — and choosing a story jumps to it in the brief. Search that does
 * something is worth more than a box that files a query.
 */
export function CommandPalette({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const { follow, isFollowing } = useWatchlist();
  const reduceMotion = useReducedMotion();

  const results = useMemo<Result[]>(() => {
    const q = query.trim().toLowerCase();

    const topics: Result[] = TOPICS.filter(
      (t) =>
        !q ||
        t.label.toLowerCase().includes(q) ||
        t.symbol?.toLowerCase().includes(q) ||
        t.blurb.toLowerCase().includes(q),
    )
      .slice(0, q ? 6 : 5)
      .map((t) => ({
        kind: "topic" as const,
        id: t.id,
        label: t.label,
        hint: isFollowing(t.id) ? "Following" : "Follow",
      }));

    const stories: Result[] = STORIES.filter(
      (s) =>
        !q ||
        s.headline.toLowerCase().includes(q) ||
        s.summary.toLowerCase().includes(q) ||
        s.category.toLowerCase().includes(q),
    )
      .slice(0, q ? 4 : 3)
      .map((s) => ({
        kind: "story" as const,
        id: s.id,
        label: s.headline,
        hint: s.category,
      }));

    return [...topics, ...stories];
  }, [query, isFollowing]);

  // Clamp rather than resetting in an effect: the result list shrinks as the
  // query narrows, and the highlight should simply follow it.
  const activeIndex = results.length ? Math.min(cursor, results.length - 1) : 0;

  const close = useCallback(() => {
    setQuery("");
    setCursor(0);
    onClose();
  }, [onClose]);

  useEffect(() => {
    if (!open) return;
    // Wait a frame so the element exists before focusing it. Selecting the
    // text means a reopen with a stale query is overwritten by typing.
    const id = requestAnimationFrame(() => {
      inputRef.current?.focus();
      inputRef.current?.select();
    });
    return () => cancelAnimationFrame(id);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  function select(result: Result) {
    close();
    if (result.kind === "topic") {
      follow(result.id);
      document.getElementById("watchlist")?.scrollIntoView({ block: "start" });
      return;
    }
    document.getElementById(`story-${result.id}`)?.scrollIntoView({ block: "center" });
  }

  function onKeyDown(event: React.KeyboardEvent) {
    if (event.key === "Escape") {
      event.preventDefault();
      close();
      return;
    }
    if (event.key === "ArrowDown" || (event.key === "n" && event.ctrlKey)) {
      event.preventDefault();
      setCursor((c) => (results.length ? (c + 1) % results.length : 0));
      return;
    }
    if (event.key === "ArrowUp" || (event.key === "p" && event.ctrlKey)) {
      event.preventDefault();
      setCursor((c) => (results.length ? (c - 1 + results.length) % results.length : 0));
      return;
    }
    if (event.key === "Enter" && results[activeIndex]) {
      event.preventDefault();
      select(results[activeIndex]);
    }
  }

  // Keep the highlighted row in view when arrowing through a long list.
  useEffect(() => {
    listRef.current
      ?.querySelector<HTMLElement>(`[data-index="${activeIndex}"]`)
      ?.scrollIntoView({ block: "nearest" });
  }, [activeIndex]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[60] flex items-start justify-center px-4 pt-[12vh] sm:pt-[16vh]"
          initial={reduceMotion ? undefined : { opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={reduceMotion ? undefined : { opacity: 0 }}
          transition={{ duration: 0.16 }}
        >
          <button
            type="button"
            aria-label="Close search"
            onClick={close}
            className="absolute inset-0 cursor-default bg-black/70 backdrop-blur-sm"
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-label="Search Edenomics"
            onKeyDown={onKeyDown}
            initial={reduceMotion ? undefined : { opacity: 0, y: -8, scale: 0.985 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={reduceMotion ? undefined : { opacity: 0, y: -8, scale: 0.985 }}
            transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
            className="border-line-strong bg-elevated relative w-full max-w-xl overflow-hidden rounded-2xl border shadow-[0_32px_80px_-20px_rgba(0,0,0,0.85)]"
          >
            {/* Focus lives on the row rather than the bare input, so the
                indicator reads as part of the design instead of an outline
                dropped on top of it. */}
            <div className="border-line focus-within:ring-accent/70 flex items-center gap-3 border-b px-4 focus-within:ring-1 focus-within:ring-inset">
              <Search size={16} className="text-faint shrink-0" aria-hidden />
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setCursor(0);
                }}
                placeholder="Search companies, topics or today's stories"
                aria-label="Search companies, topics or today's stories"
                className="placeholder:text-faint h-14 w-full bg-transparent text-[0.9375rem] outline-none focus-visible:outline-none"
              />
              <kbd className="text-faint border-line hidden rounded border px-1.5 py-0.5 font-mono text-[0.625rem] sm:block">
                ESC
              </kbd>
            </div>

            <div ref={listRef} className="max-h-[52vh] overflow-y-auto p-2">
              {results.length === 0 && (
                <p className="text-muted px-3 py-8 text-center text-sm">
                  Nothing matches “{query}”. Try a company, a ticker or a theme.
                </p>
              )}
              {results.map((result, index) => (
                <button
                  key={`${result.kind}-${result.id}`}
                  data-index={index}
                  type="button"
                  onMouseMove={() => setCursor(index)}
                  onClick={() => select(result)}
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors ${
                    index === activeIndex ? "bg-white/[0.07]" : "hover:bg-white/[0.04]"
                  }`}
                >
                  {result.kind === "topic" ? (
                    <Monogram
                      topic={TOPICS.find((t) => t.id === result.id)!}
                      size={30}
                    />
                  ) : (
                    <span className="bg-raised text-faint inline-flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-[10px]">
                      <TrendingUp size={14} aria-hidden />
                    </span>
                  )}
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm">{result.label}</span>
                    <span className="text-faint block text-xs">
                      {result.kind === "topic" ? "Topic" : "Today's brief"} · {result.hint}
                    </span>
                  </span>
                  {index === activeIndex && (
                    <CornerDownLeft size={13} className="text-faint shrink-0" aria-hidden />
                  )}
                </button>
              ))}
            </div>

            <div className="border-line text-faint flex items-center justify-between border-t px-4 py-2.5 text-[0.6875rem]">
              <span>↑↓ to move · ↵ to open</span>
              <span>Following a topic updates your feed</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
