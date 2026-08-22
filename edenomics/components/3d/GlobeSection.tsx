"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "motion/react";
import { Container } from "@/components/layout/Section";
import { Reveal } from "@/components/ui/Reveal";
import { GlobeFallback } from "@/components/3d/GlobeFallback";
import { Delta } from "@/components/markets/Delta";
import { EXCHANGES } from "@/lib/data/exchanges";
import { sessionStatus } from "@/lib/market-clock";
import { useNow } from "@/lib/hooks/useNow";

// Three.js only ships to browsers that reach this section.
const Globe = dynamic(() => import("@/components/3d/Globe"), { ssr: false });

function webglAvailable(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(
      window.WebGLRenderingContext &&
        (canvas.getContext("webgl2") || canvas.getContext("webgl")),
    );
  } catch {
    return false;
  }
}

export function GlobeSection() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<"idle" | "ready" | "unsupported">("idle");
  const [focusId, setFocusId] = useState<string | null>(null);
  const reduceMotion = useReducedMotion();
  const now = useNow(30_000);

  useEffect(() => {
    const node = containerRef.current;
    if (!node) return;
    // Both the WebGL probe and the three.js chunk are deferred until the
    // section is close to the viewport, so nothing above it pays for them.
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        observer.disconnect();
        setStatus(webglAvailable() ? "ready" : "unsupported");
      },
      { rootMargin: "300px" },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  const showGlobe = status === "ready";
  const openIds = now
    ? EXCHANGES.filter((m) => sessionStatus(m, now).state === "open").map((m) => m.id)
    : [];

  return (
    <section className="border-line grain relative overflow-hidden border-y bg-[#070809] py-16 sm:py-20 lg:py-28">
      <div
        aria-hidden
        className="pointer-events-none absolute top-1/2 right-[8%] h-[540px] w-[540px] -translate-y-1/2 rounded-full opacity-[0.13] blur-[110px]"
        style={{
          background: "radial-gradient(closest-side, var(--color-accent), transparent 70%)",
        }}
      />

      <Container className="relative">
        {/*
          Explicit grid placement rather than source order: on a phone the
          globe belongs between the copy and the list, on a desktop it sits
          beside both.
        */}
        <div className="flex flex-col gap-10 lg:grid lg:grid-cols-12 lg:items-center lg:gap-x-8 lg:gap-y-6">
          <Reveal className="lg:col-span-5 lg:col-start-1 lg:row-start-1">
            <p className="eyebrow mb-3">Global markets</p>
            <h2 className="display text-[2.1rem] leading-[1.05] sm:text-[2.8rem] lg:text-[3.2rem]">
              Money never sleeps.
              <br />
              <span className="text-muted">You should.</span>
            </h2>
            <p className="text-muted mt-5 max-w-md text-[0.9375rem] leading-relaxed">
              Somewhere a market is always open. Edenomics watches the handover
              between them and only wakes you when something crosses from one
              session into the next.
            </p>
          </Reveal>

          <div
            ref={containerRef}
            className="lg:col-span-7 lg:col-start-6 lg:row-span-2 lg:row-start-1"
          >
            <div className="relative mx-auto aspect-square w-full max-w-[440px] lg:max-w-[520px]">
              {showGlobe ? (
                <Globe
                  focusId={focusId}
                  openIds={openIds}
                  animate={!reduceMotion}
                  onHoverMarket={setFocusId}
                />
              ) : (
                <GlobeFallback className="h-full w-full" />
              )}
            </div>
          </div>

          <Reveal delay={0.08} className="lg:col-span-5 lg:col-start-1 lg:row-start-2">
            <ul className="border-line divide-y divide-[rgba(255,255,255,0.06)] border-t">
              {EXCHANGES.map((market) => {
                const status = now ? sessionStatus(market, now) : null;
                const isFocused = focusId === market.id;
                return (
                  <li key={market.id}>
                    <button
                      type="button"
                      onMouseEnter={() => setFocusId(market.id)}
                      onMouseLeave={() => setFocusId(null)}
                      onFocus={() => setFocusId(market.id)}
                      onBlur={() => setFocusId(null)}
                      onClick={() => setFocusId(isFocused ? null : market.id)}
                      aria-pressed={isFocused}
                      className={`flex w-full items-center gap-3 px-2 py-3.5 text-left transition-colors duration-200 sm:gap-4 ${
                        isFocused ? "bg-white/[0.04]" : "hover:bg-white/[0.02]"
                      }`}
                    >
                      <span
                        aria-hidden
                        className={`h-1.5 w-1.5 shrink-0 rounded-full transition-colors ${
                          status?.state === "open" ? "bg-up" : "bg-faint"
                        }`}
                      />
                      <span className="min-w-0 flex-1">
                        <span className="block text-[0.9375rem]">{market.city}</span>
                        <span className="text-faint block font-mono text-[0.6875rem] tracking-wide">
                          {status ? (
                            status.label
                          ) : (
                            <span className="skeleton inline-block h-2.5 w-28 rounded align-middle" />
                          )}
                        </span>
                      </span>
                      <span className="text-right">
                        <span className="text-muted block text-[0.75rem]">
                          {market.indexName}
                        </span>
                        <span className="tabular block text-[0.8125rem]">
                          {market.indexValue}
                        </span>
                      </span>
                      <Delta
                        value={market.changePct}
                        size="sm"
                        showIcon={false}
                        className="w-14 justify-end"
                      />
                    </button>
                  </li>
                );
              })}
            </ul>
            <p className="text-faint mt-4 text-[0.75rem]">
              <span className="lg:hidden">Tap a city to bring it round.</span>
              <span className="max-lg:hidden">Hover a city to bring it round.</span>
            </p>
          </Reveal>
        </div>
      </Container>
    </section>
  );
}
