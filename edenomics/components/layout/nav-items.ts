import { BarChart3, Gamepad2, Trophy, Waypoints, User } from "lucide-react";

/** One source of truth for the header, the mobile tab bar and scroll spy. */
export const NAV_ITEMS = [
  { id: "play", label: "Play", icon: Gamepad2 },
  { id: "progress", label: "You", icon: User },
  { id: "skills", label: "Skills", icon: Waypoints },
  { id: "lab", label: "Lab", icon: BarChart3 },
  { id: "league", label: "League", icon: Trophy },
] as const;

export const NAV_IDS: readonly string[] = NAV_ITEMS.map((item) => item.id);
