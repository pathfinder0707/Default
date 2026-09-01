"use client";

import { useCallback, useMemo, useSyncExternalStore } from "react";
import { createPersistedStore } from "@/lib/state/persisted-store";
import type { Answer } from "@/lib/game/scoring";
import type { ConceptId } from "@/lib/game/concepts";

/**
 * The record. Every call ever made is kept, because the calibration curve is
 * the product and it only means anything with history behind it.
 */
export interface PlayerState {
  answers: Answer[];
  streak: number;
  lastPlayedDay: string;
  /** Concepts won. Derived from history, but stored so it survives a reset of the hand. */
  vault: ConceptId[];
}

/**
 * A seeded record for a returning player, built to show the shape almost
 * everybody actually has: roughly right when hedging, and increasingly
 * over-confident the surer they claim to be. The curve should teach something
 * the moment it is opened, not sit empty.
 */
function seedHistory(): Answer[] {
  const bands: { confidence: number; calls: number; hitRate: number }[] = [
    { confidence: 0.55, calls: 8, hitRate: 0.63 },
    { confidence: 0.65, calls: 9, hitRate: 0.67 },
    { confidence: 0.75, calls: 11, hitRate: 0.64 },
    { confidence: 0.85, calls: 10, hitRate: 0.6 },
    { confidence: 0.94, calls: 8, hitRate: 0.63 },
  ];

  const answers: Answer[] = [];
  for (const band of bands) {
    const hits = Math.round(band.calls * band.hitRate);
    for (let i = 0; i < band.calls; i++) {
      const correct = i < hits;
      // The stated probability of the outcome that actually happened.
      const pTrue = correct ? band.confidence : 1 - band.confidence;
      const error = 1 - pTrue;
      answers.push({
        claimId: `seed-${band.confidence}-${i}`,
        side: "true",
        confidence: band.confidence,
        correct,
        points: Math.round(100 * (1 - 2 * error * error)),
      });
    }
  }
  return answers;
}

const FALLBACK: PlayerState = {
  answers: seedHistory(),
  streak: 6,
  lastPlayedDay: "",
  vault: ["splits", "cashflow"],
};

export function dayKey(date = new Date()): string {
  return `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;
}

const store = createPersistedStore<PlayerState>(
  "edenomics.player.v3",
  FALLBACK,
  (raw) => {
    if (typeof raw !== "object" || raw === null) return null;
    const stored = raw as Partial<PlayerState>;
    return {
      answers: Array.isArray(stored.answers) ? (stored.answers as Answer[]) : seedHistory(),
      streak: typeof stored.streak === "number" ? stored.streak : FALLBACK.streak,
      lastPlayedDay: typeof stored.lastPlayedDay === "string" ? stored.lastPlayedDay : "",
      vault: Array.isArray(stored.vault) ? (stored.vault as ConceptId[]) : [],
    };
  },
);

const noopSubscribe = () => () => {};
const getToday = () => dayKey();
const getTodayOnServer = () => "";

export interface PlayerApi extends PlayerState {
  playedToday: boolean;
  recordHand: (answers: Answer[], won: ConceptId[]) => void;
  reset: () => void;
}

export function usePlayer(): PlayerApi {
  const state = useSyncExternalStore(store.subscribe, store.getSnapshot, store.getServerSnapshot);
  const today = useSyncExternalStore(noopSubscribe, getToday, getTodayOnServer);

  const recordHand = useCallback((answers: Answer[], won: ConceptId[]) => {
    store.set((current) => {
      const day = dayKey();
      const first = current.lastPlayedDay !== day;
      return {
        answers: [...current.answers, ...answers],
        streak: first ? current.streak + 1 : current.streak,
        lastPlayedDay: day,
        vault: [...new Set([...current.vault, ...won])],
      };
    });
  }, []);

  const reset = useCallback(() => store.set(() => ({ ...FALLBACK, answers: seedHistory() })), []);

  return useMemo(
    () => ({
      ...state,
      playedToday: today !== "" && state.lastPlayedDay === today,
      recordHand,
      reset,
    }),
    [state, today, recordHand, reset],
  );
}
