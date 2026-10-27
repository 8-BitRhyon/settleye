import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const html = readFileSync(resolve(root, "landing.html"), "utf8");

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
});
