import type { ExchangeMarket } from "@/lib/types";

/**
 * The five sessions that between them cover the trading day. Coordinates are
 * real — the globe places its markers from these, and the session clock
 * derives open/closed state from the time zone and hours below.
 */
export const EXCHANGES: ExchangeMarket[] = [
  {
    id: "mumbai",
    city: "Mumbai",
    country: "India",
    indexName: "NIFTY 50",
    indexValue: "24,842",
    changePct: 0.84,
    lat: 19.076,
    lng: 72.8777,
    timeZone: "Asia/Kolkata",
    opens: 9.25,
    closes: 15.5,
  },
  {
    city: "New York",
    id: "new-york",
    country: "United States",
    indexName: "S&P 500",
    indexValue: "5,620",
    changePct: 0.41,
    lat: 40.7128,
    lng: -74.006,
    timeZone: "America/New_York",
    opens: 9.5,
    closes: 16,
  },
  {
    id: "london",
    city: "London",
    country: "United Kingdom",
    indexName: "FTSE 100",
    indexValue: "8,411",
    changePct: -0.12,
    lat: 51.5072,
    lng: -0.1276,
    timeZone: "Europe/London",
    opens: 8,
    closes: 16.5,
  },
  {
    id: "tokyo",
    city: "Tokyo",
    country: "Japan",
    indexName: "Nikkei 225",
    indexValue: "42,180",
    changePct: 1.1,
    lat: 35.6762,
    lng: 139.6503,
    timeZone: "Asia/Tokyo",
    opens: 9,
    closes: 15,
  },
  {
    id: "shanghai",
    city: "Shanghai",
    country: "China",
    indexName: "SSE Composite",
    indexValue: "3,486",
    changePct: 0.28,
    lat: 31.2304,
    lng: 121.4737,
    timeZone: "Asia/Shanghai",
    opens: 9.5,
    closes: 15,
  },
];
