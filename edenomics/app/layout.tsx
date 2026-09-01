import type { Metadata, Viewport } from "next";
import { Bodoni_Moda, Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const display = Bodoni_Moda({
  variable: "--font-bodoni",
  subsets: ["latin"],
  display: "swap",
});

const sans = Geist({ variable: "--font-geist", subsets: ["latin"], display: "swap" });
const mono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
  title: "Edenomics — how sure are you?",
  description:
    "A card game about money where you don't pick an answer, you flick a card — and how hard you flick it is your confidence. Scored on calibration, so the only way to win is to be honest about what you don't know.",
  applicationName: "Edenomics",
  openGraph: {
    title: "Edenomics — how sure are you?",
    description:
      "Flick the card. How hard you flick it is your confidence. Scored on calibration, not luck.",
    siteName: "Edenomics",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#0A1411",
  colorScheme: "dark",
  // The table is a fixed surface; letting it bounce breaks the illusion.
  maximumScale: 1,
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${sans.variable} ${mono.variable} h-full antialiased`}
    >
      <body className="bg-felt text-cream min-h-full">{children}</body>
    </html>
  );
}
