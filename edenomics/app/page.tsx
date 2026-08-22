import { SiteHeader } from "@/components/layout/SiteHeader";
import { MobileTabBar } from "@/components/layout/MobileTabBar";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { FinalCta } from "@/components/layout/FinalCta";
import { Hero } from "@/components/news/Hero";
import { DailyBrief } from "@/components/news/DailyBrief";
import { ForYouFeed } from "@/components/watchlist/ForYouFeed";
import { MarketSnapshot } from "@/components/markets/MarketSnapshot";
import { LearnSection } from "@/components/learn/LearnSection";
import { GlobeSection } from "@/components/3d/GlobeSection";
import { WatchlistCta } from "@/components/watchlist/WatchlistCta";

export default function Home() {
  return (
    <>
      <SiteHeader />
      <main>
        <Hero />
        <DailyBrief />
        <ForYouFeed />
        <MarketSnapshot />
        <LearnSection />
        <GlobeSection />
        <WatchlistCta />
        <FinalCta />
      </main>
      <SiteFooter />
      <MobileTabBar />
    </>
  );
}
