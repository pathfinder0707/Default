"use client";

import { motion, useReducedMotion } from "motion/react";
import { RANKS, rankFor, table } from "@/lib/game/ranks";
import { averageScore } from "@/lib/game/scoring";
import { usePlayer } from "@/lib/state/player";

/**
 * The table of players, ranked by average score rather than by how much they
 * have played. Time served earns nothing here, which is the point.
 */
export function RanksView() {
  const player = usePlayer();
  const reduceMotion = useReducedMotion();
  const average = averageScore(player.answers);
  const rows = table({ score: average, calls: player.answers.length });
  const yourRank = rows.findIndex((row) => row.isYou) + 1;
  const { rank } = rankFor(average);

  return (
    <div className="mx-auto w-full max-w-[520px] px-5 pb-8">
      <header className="pt-2 pb-6 text-center">
        <p className="label">The table</p>
        <h2 className="display mt-2 text-[2.3rem] leading-none">
          Ranked by being right
          <br />
          <span className="text-brass">as often as you claim.</span>
        </h2>
        <p className="text-muted mx-auto mt-3 max-w-sm text-[0.875rem] leading-relaxed">
          Not by how much you have played. Someone with thirty calls can sit above someone with
          three hundred.
        </p>
      </header>

      <div className="rail overflow-hidden rounded-2xl">
        {rows.map((row, index) => (
          <motion.div
            key={row.id}
            layout={!reduceMotion}
            transition={{ type: "spring", stiffness: 400, damping: 34 }}
            className={`border-line/60 flex items-center gap-3 border-b px-4 py-3.5 last:border-b-0 sm:px-5 ${
              row.isYou ? "bg-brass/[0.09]" : ""
            }`}
          >
            <span className="tabular text-faint w-6 shrink-0 text-[0.8125rem]">{index + 1}</span>
            <span className={`min-w-0 flex-1 truncate font-semibold ${row.isYou ? "text-brass" : ""}`}>
              {row.name}
            </span>
            <span className="tabular text-faint hidden w-20 text-right text-[0.75rem] sm:block">
              {row.calls} calls
            </span>
            <span className="tabular w-14 text-right text-[0.9375rem] font-bold">
              {row.score.toFixed(1)}
            </span>
          </motion.div>
        ))}
      </div>

      <p className="text-muted mt-4 text-center text-[0.875rem]">
        You are <span className="text-brass font-semibold">#{yourRank}</span> — a {rank.name.toLowerCase()}.
      </p>

      <div className="rail mt-6 rounded-2xl p-5">
        <p className="label mb-3">The ladder</p>
        <ul className="space-y-2.5">
          {RANKS.map((step) => {
            const here = step.name === rank.name;
            return (
              <li key={step.name} className="flex items-baseline gap-3">
                <span className="tabular text-faint w-8 shrink-0 text-[0.75rem]">{step.from}</span>
                <span className={`text-[0.875rem] ${here ? "text-brass font-semibold" : "text-muted"}`}>
                  {step.name}
                </span>
                {here && <span className="label ml-auto text-[0.5rem]">you</span>}
              </li>
            );
          })}
        </ul>
      </div>

      <p className="text-faint mt-5 text-center text-[0.75rem] leading-relaxed">
        Table-mates are illustrative. Their scores cluster where real forecasters cluster —
        just above a coin flip.
      </p>
    </div>
  );
}
