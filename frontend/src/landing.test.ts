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

  it("exposes the Demo, Proof, Pricing, and Audit anchors", () => {
    for (const id of ["demo", "proof", "pricing", "audit"]) {
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
    expect(html).toContain("github.com/8-BitRhyon/settleye");
    expect(html).toContain("pilot@settleye.com");
  });

  it("contains zero Umbra or climate words", () => {
    expect(html).not.toMatch(/umbra/i);
    expect(html).not.toMatch(/climate/i);
  });

  it("keeps the reference hero mechanics", () => {
    expect(html).toContain("canvas data-bg");
    expect(html).toContain('id="orbit"');
    expect(html).toContain("@keyframes spin");
    expect(html).toContain("@keyframes rise");
    expect(html).toContain("Fraunces");
    expect(html).toContain("Manrope");
    expect(html).toContain("JetBrains Mono");
    expect(html).toContain("Submissions close in");
    expect(html).toContain('id="clock"');
    expect(html).toContain("setInterval");
  });

  it("retargets the countdown to the Nov 4 hackathon deadline", () => {
    expect(html).toContain("2026-11-04");
    expect(html).toMatch(/Nov 4/i);
  });

  it("loads only local scripts and preloads the poster", () => {
    expect(html).not.toMatch(/<script[^>]+src="https?:\/\//);
    expect(html).toContain('src="vendor/eclipse/bg.js"');
    expect(html).toContain('rel="preload"');
    expect(html).toContain("vendor/eclipse/scene.jpg");
  });

  it("ports every section in order below the hero", () => {
    const order = [
      'id="problem"',
      'id="how"',
      'id="demo"',
      'id="proof"',
      'id="objections"',
      'id="pricing"',
      'id="audit"',
    ];
    const positions = order.map((id) => html.indexOf(id));
    for (const pos of positions) {
      expect(pos).toBeGreaterThan(-1);
    }
    const sorted = [...positions].sort((a, b) => a - b);
    expect(positions).toEqual(sorted);
  });

  it("keeps problem, steps, demo, proof, objections, pricing, and footer verbatim", () => {
    expect(html).toContain("Phantom refunds");
    expect(html).toContain("Policy breaches");
    expect(html).toContain("Silent cancellations");
    expect(html).toContain(
      "Footnote: chatbot promises create liability (Air Canada, BCCRT 2024). EU AI Act Article 50 transparency duties apply from Aug 2, 2026."
    );
    expect(html).toContain("Start read-only");
    expect(html).toContain("We audit your sample");
    expect(html).toContain("Deterministic ledger reconciliation");
    expect(html).toContain("Fix in one click");
    expect(html).toContain("3-minute demo (recording in progress)");
    expect(html).toContain("12 of 12");
    expect(html).toContain("$44.00");
    expect(html).toContain("4.07 seconds.");
    expect(html).toContain("Why not just switch to a better agent?");
    expect(html).toContain("Is the model decorative?");
    expect(html).toContain("$299/mo");
    expect(html).toContain("$999/mo");
    expect(html).toContain("Enterprise custom. SOC 2 is on the roadmap");
    expect(html).toContain("Stop finding phantom refunds in chargebacks.");
    expect(html).toContain("Built with Muse Spark Open");
    expect(html).toContain("meta-models/muse-spark-open-1026");
  });
});
