import type { ComponentPropsWithoutRef, ReactNode } from "react";

type Variant = "primary" | "secondary" | "ghost";
type Size = "sm" | "md" | "lg";

/*
  Game buttons want weight. The hard bottom edge plus a downward nudge on
  press is what sells "this is a thing I pushed" rather than "this is a link".
*/
const base =
  "relative inline-flex items-center justify-center gap-2 rounded-2xl font-semibold whitespace-nowrap select-none transition-[transform,background-color,border-color,box-shadow] duration-150 ease-pop disabled:pointer-events-none disabled:opacity-45";

const variants: Record<Variant, string> = {
  primary:
    "bg-brand text-void shadow-[0_4px_0_var(--color-brand-deep)] hover:brightness-110 hover:-translate-y-px active:translate-y-[3px] active:shadow-[0_1px_0_var(--color-brand-deep)]",
  secondary:
    "piece piece-hover text-fg",
  ghost: "text-muted hover:text-fg hover:bg-white/[0.06]",
};

const sizes: Record<Size, string> = {
  sm: "h-9 px-4 text-[0.8125rem]",
  md: "h-11 px-5 text-[0.9375rem]",
  lg: "h-14 px-7 text-base",
};

interface Common {
  variant?: Variant;
  size?: Size;
  className?: string;
  children: ReactNode;
}

type ButtonProps = Common & Omit<ComponentPropsWithoutRef<"button">, "className" | "children">;
type LinkProps = Common &
  Omit<ComponentPropsWithoutRef<"a">, "className" | "children"> & { href: string };

export function Button({
  variant = "primary",
  size = "md",
  className = "",
  children,
  ...props
}: ButtonProps) {
  return (
    <button className={`${base} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {children}
    </button>
  );
}

export function ButtonLink({
  variant = "primary",
  size = "md",
  className = "",
  children,
  ...props
}: LinkProps) {
  return (
    <a className={`${base} ${variants[variant]} ${sizes[size]} ${className}`} {...props}>
      {children}
    </a>
  );
}
