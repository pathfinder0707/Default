import { SiteHeader } from "@/components/layout/SiteHeader";
import { MobileTabBar } from "@/components/layout/MobileTabBar";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { Principles } from "@/components/layout/Principles";
import { FinalCta } from "@/components/layout/FinalCta";
import { Hero } from "@/components/game/Hero";
import { PlayerHq } from "@/components/player/PlayerHq";
import { SkillMap } from "@/components/skills/SkillMap";
import { PortfolioLab } from "@/components/portfolio/PortfolioLab";
import { LeagueTable } from "@/components/league/LeagueTable";

export default function Home() {
  return (
    <div id="top">
      <SiteHeader />
      <main>
        <Hero />
        <PlayerHq />
        <SkillMap />
        <PortfolioLab />
        <LeagueTable />
        <Principles />
        <FinalCta />
      </main>
      <SiteFooter />
      <MobileTabBar />
    </div>
  );
}
