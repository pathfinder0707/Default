"use client";

import { useCallback, useSyncExternalStore } from "react";

/**
 * A clock that ticks on an interval, for countdowns that should stay honest
 * while the page is open.
 *
 * The snapshot is the interval bucket rather than the raw timestamp, so it is
 * stable between ticks — which is what useSyncExternalStore requires — and
 * returns null until mounted so the server and client agree.
 */
export function useNow(intervalMs = 60_000): Date | null {
  const subscribe = useCallback(
    (onChange: () => void) => {
      const id = window.setInterval(onChange, intervalMs);
      return () => window.clearInterval(id);
    },
    [intervalMs],
  );

  const getSnapshot = useCallback(
    () => Math.floor(Date.now() / intervalMs),
    [intervalMs],
  );

  const bucket = useSyncExternalStore(subscribe, getSnapshot, () => null);
  return bucket === null ? null : new Date(bucket * intervalMs);
}
