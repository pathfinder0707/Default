import { ArrowRight } from "lucide-react";
import { Container } from "@/components/layout/Section";
import { Reveal } from "@/components/ui/Reveal";
import { ButtonLink } from "@/components/ui/Button";

export function FinalCta() {
  return (
    <section className="grain clip-decor relative py-20 sm:py-28">
      <div
        aria-hidden
        className="pointer-events-none absolute bottom-0 left-1/2 h-[300px] w-[760px] -translate-x-1/2 rounded-full opacity-[0.12] blur-[120px]"
        style={{ background: "radial-gradient(closest-side, var(--color-brand), transparent 70%)" }}
      />
      <Container className="relative">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 className="display text-[2.4rem] sm:text-[3.4rem]">
            Three minutes a day
            <br />
            <span className="text-brand">for about a year.</span>
          </h2>
          <p className="text-muted mx-auto mt-5 max-w-md text-[1.0625rem] leading-relaxed">
            That is roughly what it takes to stop finding any of this intimidating.
            It is a shorter road than anyone told you.
          </p>
          <ButtonLink href="#play" size="lg" className="mt-8">
            Play today&rsquo;s run
            <ArrowRight size={18} aria-hidden />
          </ButtonLink>
          <p className="text-faint mt-5 text-[0.8125rem]">
            Free. No account. Your streak lives in this browser.
          </p>
        </Reveal>
      </Container>
    </section>
  );
}
