import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono, Instrument_Serif } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

const instrumentSerif = Instrument_Serif({
  variable: "--font-instrument",
  subsets: ["latin"],
  weight: "400",
  style: ["normal", "italic"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Edenomics — Know what matters in money",
  description:
    "Markets, companies and financial news, distilled into a few minutes a day. Follow what you care about and Edenomics tells you when something actually matters.",
  applicationName: "Edenomics",
  openGraph: {
    title: "Edenomics — Know what matters in money",
    description:
      "Markets, companies and financial news, distilled into a few minutes a day.",
    siteName: "Edenomics",
    type: "website",
  },
};

export const viewport: Viewport = {
  themeColor: "#08090B",
  colorScheme: "dark",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${instrumentSerif.variable} h-full antialiased`}
    >
      <body className="bg-ink text-fg min-h-full">{children}</body>
    </html>
  );
}
