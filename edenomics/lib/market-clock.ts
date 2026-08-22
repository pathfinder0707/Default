import type { ExchangeMarket } from "@/lib/types";

/**
 * Derives live session state for an exchange from the visitor's clock.
 *
 * This is intentionally simple — weekday hours only, no exchange holidays or
 * lunch breaks. It exists so the globe section reads as genuinely live rather
 * than as five hardcoded strings.
 *
 * Must only run on the client: it depends on the current time, so calling it
 * during SSR would produce markup the client immediately contradicts.
 */

export type SessionState = "open" | "closed" | "pre-open";

export interface SessionStatus {
  state: SessionState;
  /** "Open · closes in 2h 14m", "Opens in 6h 40m", "Closed" */
  label: string;
}

interface LocalTime {
  hours: number;
  weekday: number; // 0 = Sunday
}

function localTime(date: Date, timeZone: string): LocalTime {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    hour: "2-digit",
    minute: "2-digit",
    weekday: "short",
    hourCycle: "h23",
  }).formatToParts(date);

  const get = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((p) => p.type === type)?.value ?? "";

  const weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  return {
    hours: Number(get("hour")) + Number(get("minute")) / 60,
    weekday: Math.max(0, weekdays.indexOf(get("weekday"))),
  };
}

function countdown(hoursAway: number): string {
  const totalMinutes = Math.max(1, Math.round(hoursAway * 60));
  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;
  if (!h) return `${m}m`;
  return `${h}h ${m}m`;
}

export function sessionStatus(market: ExchangeMarket, now: Date = new Date()): SessionStatus {
  const { hours, weekday } = localTime(now, market.timeZone);
  const isWeekend = weekday === 0 || weekday === 6;

  if (isWeekend) {
    return { state: "closed", label: "Closed · weekend" };
  }

  if (hours >= market.opens && hours < market.closes) {
    return { state: "open", label: `Open · closes in ${countdown(market.closes - hours)}` };
  }

  if (hours < market.opens) {
    return { state: "pre-open", label: `Opens in ${countdown(market.opens - hours)}` };
  }

  // After the close. Friday evening rolls to Monday.
  const hoursToMidnight = 24 - hours;
  const daysUntilOpen = weekday === 5 ? 3 : 1;
  const away = hoursToMidnight + (daysUntilOpen - 1) * 24 + market.opens;
  return { state: "closed", label: `Closed · opens in ${countdown(away)}` };
}

/** Greeting keyed to the visitor's own morning, afternoon or evening. */
export function greeting(now: Date = new Date()): string {
  const h = now.getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

export function longDate(now: Date = new Date()): string {
  return new Intl.DateTimeFormat("en-GB", {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(now);
}
