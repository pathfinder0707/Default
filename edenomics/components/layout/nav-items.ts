import { BookOpen, LineChart, Newspaper, Star } from "lucide-react";

/** One source of truth for the desktop nav, the mobile tab bar and scroll spy. */
export const NAV_ITEMS = [
  { id: "today", label: "Today", icon: Newspaper },
  { id: "markets", label: "Markets", icon: LineChart },
  { id: "learn", label: "Learn", icon: BookOpen },
  { id: "watchlist", label: "Watchlist", icon: Star },
] as const;

export const NAV_IDS: readonly string[] = NAV_ITEMS.map((item) => item.id);
