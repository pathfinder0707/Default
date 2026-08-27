export function Wordmark({ className = "" }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <span
        aria-hidden
        className="bg-brand shadow-[0_2px_0_var(--color-brand-deep)] inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-xl"
      >
        <svg viewBox="0 0 16 16" width="15" height="15" fill="none" aria-hidden>
          <rect x="1.5" y="9" width="3" height="5.5" rx="1" fill="var(--color-void)" />
          <rect x="6.5" y="5.5" width="3" height="9" rx="1" fill="var(--color-void)" />
          <rect x="11.5" y="1.5" width="3" height="13" rx="1" fill="var(--color-void)" />
        </svg>
      </span>
      <span className="font-display text-[1.2rem] leading-none font-extrabold tracking-tight">
        Edenomics
      </span>
    </span>
  );
}
