"use client";

import { useCallback, useMemo, useSyncExternalStore } from "react";
import { DEFAULT_FOLLOWED } from "@/lib/data/topics";
import { createPersistedStore } from "@/lib/state/persisted-store";

const store = createPersistedStore<string[]>(
  "edenomics.watchlist.v1",
  DEFAULT_FOLLOWED,
  (raw) =>
    Array.isArray(raw) && raw.every((v) => typeof v === "string")
      ? (raw as string[])
      : null,
);

export interface WatchlistApi {
  followed: string[];
  isFollowing: (topicId: string) => boolean;
  toggle: (topicId: string) => void;
  follow: (topicId: string) => void;
  reset: () => void;
}

/**
 * What the visitor follows. Read from anywhere on the page — the story cards,
 * the personalised feed and the chip picker all write to the same store, so
 * following a company from a headline immediately changes the feed above it.
 */
export function useWatchlist(): WatchlistApi {
  const followed = useSyncExternalStore(
    store.subscribe,
    store.getSnapshot,
    store.getServerSnapshot,
  );

  const toggle = useCallback((topicId: string) => {
    store.set((current) =>
      current.includes(topicId)
        ? current.filter((id) => id !== topicId)
        : [...current, topicId],
    );
  }, []);

  const follow = useCallback((topicId: string) => {
    store.set((current) => (current.includes(topicId) ? current : [...current, topicId]));
  }, []);

  const reset = useCallback(() => store.set(() => DEFAULT_FOLLOWED), []);

  return useMemo(
    () => ({
      followed,
      isFollowing: (topicId: string) => followed.includes(topicId),
      toggle,
      follow,
      reset,
    }),
    [followed, toggle, follow, reset],
  );
}
