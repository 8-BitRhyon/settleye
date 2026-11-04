import { chromium } from "playwright";
import { copyFileSync, mkdirSync } from "node:fs";
import { resolve } from "node:path";

const outDir = resolve("out/proof");
mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  recordVideo: { dir: outDir, size: { width: 1440, height: 900 } },
});
const page = await context.newPage();
const video = page.video();

await page.goto("http://127.0.0.1.nip.io:8000/index.html?sample=1&v=verify2", {
  waitUntil: "networkidle",
});
await page.getByText("1 drift").waitFor();
await page.waitForTimeout(2000);

await page.getByRole("button", { name: /Issue \$45\.00 refund/ }).click();
await page.getByText("Remediation receipt").waitFor();
await page.getByText("Issuer signature valid").waitFor();
await page.getByText("Merchant countersigned").waitFor();
await page
  .locator("section")
  .filter({ hasText: "Remediation receipt" })
  .scrollIntoViewIfNeeded();
await page.waitForTimeout(4000);

await page.getByRole("button", { name: "Try tamper demo" }).click();
await page.getByText("Issuer signature invalid").waitFor();
await page.getByText("Merchant signature invalid").waitFor();
await page.waitForTimeout(4000);

await page.getByRole("button", { name: "Reset" }).click();
await page.getByText("Issuer signature valid").waitFor();
await page.waitForTimeout(3000);

await context.close();
await browser.close();

const recorded = await video.path();
const target = resolve("out/settleye-verify.webm");
copyFileSync(recorded, target);
console.log(target);
