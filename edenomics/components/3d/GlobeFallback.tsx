import { EXCHANGES } from "@/lib/data/exchanges";
import { latLngToVector } from "@/lib/geo";

/**
 * Shown while the WebGL scene loads, and permanently where WebGL is
 * unavailable or the visitor has asked for reduced motion. Same data, same
 * geometry — just projected flat and held still.
 */
export function GlobeFallback({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center justify-center ${className}`}>
      <svg
        viewBox="-1.25 -1.25 2.5 2.5"
        className="h-full max-h-[440px] w-full max-w-[440px]"
        role="img"
        aria-label="Globe showing the five market centres Edenomics tracks"
      >
        <defs>
          <radialGradient id="globe-fill" cx="38%" cy="32%" r="78%">
            <stop offset="0%" stopColor="#1a1e26" />
            <stop offset="100%" stopColor="#0b0d11" />
          </radialGradient>
        </defs>

        <circle r="1" fill="url(#globe-fill)" stroke="rgba(255,255,255,0.1)" strokeWidth="0.006" />

        {/* Graticule */}
        {[-60, -30, 0, 30, 60].map((lat) => (
          <ellipse
            key={lat}
            cx="0"
            cy={-Math.sin((lat * Math.PI) / 180)}
            rx={Math.cos((lat * Math.PI) / 180)}
            ry={Math.cos((lat * Math.PI) / 180) * 0.16}
            fill="none"
            stroke="rgba(255,255,255,0.07)"
            strokeWidth="0.005"
          />
        ))}
        {[0, 30, 60, 90, 120, 150].map((lng) => (
          <ellipse
            key={lng}
            rx={Math.abs(Math.cos((lng * Math.PI) / 180))}
            ry="1"
            fill="none"
            stroke="rgba(255,255,255,0.07)"
            strokeWidth="0.005"
          />
        ))}

        {EXCHANGES.map((market) => {
          const [x, y, z] = latLngToVector(market.lat, market.lng, 1);
          // Only draw the hemisphere facing the viewer.
          if (z < 0) return null;
          return (
            <g key={market.id}>
              <circle cx={x} cy={-y} r="0.05" fill="var(--color-accent)" opacity="0.16" />
              <circle cx={x} cy={-y} r="0.018" fill="var(--color-accent)" />
            </g>
          );
        })}
      </svg>
    </div>
  );
}
