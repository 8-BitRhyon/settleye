import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const html = readFileSync(resolve(root, "landing.html"), "utf8");
const css = readFileSync(resolve(root, "src/landing.css"), "utf8");
const eye = readFileSync(resolve(root, "src/landing-eye.ts"), "utf8");
const pkg = readFileSync(resolve(root, "package.json"), "utf8");

describe("landing page contract", () => {
  it("declares language and title", () => {
    expect(html).toContain('<html lang="en">');
    expect(html).toMatch(/<title>[^<]+<\/title>/);
  });

  it("has one h1 with the 10-second hook", () => {
    const h1s = html.match(/<h1[^>]*>/g) ?? [];
    expect(h1s).toHaveLength(1);
    expect(html).toContain("Did the money move?");
  });

  it("exposes the Demo, Proof, and Pricing anchors", () => {
    for (const id of ["demo", "proof", "pricing"]) {
      expect(html).toContain(`id="${id}"`);
    }
  });

  it("loads fonts without render blocking and sets theme color", () => {
    expect(html).toContain("display=swap");
    expect(html).toContain('name="theme-color"');
  });

  it("contains zero emoji", () => {
    expect(html).not.toMatch(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u);
  });

  it("links every CTA to a real target", () => {
    expect(html).not.toContain('href="#"');
  });

  it("shows a decorative third eye beside the final CTA with real adjacent text", () => {
    expect(html).toMatch(/<div class="third-eye" aria-hidden="true">/);
    expect(html).toContain("Every promise, reconciled against the ledger.");
  });

  it("bundles the 3D eye through Vite with no CDN script", () => {
    expect(html).toContain(
      '<script type="module" src="/src/landing-eye.ts"></script>',
    );
    expect(html).not.toMatch(/<script[^>]+src="https?:\/\//);
    expect(pkg).toContain('"three"');
  });

  it("lazy-inits the eye on CTA visibility and disposes it off-screen", () => {
    expect(eye).toContain("IntersectionObserver");
    expect(eye).toContain('import("three")');
    expect(eye).toContain("renderer.dispose()");
    expect(eye).toContain("cancelAnimationFrame");
  });

  it("caps pixel ratio, hides the canvas from AT, and paints the pine iris", () => {
    expect(eye).toContain("Math.min(window.devicePixelRatio || 1, 1.5)");
    expect(eye).toContain('setAttribute("aria-hidden", "true")');
    expect(eye).toContain("047857");
  });

  it("keeps the CSS eye as fallback for reduced motion and WebGL failure", () => {
    expect(eye).toContain("(prefers-reduced-motion: reduce)");
    expect(eye).toContain("WebGLRenderer");
    expect(css).toContain(".third-eye__canvas");
  });

  it("blinks the third eye on a 5 to 7 second CSS cycle with a slow glow pulse", () => {
    expect(css).toContain("@keyframes third-eye-blink");
    expect(css).toContain("@keyframes third-eye-glow");
    expect(css).toMatch(/animation:\s*third-eye-blink\s+6s/);
    expect(css).toContain("#047857");
  });

  it("pins the reference restyle: star glint, bold lash, and enlarged iris", () => {
    expect(eye).toContain("makeStarTexture");
    expect(eye).toContain("CatmullRomCurve3");
    expect(eye).toContain("TubeGeometry(lashCurve, 32, 0.055");
    expect(eye).toContain("0, 0.6)");
    expect(eye).toContain("0, 0.265)");
  });

  it("mirrors the star and lash in the calm CSS fallback", () => {
    expect(css).toContain(".third-eye__pupil::before");
    expect(css).toContain("clip-path: polygon(");
    expect(css).toContain(".third-eye__ball::after");
    expect(css).toContain("border-top: 0.65rem solid #08080a");
  });

  it("layers static film grain over the hero only", () => {
    expect(html).toContain('class="hero-grain"');
    expect(html).toContain('<div aria-hidden="true" class="hero-grain">');
    expect(css).toContain(".hero-grain");
    expect(css).toContain("feTurbulence");
    expect(css).toMatch(/\.hero-grain[\s\S]*?opacity:\s*0\.0[0-5]/);
    expect(css).toMatch(/\.hero-grain[\s\S]*?pointer-events:\s*none/);
  });

  it("centers two slow orbit rings on the product mock in pine and gold", () => {
    expect(html).toContain('class="hero-rings"');
    expect(html).toContain("hero-ring--pine");
    expect(html).toContain("hero-ring--gold");
    expect(html).toMatch(/<svg[^>]*hero-ring[^>]*>[\s\S]*?<circle[^>]*#047857/);
    expect(html).toMatch(/<svg[^>]*hero-ring[^>]*>[\s\S]*?<circle[^>]*#b45309/);
    expect(css).toContain("@keyframes hero-ring-spin");
    expect(css).toContain("@keyframes hero-ring-spin-reverse");
    expect(css).toMatch(/90s/);
    expect(css).toMatch(/140s/);
  });

  it("stops the orbit rings under reduced motion while grain stays static", () => {
    const reduced = css.slice(css.indexOf("@media (prefers-reduced-motion: reduce)"));
    expect(reduced).toContain(".hero-ring");
    expect(reduced).toMatch(/animation:\s*none\s*!important/);
  });

  it("renders a full-viewport Eclipse hero with a canvas-free gradient wash", () => {
    expect(html).toContain("hero-eclipse");
    expect(html).toContain("min-h-svh");
    expect(html).not.toContain("data-bg");
    expect(html).not.toContain("dvklab");
    expect(html).not.toMatch(/<script[^>]+src="https?:\/\//);
    expect(css).toContain(".hero-eclipse");
    expect(css).toMatch(/min-height:\s*100svh/);
    expect(css).toContain(".hero-glow");
    expect(css).toMatch(/radial-gradient/);
  });

  it("staggers a blur rise-in entrance with per-item delays", () => {
    expect(html).toContain('class="rise');
    expect(html).toMatch(/style="--d:\s*0\.05s"/);
    expect(html).toMatch(/style="--d:\s*0\.36s"/);
    expect(css).toContain(".rise");
    expect(css).toContain("@keyframes rise-in");
    expect(css).toMatch(/animation-delay:\s*var\(--d/);
    expect(css).toContain("blur(8px)");
    expect(css).toContain("translateY(18px)");
  });

  it("parks the rise-in at full opacity under reduced motion", () => {
    const reduced = css.slice(css.indexOf("@media (prefers-reduced-motion: reduce)"));
    expect(reduced).toContain(".rise");
    expect(reduced).toMatch(/animation:\s*none\s*!important/);
    expect(reduced).toMatch(/opacity:\s*1\s*!important/);
  });

  it("shows a static mono tabular readout with only measured numbers", () => {
    expect(html).toContain("hero-readout");
    expect(html).toContain("$44.00 at risk");
    expect(html).toContain("12/12 verdicts");
    expect(html).not.toMatch(/setInterval/);
    // The single setTimeout on the page belongs to the copy-button label
    // flip (1.4s); the readout itself has no timers.
    expect(html.match(/setTimeout/g)?.length).toBe(1);
    expect(css).toContain(".hero-readout");
    expect(css).toMatch(/tabular-nums/);
  });

  it("pins the Nimbus status pill with the verified check count", () => {
    expect(html).toContain("CI green - 105 checks passing");
    expect(html).toMatch(/<span[^>]*font-mono[^>]*>CI green - 105 checks passing<\/span>/);
    expect(html).toMatch(/CI green - 105 checks passing[\s\S]*?tabular-nums|tabular-nums[\s\S]*?CI green - 105 checks passing/);
  });

  it("shows a noscript-safe clone command with a JS-only copy button", () => {
    expect(html).toContain("git clone github.com/8-BitRhyon/settleye");
    expect(html).toContain("data-copy-btn");
    expect(html).toContain('data-clone-command="git clone github.com/8-BitRhyon/settleye"');
    expect(html).toContain("js-only");
    expect(html).toMatch(/<code[^>]*>git clone github\.com\/8-BitRhyon\/settleye<\/code>/);
    expect(html).toMatch(/>\s*Copy\s*</);
  });

  it("copies via one tiny inline module script with a 1.4s label flip", () => {
    expect(html).toMatch(/<script type="module">[\s\S]*?navigator\.clipboard\.writeText[\s\S]*?<\/script>/);
    expect(html).toContain('"Copied"');
    expect(html).toContain("1400");
    expect(html).toContain('classList.add("js-only")');
    expect(html).not.toMatch(/<script[^>]+src="https?:\/\//);
  });

  it("has no count-up stats anywhere", () => {
    expect(html).not.toMatch(/count-up/i);
    expect(html).not.toMatch(/data-count/i);
    expect(html).not.toMatch(/data-animate/i);
  });

  it("keeps our copy, type system, and section order with no foreign fonts", () => {
    expect(html).toContain("Your AI agent promised a refund.");
    expect(html).toContain("Did the money move?");
    expect(html).toContain("Run a free 14-day shadow audit");
    expect(html).toContain("Watch the 3-minute demo");
    expect(html).toContain("font-display");
    expect(html).not.toContain("Fraunces");
    expect(html).not.toContain("Manrope");
    expect(css).toContain("Chakra Petch");
    expect(css).toContain("IBM Plex Mono");
    const order = ["hero-heading", "problem-heading", "how-heading", "demo", "proof", "objections-heading", "pricing", "audit"];
    const positions = order.map((id) => html.indexOf(`id="${id}"`));
    for (const pos of positions) {
      expect(String(pos)).toMatch(/^[0-9]+$/);
    }
    const sorted = [...positions].sort((a, b) => a - b);
    expect(positions).toHaveLength(sorted.length);
    expect(positions.join(",")).toContain(sorted.join(","));
  });

  it("wraps only the accent words in an italic serif em", () => {
    expect(html).toContain('<em class="hero-accent">Did the money move?</em>');
    expect(html).not.toContain('<span class="hero-accent">');
    expect(css).toContain(".hero-accent");
    expect(css).toContain("Instrument Serif");
    expect(css).toMatch(/\.hero-accent[\s\S]*?font-style:\s*italic/);
    expect(css).toMatch(/\.hero-accent[\s\S]*?font-weight:\s*400/);
    expect(css).toMatch(/\.hero-accent[\s\S]*?Georgia/);
  });

  it("loads only the single Instrument Serif 400-italic weight", () => {
    expect(html).toContain("Instrument+Serif");
    expect(html).toContain("ital,wght@1,400");
    expect(html.match(/Instrument\+Serif/g)?.length).toBe(1);
    expect(html).toContain("Chakra+Petch:wght@600;700");
    expect(html).toContain("IBM+Plex+Mono:wght@400;500;600");
    expect(html).toContain("display=swap");
  });

  it("glows an eclipse disc edge behind the right side with no layout shift", () => {
    expect(html).toContain('<div aria-hidden="true" class="hero-glow absolute inset-0">');
    expect(css).toContain(".hero-glow");
    expect(css).toMatch(/\.hero-glow[\s\S]*?position:\s*absolute/);
    expect(css).toMatch(/\.hero-glow[\s\S]*?inset:\s*0/);
    expect(css).toMatch(/\.hero-glow[\s\S]*?pointer-events:\s*none/);
    expect(css).toMatch(/\.hero-glow[\s\S]*?radial-gradient/);
    expect(css).toContain("rgba(4, 120, 87,");
    expect(css).toContain("rgba(19, 19, 22,");
    expect(css).toContain("rgba(180, 83, 9,");
    expect(css).toMatch(/\.hero-glow[\s\S]*?at (7\d|8\d)%/);
  });
});
