/** Formatting helpers shared across markets, stories and the feed. */

export function formatPct(value: number, withSign = true): string {
  const sign = withSign && value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function direction(value: number): "up" | "down" | "flat" {
  if (value > 0.001) return "up";
  if (value < -0.001) return "down";
  return "flat";
}

export function readTime(seconds: number): string {
  if (seconds < 60) return `${seconds} sec`;
  const minutes = Math.round(seconds / 60);
  return `${minutes} min`;
}

export function timeAgo(minutes: number): string {
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return rest ? `${hours}h ${rest}m ago` : `${hours}h ago`;
}
