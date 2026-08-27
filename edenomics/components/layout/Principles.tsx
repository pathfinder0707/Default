import { Brain, HandCoins, MessageSquareQuote, ShieldCheck } from "lucide-react";
import { Container, SectionHeading } from "@/components/layout/Section";
import { Reveal } from "@/components/ui/Reveal";

/**
 * The rules the game is built to. Stated plainly, because "gamified finance"
 * is one small step from a slot machine and the difference is entirely in
 * which behaviours get rewarded.
 */
const RULES = [
  {
    icon: Brain,
    title: "You score on reasoning",
    body: "Never on direction. Every round can be won by someone who has no idea where the market is going and lost by someone who guessed right.",
  },
  {
    icon: ShieldCheck,
    title: "No leverage, no day trading",
    body: "Nothing in the lab settles faster than a week. A game that rewarded quick trading would be training the exact habit that costs people money.",
  },
  {
    icon: MessageSquareQuote,
    title: "Wrong answers explain themselves",
    body: "The lesson appears whether you got it right or not, and so does the reason the other options were wrong. That is the product; the score is just what brings you back.",
  },
  {
    icon: HandCoins,
    title: "Nothing is for sale",
    body: "No streak repairs, no XP boosts, no premium hints. Every badge on your shelf is something you did rather than something you bought.",
  },
];

export function Principles() {
  return (
    <section className="border-line grain clip-decor relative border-y bg-black/25 py-14 sm:py-20">
      <Container className="relative">
        <SectionHeading
          eyebrow="How this is built"
          title={
            <>
              Gamified, and
              <br />
              <span className="text-muted">deliberately not a casino.</span>
            </>
          }
          description="Making finance addictive is easy and mostly harmful. These are the four rules that decide what Edenomics rewards."
          className="mb-9"
        />

        <ul className="grid gap-4 sm:grid-cols-2">
          {RULES.map((rule, index) => {
            const Icon = rule.icon;
            return (
              <Reveal as="li" key={rule.title} delay={index * 0.06}>
                <div className="piece h-full rounded-3xl p-6">
                  <span className="bg-brand/15 text-brand mb-4 inline-flex h-11 w-11 items-center justify-center rounded-2xl">
                    <Icon size={20} aria-hidden />
                  </span>
                  <h3 className="font-display text-xl font-bold">{rule.title}</h3>
                  <p className="text-muted mt-2.5 text-[0.9375rem] leading-relaxed">
                    {rule.body}
                  </p>
                </div>
              </Reveal>
            );
          })}
        </ul>
      </Container>
    </section>
  );
}
