import { Container } from "@/components/layout/Section";
import { StoryCard } from "@/components/news/StoryCard";
import { BriefDateline, BriefGreeting } from "@/components/news/BriefGreeting";
import { Reveal } from "@/components/ui/Reveal";
import { STORIES, totalReadTime } from "@/lib/data/stories";

/**
 * Five stories, sized unevenly on purpose: the lead earns more space, and the
 * rest sit beside it. On phones the same set becomes a swipeable rail.
 */
const SPANS = [
  "md:col-span-12 lg:col-span-7 lg:row-span-2",
  "md:col-span-6 lg:col-span-5",
  "md:col-span-6 lg:col-span-5",
  "md:col-span-6",
  "md:col-span-6",
];

export function DailyBrief() {
  return (
    <section id="today" className="py-14 sm:py-18 lg:py-24">
      <Container>
        <Reveal
          as="header"
          className="mb-10 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between lg:mb-12"
        >
          <BriefGreeting count={STORIES.length} />
          <div className="flex shrink-0 flex-col gap-1 sm:items-end">
            <BriefDateline />
            <span className="text-faint font-mono text-[0.6875rem] tracking-wide">
              {totalReadTime()} to read all of it
            </span>
          </div>
        </Reveal>

        <div className="rail rail-mask -mx-5 flex snap-x snap-mandatory gap-4 overflow-x-auto px-5 pb-2 sm:-mx-8 sm:px-8 md:mx-0 md:grid md:grid-cols-12 md:snap-none md:overflow-visible md:px-0 md:pb-0 lg:gap-5">
          {STORIES.map((story, index) => (
            <div
              key={story.id}
              className={`w-[85vw] shrink-0 snap-start sm:w-[70vw] md:w-auto md:shrink ${SPANS[index] ?? "md:col-span-6"}`}
            >
              <StoryCard
                story={story}
                variant={index === 0 ? "lead" : "standard"}
                className="h-full"
              />
            </div>
          ))}
        </div>

        <p className="text-faint mt-4 text-center font-mono text-[0.625rem] tracking-wide md:hidden">
          Swipe for the rest of today
        </p>
      </Container>
    </section>
  );
}
