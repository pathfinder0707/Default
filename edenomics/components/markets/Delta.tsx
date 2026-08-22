import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import { direction, formatPct } from "@/lib/format";

const sizes = {
  sm: "text-[0.75rem] gap-0.5",
  md: "text-[0.8125rem] gap-1",
  lg: "text-base gap-1",
} as const;

const iconSizes = { sm: 11, md: 13, lg: 15 } as const;

/**
 * The one place green and red are allowed. Everything else on the page uses
 * the brand accent, so a colour change here always means price movement.
 */
export function Delta({
  value,
  size = "md",
  showIcon = true,
  className = "",
}: {
  value: number;
  size?: keyof typeof sizes;
  showIcon?: boolean;
  className?: string;
}) {
  const dir = direction(value);
  const tone =
    dir === "up" ? "text-up" : dir === "down" ? "text-down" : "text-muted";
  const Icon = dir === "up" ? ArrowUpRight : dir === "down" ? ArrowDownRight : Minus;

  return (
    <span className={`tabular inline-flex items-center ${sizes[size]} ${tone} ${className}`}>
      {showIcon && <Icon size={iconSizes[size]} strokeWidth={2.5} aria-hidden />}
      {formatPct(value)}
    </span>
  );
}
