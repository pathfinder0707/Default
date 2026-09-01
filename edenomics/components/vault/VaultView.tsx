"use client";

import { motion, useReducedMotion } from "motion/react";
import { CONCEPTS, SUITS, type Suit } from "@/lib/game/concepts";
import { usePlayer } from "@/lib/state/player";

/**
 * The vault. Every idea in the game is a playing card, and the only way to
 * turn one face-up is to have called its claim correctly. Nothing is
 * purchasable, so a full deck means exactly one thing.
 */
export function VaultView() {
  const player = usePlayer();
  const owned = new Set(player.vault);
  const reduceMotion = useReducedMotion();

  const bySuit = (Object.keys(SUITS) as Suit[]).map((suit) => ({
    suit,
    cards: CONCEPTS.filter((concept) => concept.suit === suit),
  }));

  return (
    <div className="mx-auto w-full max-w-[760px] px-5 pb-8">
      <header className="pt-2 pb-6 text-center">
        <p className="label">The vault</p>
        <h2 className="display mt-2 text-[2.3rem] leading-none">
          {owned.size} of {CONCEPTS.length}
          <br />
          <span className="text-brass">ideas turned face-up.</span>
        </h2>
        <p className="text-muted mx-auto mt-3 max-w-sm text-[0.875rem] leading-relaxed">
          A card turns over when you call its claim correctly. There is nothing to buy, and no
          way to shortcut a single one of them.
        </p>
      </header>

      {bySuit.map(({ suit, cards }) => (
        <section key={suit} className="mb-7">
          <div className="mb-3 flex items-center gap-2">
            <span className="text-[1rem] leading-none" style={{ color: SUITS[suit].tint }} aria-hidden>
              {SUITS[suit].glyph}
            </span>
            <h3 className="label">{SUITS[suit].label}</h3>
            <span className="text-faint tabular ml-auto text-[0.6875rem]">
              {cards.filter((c) => owned.has(c.id)).length}/{cards.length}
            </span>
          </div>

          <ul className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 lg:grid-cols-4">
            {cards.map((concept, index) => {
              const has = owned.has(concept.id);
              const tint = SUITS[suit].tint;
              return (
                <motion.li
                  key={concept.id}
                  initial={reduceMotion ? false : { opacity: 0, y: 14, rotateY: has ? 0 : 0 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.04, duration: 0.35 }}
                >
                  <div
                    className={`flex aspect-[5/7] flex-col rounded-xl p-3 ${
                      has ? "card-face" : "card-back"
                    }`}
                  >
                    {has ? (
                      <>
                        <span className="flex items-baseline gap-1">
                          <span
                            className="display text-[1.05rem] leading-none"
                            style={{ color: tint === "#eae4d6" ? "#151f1b" : tint }}
                          >
                            {concept.rank}
                          </span>
                          <span
                            className="text-[0.8125rem] leading-none"
                            style={{ color: tint === "#eae4d6" ? "#151f1b" : tint }}
                            aria-hidden
                          >
                            {SUITS[suit].glyph}
                          </span>
                        </span>
                        <p className="text-ink mt-2 text-[0.75rem] leading-tight font-semibold">
                          {concept.name}
                        </p>
                        <p className="text-ink-soft mt-auto text-[0.6875rem] leading-snug">
                          {concept.line}
                        </p>
                      </>
                    ) : (
                      <span className="sr-only">
                        {concept.rank} of {SUITS[suit].label} — not yet won
                      </span>
                    )}
                  </div>
                </motion.li>
              );
            })}
          </ul>
        </section>
      ))}
    </div>
  );
}
