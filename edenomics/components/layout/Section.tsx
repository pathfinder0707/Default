import type { ReactNode } from "react";
import { Reveal } from "@/components/ui/Reveal";

export function Container({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`mx-auto w-full max-w-[1240px] px-5 sm:px-8 lg:px-10 ${className}`}>
      {children}
    </div>
  );
}

/**
 * Shared section header: a mono eyebrow, an editorial serif title and an
 * optional action on the right. Consistent enough that the page reads as one
 * publication rather than a stack of components.
 */
export function SectionHeading({
  eyebrow,
  title,
  description,
  action,
  className = "",
}: {
  eyebrow?: string;
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <Reveal
      as="header"
      className={`flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between ${className}`}
    >
      <div className="max-w-2xl">
        {eyebrow && <p className="eyebrow mb-3">{eyebrow}</p>}
        <h2 className="display text-[2rem] leading-[1.05] sm:text-[2.6rem] lg:text-[3rem]">
          {title}
        </h2>
        {description && (
          <p className="text-muted mt-4 max-w-xl text-[0.9375rem] leading-relaxed">
            {description}
          </p>
        )}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </Reveal>
  );
}

/** Hairline rule used between major sections. */
export function Hairline({ className = "" }: { className?: string }) {
  return <div className={`bg-line h-px w-full ${className}`} />;
}
