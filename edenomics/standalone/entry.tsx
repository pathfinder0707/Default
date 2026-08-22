import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import Home from "@/app/page";

/**
 * Entry point for the standalone single-file build (see
 * scripts/build-standalone.mjs). The Next app renders the same tree on the
 * server; here it is mounted client-side into a prepainted shell.
 */
const container = document.getElementById("edenomics-root");
if (container) {
  createRoot(container).render(
    <StrictMode>
      <Home />
    </StrictMode>,
  );
  container.dataset.ready = "true";
}
