"use client";

import { useCallback, useMemo, useSyncExternalStore } from "react";
import { createPersistedStore } from "@/lib/state/persisted-store";
import { STARTING_MASTERY } from "@/lib/game/skills";
import { STARTING_BALANCE } from "@/lib/game/portfolio";
import type { SkillId } from "@/lib/game/types";

/**
 * Everything the player has earned. One store, read by the HUD, the skill map,
 * the league table and the portfolio lab — so finishing a run visibly moves
 * all four at once.
 */
export interface PlayerState {
  xp: number;
  streak: number;
  freezes: number;
  runsCompleted: number;
  bestCombo: number;
  mastery: Partial<Record<SkillId, number>>;
  /** Local date key of the last completed run, so a streak extends once a day. */
  lastRunDay: string;
  allocation: Record<string, number>;
}

/** A returning player, mid-climb — a blank slate would show nothing off. */
const FALLBACK: PlayerState = {
  xp: 3120,
  streak: 12,
  freezes: 2,
  runsCompleted: 23,
  bestCombo: 4,
  mastery: { ...STARTING_MASTERY },
  lastRunDay: "",
  // Only unlocked classes carry weight at the start; the rest are earned.
  allocation: { cash: 25, index: 75, bonds: 0, stocks: 0, gold: 0, crypto: 0 },
};

export function dayKey(date = new Date()): string {
  return `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;
}

const store = createPersistedStore<PlayerState>(
  "edenomics.player.v1",
  FALLBACK,
  (raw) => {
    if (typeof raw !== "object" || raw === null) return null;
    const stored = raw as Partial<PlayerState>;
    return {
      xp: typeof stored.xp === "number" ? stored.xp : FALLBACK.xp,
      streak: typeof stored.streak === "number" ? stored.streak : FALLBACK.streak,
      freezes: typeof stored.freezes === "number" ? stored.freezes : FALLBACK.freezes,
      runsCompleted:
        typeof stored.runsCompleted === "number" ? stored.runsCompleted : FALLBACK.runsCompleted,
      bestCombo: typeof stored.bestCombo === "number" ? stored.bestCombo : FALLBACK.bestCombo,
      mastery:
        typeof stored.mastery === "object" && stored.mastery !== null
          ? (stored.mastery as PlayerState["mastery"])
          : { ...STARTING_MASTERY },
      lastRunDay: typeof stored.lastRunDay === "string" ? stored.lastRunDay : "",
      allocation:
        typeof stored.allocation === "object" && stored.allocation !== null
          ? (stored.allocation as Record<string, number>)
          : { ...FALLBACK.allocation },
    };
  },
);

export interface RunResult {
  xpEarned: number;
  bestCombo: number;
  /** Skills touched by rounds the player got right. */
  skillsHit: SkillId[];
}

export interface PlayerApi extends PlayerState {
  /** True once today's run has been banked. */
  playedToday: boolean;
  balance: number;
  completeRun: (result: RunResult) => void;
  setAllocation: (allocation: Record<string, number>) => void;
  reset: () => void;
}

/*
  Today's date key, read through useSyncExternalStore so the server and the
  hydrating client agree on "" and only the settled client sees a real date.
  Defined at module scope because reading the clock during render is not
  something a component body may do.
*/
const noopSubscribe = () => () => {};
const getToday = () => dayKey();
const getTodayOnServer = () => "";

export function usePlayer(): PlayerApi {
  const state = useSyncExternalStore(
    store.subscribe,
    store.getSnapshot,
    store.getServerSnapshot,
  );
  const today = useSyncExternalStore(noopSubscribe, getToday, getTodayOnServer);

  const completeRun = useCallback((result: RunResult) => {
    store.set((current) => {
      const today = dayKey();
      const firstToday = current.lastRunDay !== today;

      // Mastery climbs fastest early and tapers, so a node never jumps to
      // "mastered" off one lucky answer.
      const mastery = { ...current.mastery };
      for (const skill of result.skillsHit) {
        const now = mastery[skill] ?? 0;
        mastery[skill] = Math.min(100, now + Math.max(12, Math.round((100 - now) * 0.3)));
      }

      return {
        ...current,
        xp: current.xp + result.xpEarned,
        streak: firstToday ? current.streak + 1 : current.streak,
        runsCompleted: firstToday ? current.runsCompleted + 1 : current.runsCompleted,
        bestCombo: Math.max(current.bestCombo, result.bestCombo),
        mastery,
        lastRunDay: today,
      };
    });
  }, []);

  const setAllocation = useCallback((allocation: Record<string, number>) => {
    store.set((current) => ({ ...current, allocation }));
  }, []);

  const reset = useCallback(() => store.set(() => ({ ...FALLBACK })), []);

  return useMemo(
    () => ({
      ...state,
      playedToday: today !== "" && state.lastRunDay === today,
      balance: STARTING_BALANCE,
      completeRun,
      setAllocation,
      reset,
    }),
    [state, today, completeRun, setAllocation, reset],
  );
}
