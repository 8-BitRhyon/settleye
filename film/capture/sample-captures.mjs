import { chromium } from "playwright";
import { copyFileSync } from "node:fs";
import { resolve } from "node:path";

const BASE = "http://127.0.0.1:8091/index.html";
copyFileSync(resolve("..", "frontend", "src", "sample-receipt.json"), resolve("capture", "sample-receipt.json"));
const browser = await chromium.launch();

async function pageAt(width, height, scale = 1) {
  const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: scale });
  const page = await context.newPage();
  await page.goto(BASE, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  return { context, page };
}

const shot = async (page, name) => {
  await page.waitForTimeout(450);
  await page.screenshot({ path: resolve("capture", name) });
  console.log(name);
};

// 01: inbox before any audit.
{
  const { context, page } = await pageAt(1600, 900);
  await page.getByText("SUPPORT TRANSCRIPT").waitFor();
  await shot(page, "01-inbox.png");
  await context.close();
}

// 03 + 04 + 05: sample report, explanation, fix and receipt.
{
  const { context, page } = await pageAt(1600, 900, 2);
  await page.goto(`${BASE}?sample=1`, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.getByText("State drift").first().waitFor();
  const driftCard = page.locator("section").filter({ hasText: "State drift" }).first();
  const driftArticle = driftCard.locator("article").first();
  await driftArticle.screenshot({ path: resolve("capture", "03-drift.png") });
  console.log("03-drift.png");

  await page.getByRole("button", { name: "Why does this matter?" }).click();
  await page.getByText("The transcript says").waitFor();
  await driftArticle.screenshot({ path: resolve("capture", "04-explain.png") });
  console.log("04-explain.png");

  await page.getByRole("button", { name: /Issue \$45\.00 refund/ }).click();
  await page.getByText("Issuer signature valid").waitFor();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: resolve("capture", "05-verified.png") });
  console.log("05-verified.png");
  await context.close();
}

// 06: the receipt card at 2x for the film frame.
{
  const { context, page } = await pageAt(1600, 1000, 2);
  await page.goto(`${BASE}?sample=1`, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.getByRole("button", { name: /Issue \$45\.00 refund/ }).click();
  await page.getByText("Issuer signature valid").waitFor();
  const card = page.locator("section").filter({ hasText: "Issuer signature valid" }).first();
  await card.screenshot({ path: resolve("capture", "06-receipt.png") });
  console.log("06-receipt.png");
  await context.close();
}

await browser.close();
