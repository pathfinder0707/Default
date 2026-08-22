"use client";

import { useCallback, useMemo, useSyncExternalStore } from "react";
import { createPersistedStore } from "@/lib/state/persisted-store";

/** Where a returning player starts, so the demo shows a real streak. */
const BASE_XP = 340;
const BASE_STREAK = 7;

export interface ProgressState {
  xp: number;
  streak: number;
  /** Challenge ids answered today. */
  solved: string[];
  /** XP earned today, for the "+45 XP today" line. */
  earnedToday: number;
  /** Local date key — a change means a new day and today's run resets. */
  day: string;
}

const FALLBACK: ProgressState = {
  xp: BASE_XP,
  streak: BASE_STREAK,
  solved: [],
  earnedToday: 0,
  day: "",
};

function dayKey(date = new Date()): string {
  return `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;
}

const store = createPersistedStore<ProgressState>(
  "edenomics.progress.v2",
  FALLBACK,
  (raw) => {
    if (typeof raw !== "object" || raw === null) return null;
    const stored = raw as Partial<ProgressState>;
    const today = dayKey();
    const carried: ProgressState = {
      xp: typeof stored.xp === "number" ? stored.xp : BASE_XP,
      streak: typeof stored.streak === "number" ? stored.streak : BASE_STREAK,
      solved: Array.isArray(stored.solved) ? stored.solved : [],
      earnedToday: typeof stored.earnedToday === "number" ? stored.earnedToday : 0,
      day: typeof stored.day === "string" ? stored.day : today,
    };
    // A new day means a fresh run: today's questions unlock again.
    return carried.day === today
      ? carried
      : { ...carried, solved: [], earnedToday: 0, day: today };
  },
);

export interface ProgressApi extends ProgressState {
  /** True once today's first answer has extended the streak. */
  streakExtended: boolean;
  award: (challengeId: string, xp: number) => void;
}

export function useProgress(): ProgressApi {
  const state = useSyncExternalStore(
    store.subscribe,
    store.getSnapshot,
    store.getServerSnapshot,
  );

  const award = useCallback((challengeId: string, xp: number) => {
    store.set((current) => {
      if (current.solved.includes(challengeId)) return current;
      const firstOfTheDay = current.solved.length === 0;
      return {
        ...current,
        xp: current.xp + xp,
        // The streak extends once per day, on the first answer — not per question.
        streak: firstOfTheDay ? current.streak + 1 : current.streak,
        solved: [...current.solved, challengeId],
        earnedToday: current.earnedToday + xp,
        day: current.day || dayKey(),
      };
    });
  }, []);

  return useMemo(
    () => ({ ...state, streakExtended: state.solved.length > 0, award }),
    [state, award],
  );
}
