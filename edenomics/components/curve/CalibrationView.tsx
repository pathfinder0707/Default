"use client";

import { CalibrationChart } from "@/components/curve/CalibrationChart";
import { usePlayer } from "@/lib/state/player";
import {
  COIN_FLIP_SCORE,
  averageScore,
  calibration,
  overconfidence,
} from "@/lib/game/scoring";
import { rankFor } from "@/lib/game/ranks";

/** The full record. This is the scoreboard the game actually cares about. */
export function CalibrationView() {
  const player = usePlayer();
  const answers = player.answers;
  const buckets = calibration(answers);
  const average = averageScore(answers);
  const gap = overconfidence(answers);
  const { rank, next } = rankFor(average);

  return (
    <div className="mx-auto w-full max-w-[520px] px-5 pb-8">
      <header className="pt-2 pb-6 text-center">
        <p className="label">Your record</p>
        <h2 className="display mt-2 text-[2.3rem] leading-none">
          When you say 80%,
          <br />
          <span className="text-brass">are you right 80% of the time?</span>
        </h2>
      </header>

      <div className="rail rounded-3xl p-5">
        <CalibrationChart buckets={buckets} />
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2.5">
        <Stat label="Average" value={average.toFixed(0)} note={`coin flip ${COIN_FLIP_SCORE}`} />
        <Stat label="Calls" value={String(answers.length)} note="all time" />
        <Stat
          label={gap >= 0 ? "Overconfident" : "Underconfident"}
          value={`${Math.abs(Math.round(gap * 100))}`}
          note="points"
          tone={Math.abs(gap) > 0.08 ? "warn" : "good"}
        />
      </div>

      <div className="rail mt-4 rounded-2xl p-5">
        <p className="label mb-1.5">Rank</p>
        <p className="display text-[1.7rem] leading-none">{rank.name}</p>
        <p className="text-muted mt-2 text-[0.875rem] leading-relaxed">{rank.blurb}</p>
        {next && (
          <p className="text-faint mt-3 font-mono text-[0.6875rem]">
            {(next.from - average).toFixed(1)} points of average score to {next.name}
          </p>
        )}
      </div>

      <div className="rail mt-4 overflow-hidden rounded-2xl">
        <div className="border-line text-faint grid grid-cols-[1fr_auto_auto] gap-4 border-b px-5 py-2.5 font-mono text-[0.625rem] tracking-[0.14em] uppercase">
          <span>When you said</span>
          <span className="text-right">You were right</span>
          <span className="text-right">Calls</span>
        </div>
        {buckets.map((bucket) => {
          const drift = bucket.count ? bucket.actual - bucket.stated : 0;
          return (
            <div
              key={bucket.from}
              className="border-line/60 grid grid-cols-[1fr_auto_auto] items-center gap-4 border-b px-5 py-3 last:border-b-0"
            >
              <span className="tabular text-[0.875rem]">
                {Math.round(bucket.from * 100)}–{Math.round(bucket.to * 100)}%
              </span>
              <span
                className={`tabular text-right text-[0.875rem] font-semibold ${
                  !bucket.count
                    ? "text-faint"
                    : drift < -0.08
                      ? "text-crimson"
                      : drift > 0.08
                        ? "text-jade"
                        : "text-cream"
                }`}
              >
                {bucket.count ? `${Math.round(bucket.actual * 100)}%` : "—"}
              </span>
              <span className="tabular text-faint w-8 text-right text-[0.8125rem]">
                {bucket.count}
              </span>
            </div>
          );
        })}
      </div>

      <p className="text-faint mt-5 text-center text-[0.75rem] leading-relaxed">
        Scored with a Brier rule. Hedging every call to 50% scores exactly 50 forever, and
        claiming 99% costs 96 points when you are wrong — so the highest-scoring strategy is
        simply telling the truth about what you know.
      </p>
    </div>
  );
}

function Stat({
  label,
  value,
  note,
  tone = "neutral",
}: {
  label: string;
  value: string;
  note: string;
  tone?: "neutral" | "good" | "warn";
}) {
  return (
    <div className="rail rounded-2xl p-3.5 text-center">
      <p className="label text-[0.5rem]">{label}</p>
      <p
        className={`display mt-1.5 text-[1.7rem] leading-none ${
          tone === "warn" ? "text-crimson" : tone === "good" ? "text-jade" : "text-cream"
        }`}
      >
        {value}
      </p>
      <p className="text-faint mt-1 font-mono text-[0.5625rem]">{note}</p>
    </div>
  );
}
