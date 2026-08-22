import { ArrowRight } from "lucide-react";
import { Container } from "@/components/layout/Section";
import { Reveal } from "@/components/ui/Reveal";
import { ButtonLink } from "@/components/ui/Button";

export function FinalCta() {
  return (
    <section className="grain relative overflow-hidden py-20 sm:py-24 lg:py-28">
      <div
        aria-hidden
        className="pointer-events-none absolute bottom-[-30%] left-1/2 h-[420px] w-[820px] -translate-x-1/2 rounded-full opacity-[0.11] blur-[120px]"
        style={{
          background: "radial-gradient(closest-side, var(--color-accent), transparent 70%)",
        }}
      />
      <Container className="relative">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 className="display text-[2.4rem] leading-[1.05] sm:text-[3.4rem]">
            Your financial world
            <br />
            in five minutes.
          </h2>
          <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
            <ButtonLink href="#today" size="lg">
              Start your daily brief
              <ArrowRight size={16} aria-hidden />
            </ButtonLink>
          </div>
          <p className="text-faint mt-6 text-[0.8125rem]">
            Free to start. One email a day, only if you want it.
          </p>
        </Reveal>
      </Container>
    </section>
  );
}
