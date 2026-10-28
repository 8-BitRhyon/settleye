/**
 * Real capture harness. No fakes.
 *
 * Drives the live local stack (backend :8000, frontend :5173) in Chromium:
 * prefilled inbox -> Audit click (real model call) -> drift card ->
 * "Why does this matter?" (real /explain) -> "Issue $45.00 refund" click
 * (real /remediate) -> a real second POST /remediate with the same body
 * (idempotency proof) -> screenshots + receipts.json for the film.
 *
 * Precondition: backend and frontend are already running (see README).
 * If the stack or the model call fails, this script exits non-zero and
 * prints exactly what blocked. It never fabricates a screenshot.
 */
import { chromium } from "playwright";
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const OUT = here;
const FRONTEND = process.env.FILM_FRONTEND_URL || "http://127.0.0.1:5173/";
const BACKEND = process.env.FILM_BACKEND_URL || "http://127.0.0.1:8000";

async function check(url, label) {
  try {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r;
  } catch (e) {
    console.error(`BLOCKED: ${label} not reachable at ${url}: ${e.message}`);
    console.error("Start the stack first (see film/README.md), then re-run npm run capture.");
    process.exit(2);
  }
}

await check(`${BACKEND}/healthz`, "backend");
await check(FRONTEND, "frontend");
console.log("Stack OK: backend /healthz and frontend responded.");

mkdirSync(OUT, { recursive: true });
const manifest = { capturedAt: new Date().toISOString(), frontend: FRONTEND, backend: BACKEND, steps: [] };
const log = (s) => { manifest.steps.push(s); console.log("capture:", s); };

let auditBody = null;
let firstReceipt = null;
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1600, height: 900 } });

page.on("response", async (res) => {
  const url = res.url();
  try {
    if (url.endsWith("/audit") && res.request().method() === "POST") {
      auditBody = await res.json();
      log(`POST /audit -> ${res.status()} drifts=${auditBody.drifts?.length} total_at_risk=${auditBody.total_at_risk_usd}`);
    }
    if (url.endsWith("/remediate") && res.request().method() === "POST" && !firstReceipt) {
      firstReceipt = await res.json();
      log(`POST /remediate (UI click) -> ${res.status()} ${JSON.stringify(firstReceipt)}`);
    }
  } catch { /* body already consumed elsewhere */ }
});

