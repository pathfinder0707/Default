import type { Metadata, Viewport } from "next";
import { Bricolage_Grotesque, Plus_Jakarta_Sans, Geist_Mono } from "next/font/google";
import "./globals.css";

const display = Bricolage_Grotesque({
  variable: "--font-bricolage",
  subsets: ["latin"],
  display: "swap",
});

const sans = Plus_Jakarta_Sans({
  variable: "--font-jakarta",
  subsets: ["latin"],
  display: "swap",
});

const mono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Edenomics — the daily money game",
  description:
    "Five rounds a day. Learn how money actually moves by playing the market, not guessing it. Streaks, XP, a skill constellation and a portfolio you unlock by understanding it.",
  applicationName: "Edenomics",
  openGraph: {
    title: "Edenomics — the daily money game",
    description:
      "Five rounds a day. Learn how money actually moves by playing the market, not guessing it.",
    siteName: "Edenomics",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#0D0B1A",
  colorScheme: "dark",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${sans.variable} ${mono.variable} h-full antialiased`}
    >
      <body className="bg-void text-fg min-h-full">{children}</body>
    </html>
  );
}
