"use client";

import { useCallback, useEffect, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { Search } from "lucide-react";
import { Wordmark } from "@/components/layout/Wordmark";
import { NAV_IDS, NAV_ITEMS } from "@/components/layout/nav-items";
import { CommandPalette } from "@/components/layout/CommandPalette";
import { Button, ButtonLink } from "@/components/ui/Button";
import { useScrollSpy } from "@/lib/hooks/useScrollSpy";

export function SiteHeader() {
  const [scrolled, setScrolled] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const active = useScrollSpy(NAV_IDS);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "k" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        setSearchOpen((open) => !open);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  const closeSearch = useCallback(() => setSearchOpen(false), []);

  return (
    <>
      <a
        href="#today"
        className="bg-accent text-ink sr-only rounded-full px-4 py-2 text-sm font-medium focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-[70]"
      >
        Skip to today&rsquo;s brief
      </a>

      <header
        className={`fixed inset-x-0 top-0 z-50 transition-[background-color,border-color,backdrop-filter] duration-300 ${
          scrolled
            ? "border-line bg-ink/75 border-b backdrop-blur-xl"
            : "border-b border-transparent"
        }`}
      >
        <div className="mx-auto flex h-16 w-full max-w-[1240px] items-center gap-4 px-5 sm:px-8 lg:px-10">
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
                      className={`relative inline-flex h-8 items-center rounded-full px-3.5 text-[0.8125rem] transition-colors duration-200 ${
                        isActive ? "text-fg" : "text-muted hover:text-fg"
                      }`}
                    >
                      {isActive && (
                        <motion.span
                          layoutId={reduceMotion ? undefined : "nav-pill"}
                          className="absolute inset-0 -z-10 rounded-full bg-white/[0.07]"
                          transition={{ type: "spring", stiffness: 380, damping: 32 }}
                        />
                      )}
                      {item.label}
                    </a>
                  </li>
                );
              })}
            </ul>
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <button
              type="button"
              onClick={() => setSearchOpen(true)}
              aria-label="Search"
              className="text-muted hover:text-fg border-line hover:border-line-strong inline-flex h-9 items-center gap-2 rounded-full border px-3 transition-colors sm:pr-2"
            >
              <Search size={15} aria-hidden />
              <kbd className="border-line text-faint hidden rounded border px-1.5 py-px font-mono text-[0.625rem] sm:block">
                ⌘K
              </kbd>
            </button>

            <a
              href="#top"
              className="text-muted hover:text-fg hidden px-2 text-[0.8125rem] transition-colors md:block"
            >
              Sign in
            </a>

            <ButtonLink href="#watchlist" size="sm" className="max-sm:hidden">
              Start your feed
            </ButtonLink>
            <Button
              size="sm"
              className="sm:hidden"
              onClick={() =>
                document.getElementById("watchlist")?.scrollIntoView({ block: "start" })
              }
            >
              Start
            </Button>
          </div>
        </div>
      </header>

      <CommandPalette open={searchOpen} onClose={closeSearch} />
    </>
  );
}
