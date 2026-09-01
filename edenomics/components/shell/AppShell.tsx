"use client";

import { useState, useSyncExternalStore } from "react";
import { motion, useReducedMotion } from "motion/react";
import { Flame, LineChart, Layers, Spade, Trophy, Volume2, VolumeX } from "lucide-react";
import { Table } from "@/components/table/Table";
import { CalibrationView } from "@/components/curve/CalibrationView";
import { VaultView } from "@/components/vault/VaultView";
import { RanksView } from "@/components/ranks/RanksView";
import { usePlayer } from "@/lib/state/player";
import { averageScore } from "@/lib/game/scoring";
import {
  getMutedServerSnapshot,
  getMutedSnapshot,
  setMuted,
  sfx,
  subscribeMuted,
} from "@/lib/sound";

type View = "play" | "curve" | "vault" | "ranks";

const TABS = [
  { id: "play" as const, label: "Table", icon: Spade },
  { id: "curve" as const, label: "Record", icon: LineChart },
  { id: "vault" as const, label: "Vault", icon: Layers },
  { id: "ranks" as const, label: "Ranks", icon: Trophy },
];

/**
 * An app, not a page. The table fills the screen, the meta lives behind tabs,
 * and nothing scrolls while you are playing a card — because a game that
 * scrolls away from you under your thumb is not a game.
 */
export function AppShell() {
  const player = usePlayer();
  const [view, setView] = useState<View>("play");
  const muted = useSyncExternalStore(subscribeMuted, getMutedSnapshot, getMutedServerSnapshot);
  const reduceMotion = useReducedMotion();

  const average = averageScore(player.answers);

  function toggleSound() {
    const next = !muted;
    setMuted(next);
    if (!next) sfx.tap();
  }

  return (
    <div className="felt relative flex min-h-dvh flex-col">
      <a
        href="#table"
        className="bg-brass text-felt sr-only rounded-full px-4 py-2 text-sm font-semibold focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[70]"
      >
        Skip to the table
      </a>

      {/* HUD */}
      <header className="border-line bg-felt/85 fixed inset-x-0 top-0 z-40 border-b backdrop-blur-md">
        <div className="mx-auto flex h-14 w-full max-w-[620px] items-center gap-3 px-4">
          <span className="flex items-center gap-2">
            <span className="text-brass text-[1.05rem] leading-none" aria-hidden>
              ♠
            </span>
            <span className="display text-[1.05rem] leading-none">Edenomics</span>
          </span>

          <div className="ml-auto flex items-center gap-2">
            <span
              className="rail flex items-center gap-1.5 rounded-lg px-2.5 py-1.5"
              title={`${player.streak} day streak`}
            >
              <Flame size={13} className="text-brass" aria-hidden />
              <span className="tabular text-[0.75rem] font-bold">{player.streak}</span>
              <span className="sr-only">day streak</span>
            </span>
            <span
              className="rail flex items-center gap-1.5 rounded-lg px-2.5 py-1.5"
              title="Average Brier score. A coin flip scores 50."
            >
              <span className="label text-[0.5rem]">avg</span>
              <span className="tabular text-[0.75rem] font-bold">{average.toFixed(0)}</span>
            </span>
            <button
              type="button"
              onClick={toggleSound}
              aria-pressed={muted}
              aria-label={muted ? "Turn sound on" : "Turn sound off"}
              className="rail rail-hover text-muted hover:text-cream rounded-lg p-2"
            >
              {muted ? <VolumeX size={14} aria-hidden /> : <Volume2 size={14} aria-hidden />}
            </button>
          </div>
        </div>
      </header>

      <main
        id="table"
        className="flex flex-1 flex-col items-center pt-16 pb-24"
      >
        <motion.div
          key={view}
          initial={reduceMotion ? false : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.26, ease: [0.22, 1, 0.36, 1] }}
          className="my-auto flex w-full flex-col items-center"
        >
          {view === "play" && <Table onSeeCurve={() => setView("curve")} />}
          {view === "curve" && <CalibrationView />}
          {view === "vault" && <VaultView />}
          {view === "ranks" && <RanksView />}
        </motion.div>
      </main>

      {/* Tabs */}
      <nav
        aria-label="Views"
        className="border-line bg-felt/90 fixed inset-x-0 bottom-0 z-40 border-t backdrop-blur-md"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        <ul className="mx-auto flex max-w-[620px] items-stretch">
          {TABS.map((tab) => {
            const active = view === tab.id;
            const Icon = tab.icon;
            return (
              <li key={tab.id} className="flex-1">
                <button
                  type="button"
                  onClick={() => {
                    setView(tab.id);
                    sfx.tap();
                  }}
                  aria-current={active ? "page" : undefined}
                  className={`relative flex w-full flex-col items-center gap-1 pt-2.5 pb-2 transition-colors ${
                    active ? "text-brass" : "text-faint hover:text-muted"
                  }`}
                >
                  {active && (
                    <motion.span
                      layoutId={reduceMotion ? undefined : "tab-underline"}
                      className="bg-brass absolute inset-x-5 top-0 h-0.5 rounded-full"
                      transition={{ type: "spring", stiffness: 420, damping: 34 }}
                    />
                  )}
                  <Icon size={18} strokeWidth={active ? 2.3 : 1.8} aria-hidden />
                  <span className="text-[0.625rem] font-semibold tracking-wide">{tab.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
    </div>
  );
}