try {
  await page.goto(FRONTEND, { waitUntil: "networkidle", timeout: 30000 });
  // Browser zoom only: real app, enlarged for 1080p legibility.
  await page.evaluate(() => { document.body.style.zoom = "1.25"; });
  await page.getByLabel("Support transcript").waitFor({ timeout: 15000 });
  const prefilled = await page.getByLabel("Support transcript").inputValue();
  if (!prefilled.includes("order #992") || !prefilled.includes("$45")) {
    throw new Error(`Sample transcript not prefilled as expected. Got: ${prefilled.slice(0, 120)}`);
  }
  log("Inbox loaded, sample transcript prefilled (order #992, $45).");
  await page.waitForTimeout(600);
  await page.screenshot({ path: join(OUT, "01-inbox.png") });
  log("01-inbox.png");

  // Audit click: real extraction model call.
  await page.getByRole("button", { name: "Audit transcript" }).click();
  await page.waitForTimeout(700);
  await page.screenshot({ path: join(OUT, "02-auditing.png") }).catch(() => {});
  log("02-auditing.png (in-flight state right after click; may already show results if the model was fast)");
  await page.getByText("State drift").first().waitFor({ timeout: 180000 });
  if (!auditBody) throw new Error("Audit response was not observed on the network.");
  const drift = auditBody.drifts?.[0];
  if (!drift) throw new Error(`Expected at least one drift, audit returned: ${JSON.stringify(auditBody).slice(0, 400)}`);
  log(`Drift confirmed: order=${drift.promise.order_id} at_risk=$${drift.amount_at_risk_usd} ledger="${drift.ledger_summary}"`);

  const article = page.locator("article").first();
  await article.scrollIntoViewIfNeeded();
  await page.waitForTimeout(500);
  await page.screenshot({ path: join(OUT, "03-drift.png") });
  log("03-drift.png");

  // Explain: real /explain model call.
  await page.getByRole("button", { name: "Why does this matter?" }).click();
  // The placeholder is a single ellipsis char; wait until real text replaces it.
  await page.waitForFunction(() => {
    const el = [...document.querySelectorAll("article p")].find((p) => p.className.includes("emerald"));
    return el && el.textContent && el.textContent.trim().length > 12 && el.textContent.trim() !== "…";
  }, { timeout: 180000 });
  const explainText = await page.locator("article p.text-emerald-200").first().textContent().catch(() => "");
  manifest.explainText = explainText?.trim() || "";
  log(`Explain returned: "${manifest.explainText.slice(0, 160)}"`);
  await article.scrollIntoViewIfNeeded();
  await page.waitForTimeout(400);
  await page.screenshot({ path: join(OUT, "04-explain.png") });
  log("04-explain.png");

  // Fix click: real /remediate.
  const valueBefore = await (await fetch(`${BACKEND}/value`)).json();
  manifest.valueBeforeFix = valueBefore;
  await page.getByRole("button", { name: /Issue \$45\.00 refund/ }).click();
  await page.getByText("Verified").first().waitFor({ timeout: 30000 });
  await page.getByText("Recovered $45.00 so far").waitFor({ timeout: 30000 });
  if (!firstReceipt) throw new Error("Remediate response was not observed on the network.");
  manifest.firstReceipt = firstReceipt;
  await page.waitForTimeout(500);
  await page.screenshot({ path: join(OUT, "05-verified.png") });
  log("05-verified.png (card Verified, header Recovered $45.00 so far)");

  // Idempotent re-click: a real second POST /remediate, same body the UI sent.
  // The UI removes the button after a fix, so the re-click is issued at the
  // API level from inside the real browser page and recorded verbatim.
  const valueBeforeSecond = await (await fetch(`${BACKEND}/value`)).json();
  const second = await page.evaluate(async ({ backend, promise, amount }) => {
    const r = await fetch(`${backend}/remediate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ promise, amount_usd: amount }),
    });
    return { status: r.status, body: await r.json() };
  }, { backend: BACKEND, promise: drift.promise, amount: drift.amount_at_risk_usd });
  const valueAfterSecond = await (await fetch(`${BACKEND}/value`)).json();
  manifest.secondReceiptHttpStatus = second.status;
  manifest.valueBeforeSecond = valueBeforeSecond;
  manifest.valueAfterSecond = valueAfterSecond;
  log(` Second POST /remediate -> HTTP ${second.status} ${JSON.stringify(second.body)}`);
  if (second.body.idempotency_key !== firstReceipt.idempotency_key) {
    throw new Error(`Idempotency key changed on re-click: ${second.body.idempotency_key} vs ${firstReceipt.idempotency_key}`);
  }
  if (second.body.status !== "already_executed") {
    throw new Error(`Expected already_executed on re-click, got: ${JSON.stringify(second.body)}`);
  }
  if (JSON.stringify(valueBeforeSecond) !== JSON.stringify(valueAfterSecond)) {
    throw new Error(`Value ledger moved on re-click: ${JSON.stringify(valueBeforeSecond)} -> ${JSON.stringify(valueAfterSecond)}`);
  }
  log("Idempotency proven: same key, already_executed, /value unchanged.");

  const receipts = {
    note: "Real receipts captured from the live backend during film/capture/capture.mjs. First from the UI click, second from a repeat POST with the identical body.",
    first: firstReceipt,
    second: second.body,
    valueBeforeSecond,
    valueAfterSecond,
  };
  writeFileSync(join(OUT, "receipts.json"), JSON.stringify(receipts, null, 2));
  writeFileSync(join(OUT, "audit.json"), JSON.stringify(auditBody, null, 2));
  manifest.ok = true;
} catch (e) {
  manifest.ok = false;
  manifest.error = String(e && e.message ? e.message : e);
  writeFileSync(join(OUT, "capture.json"), JSON.stringify(manifest, null, 2));
  console.error("BLOCKED during capture:", manifest.error);
  await browser.close().catch(() => {});
  process.exit(3);
}
writeFileSync(join(OUT, "capture.json"), JSON.stringify(manifest, null, 2));
await browser.close();
console.log("Capture complete:", join(OUT, "01-inbox.png"), "03-drift.png", "04-explain.png", "05-verified.png", "receipts.json");
