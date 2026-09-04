/**
 * Deterministic price series for sparklines and the lead chart.
 *
 * Seeded on purpose: the server and the client must render byte-identical
 * paths, and a demo should look the same every time you show it to someone.
 * Replace with real OHLC data later — the components only need normalised
 * 0–1 values.
 */

function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * @param seed   any stable number — use one per instrument
 * @param points how many samples to draw
 * @param drift  net move across the window; sign should match the day's change
 */
export function series(seed: number, points = 28, drift = 0): number[] {
  const rand = mulberry32(seed);
  const raw: number[] = [];
  let value = 0;

  for (let i = 0; i < points; i++) {
    // Mean-reverting noise plus a steady drift keeps the shape believable
    // rather than a straight line or pure static.
    value += (rand() - 0.5) * 0.9 - value * 0.18 + drift / points;
    raw.push(value);
  }

  // One smoothing pass: the raw walk reads as static, a smoothed one reads
  // as a price.
  const smoothed = raw.map((value, i) => {
    const prev = raw[i - 1] ?? value;
    const next = raw[i + 1] ?? value;
    return (prev + value * 2 + next) / 4;
  });

  const min = Math.min(...smoothed);
  const max = Math.max(...smoothed);
  const span = max - min || 1;
  return smoothed.map((v) => (v - min) / span);
}

/**
 * A spike that gives most of itself back — the shape of a stock popping on
 * good news and then fading as the move gets sold into.
 *
 * @param peakAt   index of the high
 * @param endLevel where it settles, 0–1 relative to the peak
 */
export function pumpAndFade(
  seed: number,
  points: number,
  peakAt: number,
  endLevel: number,
): number[] {
  const rand = mulberry32(seed);
  const easeOut = (t: number) => 1 - Math.pow(1 - t, 2.2);
  const raw: number[] = [];

  for (let i = 0; i < points; i++) {
    const base =
      i <= peakAt
        ? 0.12 + easeOut(i / peakAt) * 0.88
        : 1 - easeOut((i - peakAt) / (points - 1 - peakAt)) * (1 - endLevel);
    raw.push(base + (rand() - 0.5) * 0.09);
  }

  const min = Math.min(...raw);
  const max = Math.max(...raw);
  const span = max - min || 1;
  return raw.map((v) => (v - min) / span);
}
