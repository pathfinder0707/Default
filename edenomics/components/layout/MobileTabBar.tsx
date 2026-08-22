"use client";

import { NAV_IDS, NAV_ITEMS } from "@/components/layout/nav-items";
import { useScrollSpy } from "@/lib/hooks/useScrollSpy";

/**
 * The app-like bottom bar on phones. It mirrors the desktop nav and tracks
 * the same scroll spy, so the two never disagree about where you are.
 */
export function MobileTabBar() {
  const active = useScrollSpy(NAV_IDS);

  return (
    <nav
      aria-label="Sections"
      className="border-line bg-ink/85 fixed inset-x-0 bottom-0 z-50 border-t backdrop-blur-xl lg:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <ul className="mx-auto flex max-w-md items-stretch">
        {NAV_ITEMS.map((item) => {
          const isActive = active === item.id;
          const Icon = item.icon;
          return (
            <li key={item.id} className="flex-1">
              <a
                href={`#${item.id}`}
                aria-current={isActive ? "true" : undefined}
                className={`flex flex-col items-center gap-1 pt-2.5 pb-2 transition-colors duration-200 ${
                  isActive ? "text-accent" : "text-faint"
                }`}
              >
                <Icon size={19} strokeWidth={isActive ? 2.2 : 1.8} aria-hidden />
                <span className="text-[0.625rem] tracking-wide">{item.label}</span>
              </a>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
