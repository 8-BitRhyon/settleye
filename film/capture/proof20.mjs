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

await page.goto("https://8-bitrhyon.github.io/settleye/index.html?sample=1", {
  waitUntil: "networkidle",
});
await page.getByText("1 drift").waitFor();
await page.waitForTimeout(2500);

await page.getByRole("button", { name: /Issue \$45\.00 refund/ }).click();
await page.getByText("Remediation receipt").waitFor();
await page.getByText("$45.00 refunded.").waitFor();
await page.waitForTimeout(2500);

await page.getByRole("button", { name: "Retry the same fix" }).click();
await page
  .getByText("Already executed. $0.00 additional movement.")
  .waitFor();
await page.waitForTimeout(3000);

await context.close();
await browser.close();

const recorded = await video.path();
const target = resolve("out/settleye-proof.webm");
copyFileSync(recorded, target);
console.log(target);
