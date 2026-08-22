import { Container, SectionHeading } from "@/components/layout/Section";
import { Reveal } from "@/components/ui/Reveal";
import { StreakPanel } from "@/components/learn/StreakPanel";
import { ChallengeCard } from "@/components/learn/ChallengeCard";

export function LearnSection() {
  return (
    <section id="learn" className="py-14 sm:py-18 lg:py-24">
      <Container>
        <SectionHeading
          eyebrow="Daily challenge"
          title={
            <>
              Learn finance
              <br />
              <span className="text-muted">without studying finance.</span>
            </>
          }
          description="Three questions a day, roughly a minute. Every one of them explains itself the moment you answer, right or wrong."
          className="mb-10"
        />

        <div className="grid gap-5 lg:grid-cols-12">
          <Reveal className="lg:col-span-4">
            <StreakPanel />
          </Reveal>
          <Reveal delay={0.08} className="lg:col-span-8">
            <ChallengeCard />
          </Reveal>
        </div>
      </Container>
    </section>
  );
}
