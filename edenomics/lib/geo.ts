import { LAND_MASK_BASE64, LAND_POINT_COUNT } from "@/lib/data/land-mask";

const DEG = Math.PI / 180;
const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));

/**
 * Standard globe mapping: latitude/longitude to a point on a sphere with the
 * prime meridian facing the camera at rotation zero. Used for both the land
 * dots and the city markers so the two can never drift apart.
 */
export function latLngToVector(lat: number, lng: number, radius = 1): [number, number, number] {
  const phi = (90 - lat) * DEG;
  const theta = (lng + 180) * DEG;
  return [
    -radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.cos(phi),
    radius * Math.sin(phi) * Math.sin(theta),
  ];
}

/** Rotation that brings a coordinate round to face the camera. */
export function facingRotation(lat: number, lng: number): { x: number; y: number } {
  return { x: lat * DEG, y: Math.PI / 2 - (lng + 180) * DEG };
}

function decodeMask(base64: string): Uint8Array {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

/**
 * Rebuilds the land point cloud from the generated bitmask.
 *
 * The positions themselves are never shipped — they are re-derived from the
 * same Fibonacci sequence the generator used, so the payload is one bit per
 * candidate point instead of three floats.
 */
export function landPositions(radius = 1.004): Float32Array {
  const mask = decodeMask(LAND_MASK_BASE64);
  const points: number[] = [];

  for (let i = 0; i < LAND_POINT_COUNT; i++) {
    if (!(mask[i >> 3] & (1 << (i & 7)))) continue;

    const y = 1 - (i / (LAND_POINT_COUNT - 1)) * 2;
    const lat = Math.asin(y) / DEG;
    let lng = (((GOLDEN_ANGLE * i) / DEG) % 360) - 180;
    if (lng < -180) lng += 360;

    points.push(...latLngToVector(lat, lng, radius));
  }

  return new Float32Array(points);
}
