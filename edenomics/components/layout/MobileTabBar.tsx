"use client";

import { NAV_IDS, NAV_ITEMS } from "@/components/layout/nav-items";
import { useScrollSpy } from "@/lib/hooks/useScrollSpy";

export function MobileTabBar() {
  const active = useScrollSpy(NAV_IDS);

  return (
    <nav
      aria-label="Sections"
      className="border-line bg-void/90 fixed inset-x-0 bottom-0 z-50 border-t backdrop-blur-xl lg:hidden"
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
                  isActive ? "text-brand" : "text-faint"
                }`}
              >
                <Icon size={19} strokeWidth={isActive ? 2.4 : 1.8} aria-hidden />
                <span className="text-[0.625rem] font-semibold tracking-wide">{item.label}</span>
              </a>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
