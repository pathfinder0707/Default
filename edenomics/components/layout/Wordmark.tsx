export function Wordmark({ className = "" }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`}>
      <svg
        viewBox="0 0 20 20"
        width="20"
        height="20"
        fill="none"
        aria-hidden
        className="shrink-0"
      >
        <circle cx="10" cy="10" r="8.75" stroke="currentColor" strokeOpacity="0.22" />
        <path
          d="M4.6 13.4 8.6 8.9l3 2.6 3.9-5.4"
          stroke="var(--color-accent)"
          strokeWidth="1.7"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span className="font-serif text-[1.2rem] leading-none tracking-[-0.01em]">
        Edenomics
      </span>
    </span>
  );
}
