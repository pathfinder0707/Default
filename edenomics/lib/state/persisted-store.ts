/**
 * A tiny localStorage-backed store designed for useSyncExternalStore.
 *
 * Why not useState + useEffect: reading storage in an effect means rendering
 * the default first and then immediately re-rendering with the stored value.
 * useSyncExternalStore is built for exactly this — the server snapshot is used
 * for SSR *and* hydration, then React switches to the live snapshot once the
 * subscription is in place. It also gives cross-tab sync for free.
 */
export interface PersistedStore<T> {
  subscribe: (listener: () => void) => () => void;
  getSnapshot: () => T;
  getServerSnapshot: () => T;
  set: (updater: (current: T) => T) => void;
}

export function createPersistedStore<T>(
  key: string,
  fallback: T,
  /** Returns null when the stored value is missing or malformed. */
  revive: (raw: unknown) => T | null,
): PersistedStore<T> {
  let value = fallback;
  let loaded = false;
  const listeners = new Set<() => void>();

  function load() {
    if (loaded) return;
    loaded = true;
    try {
      const raw = window.localStorage.getItem(key);
      if (raw !== null) {
        const revived = revive(JSON.parse(raw));
        if (revived !== null) value = revived;
      }
    } catch {
      // Private browsing, blocked storage or corrupt JSON — keep the fallback.
    }
  }

  function emit() {
    for (const listener of listeners) listener();
  }

  return {
    subscribe(listener) {
      // Runs from an effect, which makes it the right place to touch storage.
      load();
      listeners.add(listener);

      const onStorage = (event: StorageEvent) => {
        if (event.key !== key) return;
        loaded = false;
        load();
        emit();
      };
      window.addEventListener("storage", onStorage);

      return () => {
        listeners.delete(listener);
        window.removeEventListener("storage", onStorage);
      };
    },

    getSnapshot: () => value,
    getServerSnapshot: () => fallback,

    set(updater) {
      const next = updater(value);
      if (next === value) return;
      value = next;
      try {
        window.localStorage.setItem(key, JSON.stringify(next));
      } catch {
        // Persistence is a convenience here, never a requirement.
      }
      emit();
    },
  };
}
