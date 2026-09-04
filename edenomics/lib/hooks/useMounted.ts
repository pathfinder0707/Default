"use client";

import { useSyncExternalStore } from "react";

const noopSubscribe = () => () => {};

/**
 * False during server render and hydration, true afterwards.
 *
 * Anything derived from the visitor's clock or locale has to wait for this,
 * otherwise the server renders one value and the client another. Built on
 * useSyncExternalStore so it never schedules a second render pass of its own.
 */
export function useMounted(): boolean {
  return useSyncExternalStore(
    noopSubscribe,
    () => true,
    () => false,
  );
}
