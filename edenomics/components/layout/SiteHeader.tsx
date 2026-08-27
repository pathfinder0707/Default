"use client";

import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { Flame, Zap } from "lucide-react";
import { Wordmark } from "@/components/layout/Wordmark";
import { NAV_IDS, NAV_ITEMS } from "@/components/layout/nav-items";
import { ButtonLink } from "@/components/ui/Button";
import { useScrollSpy } from "@/lib/hooks/useScrollSpy";
import { usePlayer } from "@/lib/state/player";
import { formatXp } from "@/lib/game/format";

/**
 * A game HUD rather than a marketing nav. Streak and XP are pinned to the top
 * of every screen, because in a game those two numbers are the reason you are
 * here — and they move while you play.
 */
export function SiteHeader() {
  const [scrolled, setScrolled] = useState(false);
  const active = useScrollSpy(NAV_IDS);
  const player = usePlayer();
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <>
      <a
        href="#play"
        className="bg-brand text-void sr-only rounded-full px-4 py-2 text-sm font-semibold focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[70]"
      >
        Skip to today&rsquo;s run
      </a>

      <header
        className={`fixed inset-x-0 top-0 z-50 transition-[background-color,border-color,backdrop-filter] duration-300 ${
          scrolled
            ? "border-line bg-void/80 border-b backdrop-blur-xl"
            : "border-b border-transparent"
        }`}
      >
        <div className="mx-auto flex h-16 w-full max-w-[1220px] items-center gap-4 px-5 sm:px-8">
          <a href="#top" className="text-fg shrink-0" aria-label="Edenomics home">
            <Wordmark />
          </a>

          <nav aria-label="Sections" className="ml-6 hidden lg:block">
            <ul className="flex items-center gap-1">
              {NAV_ITEMS.map((item) => {
                const isActive = active === item.id;
                return (
                  <li key={item.id}>
                    <a
                      href={`#${item.id}`}
                      aria-current={isActive ? "true" : undefined}
                      className={`relative inline-flex h-9 items-center rounded-xl px-3.5 text-[0.875rem] font-medium transition-colors duration-200 ${
                        isActive ? "text-fg" : "text-muted hover:text-fg"
                      }`}
                    >
                      {isActive && (
                        <motion.span
                          layoutId={reduceMotion ? undefined : "nav-pill"}
                          className="absolute inset-0 -z-10 rounded-xl bg-white/[0.08]"
                          transition={{ type: "spring", stiffness: 400, damping: 34 }}
                        />
                      )}
                      {item.label}
                    </a>
                  </li>
                );
              })}
            </ul>
          </nav>

          <div className="ml-auto flex items-center gap-2 sm:gap-2.5">
            <span
              className="border-line flex items-center gap-1.5 rounded-xl border bg-white/[0.03] px-2.5 py-1.5"
              title={`${player.streak} day streak`}
            >
              <Flame size={15} className="text-streak" aria-hidden />
              <span className="tabular text-[0.8125rem] font-bold">{player.streak}</span>
              <span className="sr-only">day streak</span>
            </span>

            <span
              className="border-line flex items-center gap-1.5 rounded-xl border bg-white/[0.03] px-2.5 py-1.5"
              title={`${formatXp(player.xp)} XP`}
            >
              <Zap size={15} className="text-xp" aria-hidden />
              <span className="tabular text-[0.8125rem] font-bold">{formatXp(player.xp)}</span>
              <span className="sr-only">total XP</span>
            </span>

            <ButtonLink href="#play" size="sm" className="max-sm:hidden">
              Play
            </ButtonLink>
          </div>
        </div>
      </header>
    </>
  );
}
