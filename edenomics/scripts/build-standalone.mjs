/**
 * Builds the whole homepage into one self-contained HTML file.
 *
 * Useful for sharing the prototype as a link or a file — no Node, no server,
 * no install. Everything except the Google Fonts stylesheet is inlined.
 *
 *   node scripts/build-standalone.mjs   ->  dist/edenomics.html
 *
 * The Next app remains the real one: it server-renders, code-splits three.js
 * into its own chunk, and self-hosts fonts. This build trades those for a
 * single portable file.
 */
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, rmSync, writeFileSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import * as esbuild from "esbuild";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const tmp = join(root, ".standalone-tmp");
const outDir = join(root, "dist");
const outFile = join(outDir, "edenomics.html");

mkdirSync(tmp, { recursive: true });
mkdirSync(outDir, { recursive: true });

// 1. Tailwind — same input the Next build uses, so the tokens cannot drift.
console.log("compiling css…");
execFileSync(
  process.execPath,
  [
    join(root, "node_modules/@tailwindcss/cli/dist/index.mjs"),
    "-i",
    join(root, "app/globals.css"),
    "-o",
    join(tmp, "app.css"),
    "--minify",
  ],
  { cwd: root, stdio: ["ignore", "ignore", "inherit"] },
);

// 2. One JS bundle. `next/dynamic` is aliased to a React.lazy shim, since a
//    single file has nowhere to fetch a chunk from.
console.log("bundling js…");
await esbuild.build({
  entryPoints: [join(root, "standalone/entry.tsx")],
  bundle: true,
  format: "iife",
  target: ["es2021"],
  minify: true,
  jsx: "automatic",
  legalComments: "none",
  define: { "process.env.NODE_ENV": '"production"' },
  alias: {
    "@": root,
    "next/dynamic": join(root, "standalone/next-dynamic.tsx"),
  },
  outfile: join(tmp, "app.js"),
  logLevel: "warning",
});


const FONT_CSS_URL =
  "https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&family=Instrument+Serif:ital@0;1&display=swap";

// A desktop UA is what makes Google serve woff2 rather than older formats.
const DESKTOP_UA =
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

/**
 * Pulls the font files down and rewrites them into the stylesheet as data
 * URIs, so the finished page makes no network requests at all. Falls back to
 * a plain stylesheet link if the network is unavailable at build time.
 */
async function inlineFonts() {
  const response = await fetch(FONT_CSS_URL, { headers: { "user-agent": DESKTOP_UA } });
  if (!response.ok) throw new Error(`font css ${response.status}`);
  let css = await response.text();

  // Latin is all this prototype needs; the extended subsets double the weight.
  css = css
    .split("\n")
    .reduce((blocks, line) => {
      if (line.startsWith("/*")) blocks.push({ subset: line, lines: [] });
      else if (blocks.length) blocks[blocks.length - 1].lines.push(line);
      return blocks;
    }, [])
    .filter((block) => /\/\* latin \*\//.test(block.subset))
    .map((block) => block.lines.join("\n"))
    .join("\n");

  const urls = [...new Set(css.match(/https:\/\/fonts\.gstatic\.com\/[^)]+/g) ?? [])];
  let bytes = 0;

  for (const url of urls) {
    const file = await fetch(url);
    if (!file.ok) throw new Error(`font file ${file.status}`);
    const buffer = Buffer.from(await file.arrayBuffer());
    bytes += buffer.length;
    css = css.replaceAll(url, `data:font/woff2;base64,${buffer.toString("base64")}`);
  }

  console.log(`  inlined ${urls.length} font files (${(bytes / 1024).toFixed(0)} KB)`);
  return css;
}

let fontCss = "";
let fontLink = "";
console.log("fetching fonts…");
try {
  fontCss = await inlineFonts();
} catch (error) {
  console.warn(`  could not inline fonts (${error.message}) — linking Google Fonts instead`);
  fontLink = `<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link rel="stylesheet" href="${FONT_CSS_URL}" />`;
}

const css = readFileSync(join(tmp, "app.css"), "utf8");
// A bundle can legitimately contain "</script>" inside a string literal.
const js = readFileSync(join(tmp, "app.js"), "utf8").replace(/<\/script/gi, "<\\/script");

// 3. Compose. No <html>/<head>/<body> — the host page supplies those.
const html = `<title>Edenomics</title>
<meta name="description" content="Markets, companies and financial news, distilled into a few minutes a day." />

${fontLink}
<style>
${fontCss}
</style>

<style>
${css}
</style>

<style>
  /* The Next build injects these three via next/font; here they come from the
     inlined @font-face rules above, with the same fallback stacks. */
  :root {
    --font-geist: "Geist";
    --font-geist-mono: "Geist Mono";
    --font-instrument: "Instrument Serif";
  }

  /* Painted before the bundle parses, so there is never a white flash. */
  #edenomics-boot {
    position: fixed;
    inset: 0;
    display: grid;
    place-items: center;
    background: var(--color-ink, #08090b);
    color: #f5f6f7;
    font-family: var(--font-instrument), Georgia, serif;
    font-size: 1.25rem;
    letter-spacing: -0.01em;
    transition: opacity 0.4s ease;
  }
  #edenomics-root[data-ready="true"] + #edenomics-boot {
    opacity: 0;
    pointer-events: none;
  }
</style>

<div id="edenomics-root"></div>
<div id="edenomics-boot" aria-hidden="true">Edenomics</div>
<noscript>
  <p style="padding:2rem;color:#8d929b;font-family:system-ui,sans-serif">
    Edenomics is an interactive prototype and needs JavaScript to run.
  </p>
</noscript>

<script>
${js}
</script>
`;

writeFileSync(outFile, html, "utf8");
rmSync(tmp, { recursive: true, force: true });

const kb = (statSync(outFile).size / 1024).toFixed(0);
console.log(`wrote dist/edenomics.html — ${kb} KB`);
