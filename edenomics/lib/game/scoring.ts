/**
 * Brier scoring.
 *
 * This is the whole design. Brier is a *proper* scoring rule: your expected
 * score is highest when the number you state is the number you actually
 * believe. There is no way to farm it by always shouting 99%, and no way to
 * hide by always hedging — so the game cannot reward the one instinct that
 * costs people real money, which is confidence they haven't earned.
 *
 *   say 50/50           →  50, always, whatever happens
 *   say 90% and right   →  +98
 *   say 90% and wrong   →  −62
 *   say 99% and wrong   →  −96
 */

/** Confidence never drops below a coin flip or reaches certainty. */
export const MIN_CONFIDENCE = 0.5;
export const MAX_CONFIDENCE = 0.99;

/** @param pTrue probability the player assigned to the claim being true */
export function brierPoints(pTrue: number, claimIsTrue: boolean): number {
  const error = (claimIsTrue ? 1 : 0) - pTrue;
  return Math.round(100 * (1 - 2 * error * error));
}

/** Convert a side plus a confidence into the probability assigned to "true". */
export function probabilityOfTrue(side: "true" | "false", confidence: number): number {
  return side === "true" ? confidence : 1 - confidence;
}

/** What a coin flip earns, for comparison on the scoreboard. */
export const COIN_FLIP_SCORE = 50;

export interface Answer {
  claimId: string;
  side: "true" | "false";
  /** 0.5–0.99, how sure the player was of their side. */
  confidence: number;
  correct: boolean;
  points: number;
}

export interface CalibrationBucket {
  /** Lower edge of the confidence band, e.g. 0.7 for "70–80%". */
  from: number;
  to: number;
  count: number;
  /** Mean confidence actually stated inside this band. */
  stated: number;
  /** Share of those calls that turned out right. */
  actual: number;
}

const BANDS = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0];

/**
 * Groups answers into confidence bands and reports how often each band was
 * right. A perfectly calibrated person sits on the diagonal: when they say
 * 70%, they are right 70% of the time.
 */
export function calibration(answers: Answer[]): CalibrationBucket[] {
  return BANDS.slice(0, -1).map((from, index) => {
    const to = BANDS[index + 1];
    const inBand = answers.filter(
      (a) => a.confidence >= from && (to === 1 ? a.confidence <= to : a.confidence < to),
    );
    const count = inBand.length;
    return {
      from,
      to,
      count,
      stated: count ? inBand.reduce((sum, a) => sum + a.confidence, 0) / count : (from + to) / 2,
      actual: count ? inBand.filter((a) => a.correct).length / count : 0,
    };
  });
}

/**
 * One number for the whole record: positive means overconfident (you were
 * right less often than you claimed), negative means you undersold yourself.
 */
export function overconfidence(answers: Answer[]): number {
  if (!answers.length) return 0;
  const stated = answers.reduce((sum, a) => sum + a.confidence, 0) / answers.length;
  const actual = answers.filter((a) => a.correct).length / answers.length;
  return stated - actual;
}

export function averageScore(answers: Answer[]): number {
  if (!answers.length) return COIN_FLIP_SCORE;
  return answers.reduce((sum, a) => sum + a.points, 0) / answers.length;
}
