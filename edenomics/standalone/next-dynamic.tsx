"use client";

import { Suspense, lazy, type ComponentType } from "react";

/**
 * Stands in for `next/dynamic` in the standalone build.
 *
 * The single-file bundle has nothing to fetch a chunk from, so the deferral
 * becomes a React.lazy boundary instead of a network one. The section that
 * uses it still gates on an IntersectionObserver, so the WebGL scene is
 * created only when it is scrolled to — same behaviour, one less round trip.
 */
export default function dynamic<P extends object>(
  loader: () => Promise<{ default: ComponentType<P> }>,
): ComponentType<P> {
  const Loaded = lazy(loader);
  return function DynamicComponent(props: P) {
    return (
      <Suspense fallback={null}>
        <Loaded {...props} />
      </Suspense>
    );
  };
}
