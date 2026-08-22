"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Bell, Mail, MessageCircle } from "lucide-react";

const CHANNELS = [
  {
    id: "browser",
    label: "Browser",
    hint: "Only for moves you'd want interrupting for",
    icon: Bell,
    defaultOn: true,
  },
  {
    id: "email",
    label: "Email",
    hint: "One digest, 7:30am your time",
    icon: Mail,
    defaultOn: true,
  },
  {
    id: "whatsapp",
    label: "WhatsApp",
    hint: "Rolling out soon",
    icon: MessageCircle,
    defaultOn: false,
  },
] as const;

const PREVIEWS = [
  {
    title: "Nvidia · +4.2%",
    body: "Chip orders came in ahead of expectations. Two suppliers followed.",
    time: "now",
  },
  {
    title: "Gold · −0.32%",
    body: "First down week in eight. Nothing structural — profit taking.",
    time: "2h ago",
  },
  {
    title: "RBI · rates held",
    body: "Stance moved to accommodative. Banks reacted before the rate did.",
    time: "5h ago",
  },
];

/**
 * Makes the notification promise concrete: which channels, what they'd
 * actually say, and how rarely they'd fire.
 */
export function NotificationPanel() {
  const [enabled, setEnabled] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(CHANNELS.map((c) => [c.id, c.defaultOn])),
  );
  const [index, setIndex] = useState(0);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    if (reduceMotion) return;
    const id = window.setInterval(() => setIndex((i) => (i + 1) % PREVIEWS.length), 4200);
    return () => window.clearInterval(id);
  }, [reduceMotion]);

  const preview = PREVIEWS[index];

  return (
    <div className="border-line bg-elevated flex h-full flex-col rounded-2xl border p-6 sm:p-7">
      <h3 className="display text-[1.6rem] leading-tight sm:text-[1.85rem]">
        Stop checking markets
        <br />
        every twenty minutes.
      </h3>
      <p className="text-muted mt-4 text-[0.9375rem] leading-relaxed">
        Follow what matters and Edenomics tells you when something happens. Nothing
        else — no daily price recaps, no push about a 0.2% move.
      </p>

      <div className="border-line mt-6 overflow-hidden rounded-xl border bg-black/25 p-4">
        <p className="eyebrow mb-3">What you&rsquo;d actually get</p>
        <div className="relative h-[74px]">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={preview.title}
              initial={reduceMotion ? false : { opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={reduceMotion ? undefined : { opacity: 0, y: -10 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              className="border-line bg-elevated absolute inset-0 flex gap-3 rounded-lg border p-3"
            >
              <span className="bg-accent/15 text-accent flex h-8 w-8 shrink-0 items-center justify-center rounded-lg">
                <Bell size={14} aria-hidden />
              </span>
              <span className="min-w-0 flex-1">
                <span className="flex items-baseline gap-2">
                  <span className="truncate text-[0.8125rem]">{preview.title}</span>
                  <span className="text-faint ml-auto shrink-0 font-mono text-[0.625rem]">
                    {preview.time}
                  </span>
                </span>
                <span className="text-muted mt-1 block text-[0.75rem] leading-snug">
                  {preview.body}
                </span>
              </span>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>

      <ul className="mt-6 space-y-1">
        {CHANNELS.map((channel) => {
          const Icon = channel.icon;
          const on = enabled[channel.id];
          const isSoon = channel.id === "whatsapp";
          return (
            <li key={channel.id}>
              <button
                type="button"
                onClick={() =>
                  setEnabled((current) => ({ ...current, [channel.id]: !current[channel.id] }))
                }
                role="switch"
                aria-checked={on}
                disabled={isSoon}
                className="flex w-full items-center gap-3 rounded-xl px-2 py-2.5 text-left transition-colors hover:bg-white/[0.03] disabled:cursor-not-allowed disabled:opacity-55 disabled:hover:bg-transparent"
              >
                <Icon size={15} className={on ? "text-accent" : "text-faint"} aria-hidden />
                <span className="min-w-0 flex-1">
                  <span className="block text-[0.875rem]">{channel.label}</span>
                  <span className="text-faint block text-[0.75rem]">{channel.hint}</span>
                </span>
                <span
                  aria-hidden
                  className={`relative h-5 w-9 shrink-0 rounded-full transition-colors duration-200 ${
                    on ? "bg-accent" : "bg-white/12"
                  }`}
                >
                  <motion.span
                    layout={!reduceMotion}
                    transition={{ type: "spring", stiffness: 520, damping: 34 }}
                    className={`absolute top-0.5 h-4 w-4 rounded-full ${
                      on ? "bg-ink right-0.5" : "left-0.5 bg-white/70"
                    }`}
                  />
                </span>
              </button>
            </li>
          );
        })}
      </ul>

      <p className="text-faint border-line mt-auto border-t pt-5 text-[0.75rem] leading-relaxed">
        Roughly three notifications a week for a typical watchlist. You can change
        the bar for what counts as important.
      </p>
    </div>
  );
}
