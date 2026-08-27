/** Number formatting shared by the rounds, the lab and the HUD. */

const USD_UNITS: [number, string][] = [
  [1e12, "T"],
  [1e9, "B"],
  [1e6, "M"],
  [1e3, "K"],
];

/** $3.4T, $920B, $45M — compact enough to sit on a slider tick. */
export function formatUsd(value: number): string {
  for (const [size, suffix] of USD_UNITS) {
    if (Math.abs(value) >= size) {
      const scaled = value / size;
      return `$${scaled >= 100 ? scaled.toFixed(0) : scaled.toFixed(1)}${suffix}`;
    }
  }
  return `$${Math.round(value)}`;
}

/** Indian units, because a lakh is how the number is actually said here. */
export function formatInr(value: number): string {
  if (Math.abs(value) >= 1e7) return `₹${(value / 1e7).toFixed(2)} Cr`;
  if (Math.abs(value) >= 1e5) return `₹${(value / 1e5).toFixed(2)} L`;
  return `₹${Math.round(value).toLocaleString("en-IN")}`;
}

export function formatCompact(value: number, style: "usd" | "inr" | "plain" | "percent"): string {
  if (style === "usd") return formatUsd(value);
  if (style === "inr") return formatInr(value);
  if (style === "percent") return `${value.toFixed(1)}%`;
  return Math.round(value).toLocaleString("en-IN");
}

export function formatSignedPct(value: number, digits = 1): string {
  return `${value > 0 ? "+" : ""}${value.toFixed(digits)}%`;
}

export function formatXp(value: number): string {
  return Math.round(value).toLocaleString("en-IN");
}
