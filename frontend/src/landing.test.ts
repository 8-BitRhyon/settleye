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
    expect(html).toContain("issues/new");
    expect(html).not.toContain("mailto:");
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
  });

  it("carries no countdown or fake urgency", () => {
    expect(html).not.toContain("Submissions close in");
    expect(html).not.toContain('id="clock"');
    expect(html).not.toMatch(/setInterval/);
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

  it("names the model, the frontier comparison, and the anti-customer in Proof", () => {
    expect(html).toContain("modelbar");
    expect(html).toContain("meta-models/muse-spark-open-1026");
    expect(html).toContain("Gemini 4 Argon invented an order number");
    expect(html).toContain("Who this is not for");
  });

  it("keeps problem, steps, demo, proof, objections, pricing, and footer verbatim", () => {
    expect(html).toContain("Phantom refunds");
    expect(html).toContain("Policy breaches");
    expect(html).toContain("Silent cancellations");
    expect(html).toContain(
      "Footnote: chatbot promises create liability (Air Canada, BCCRT 2024). EU AI Act Article 50 transparency duties apply from Aug 2, 2026."
    );
    expect(html).toContain("Connect with test-mode keys");
    expect(html).toContain("Reconcile up to 90 days");
    expect(html).toContain("Ledger reconciliation is deterministic code");
    expect(html).toContain("Refund the exact shortfall");
    expect(html).toContain("Or open the inbox with the sample loaded");
    expect(html).toContain("releases/download/demo-v1/settleye-film.mp4");
    expect(html).toContain("<video");
    expect(html).toContain("?sample=1");
    expect(html).toContain("12 of 12");
    expect(html).toContain("300 / 300");
    expect(html).toContain("0 of 4");
    expect(html).toContain("$44.00");
    expect(html).toContain("4.07 seconds.");
    expect(html).toContain("Single order, not a fleet sample.");
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

describe("conversion path", () => {
  const page = readFileSync(resolve(root, "landing.html"), "utf8");

  it("names who the product is for above the fold", () => {
    expect(page).toMatch(/Built for merchants running an AI agent on 5,000 or more tickets/);
  });

  it("shows live proof before asking for a demo", () => {
    const heroProof = page.indexOf("heroproof");
    const demo = page.indexOf('id="demo"');
    expect(heroProof).toBeGreaterThan(-1);
    expect(heroProof).toBeLessThan(demo);
  });

  it("states the cost of doing nothing with sourced qualifiers", () => {
    expect(page).toContain("$128");
    expect(page).toContain("Mastercard, 2025");
    expect(page).toContain("$4.61");
    expect(page).toContain("LexisNexis, 2025, N=569");
    expect(page).toContain("96 hours");
  });

  it("answers the comparison question honestly, including what we are not", () => {
    expect(page).toContain("What actually catches this today.");
    expect(page).toContain("Helpdesk guardrails");
    expect(page).toContain("Chargeback services");
    expect(page).toContain("Not a guardrail and not a payment rail.");
  });

  it("frames price against a cost the buyer already pays", () => {
    expect(page).toContain("Priced below two chargebacks.");
    expect(page).toContain("Two chargebacks at the average US cost are $256");
  });

  it("removes risk from the pilot and names the exit", () => {
    expect(page).toContain("You keep the leakage ledger either way");
    expect(page).toContain("No write access needed to start");
  });

  it("links every market number to the claim ledger", () => {
    expect(page).toContain("docs/research/20-claims.md");
  });
});

describe("frontier model objection", () => {
  const page = readFileSync(resolve(root, "landing.html"), "utf8");
  const claims = readFileSync(
    resolve(root, "../docs/research/20-claims.md"),
    "utf8",
  );

  it("answers the frontier objection before any other", () => {
    const frontier = page.indexOf("Can't a frontier model just do this?");
    const better = page.indexOf("Why not just switch to a better agent?");
    expect(frontier).toBeGreaterThan(-1);
    expect(frontier).toBeLessThan(better);
  });

  it("puts the comparison on the first screen and the measurement in Proof", () => {
    expect(page).toContain("Only one of them invented an order id");
    expect(page).toContain("Gemini 4 Argon invented an order number");
    expect(page).toContain("We ran the comparison rather than argue it");
    expect(page).toContain("docs/research/21-model-comparison.md");
  });

  it("quotes a measured per-transcript cost instead of a multiple", () => {
    expect(page).toContain("$0.0096");
    expect(page).not.toMatch(/\b\d{2,}x cheaper\b/);
    expect(page).not.toContain("10x");
    expect(page).not.toContain("100x");
  });

  it("concedes that cheaper models drop fields rather than overclaiming", () => {
    expect(page).toContain("Cheaper models exist. They drop fields.");
  });

  it("carries the pricing scope and the Haiku inversion in the claim ledger", () => {
    expect(claims).toContain("Claude Haiku 5.5");
    expect(claims).toMatch(/do not claim to beat it/i);
  });
});
