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

  it("kills all third eye animation under reduced motion and leaves it open", () => {
    const reduced = css.slice(css.indexOf("@media (prefers-reduced-motion: reduce)"));
    expect(reduced).toContain(".third-eye");
    expect(reduced).toMatch(/animation:\s*none\s*!important/);
    expect(reduced).toContain(".third-eye__lid");
  });
});
