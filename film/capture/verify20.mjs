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

await page.goto("http://127.0.0.1.nip.io:8000/index.html?sample=1", {
  waitUntil: "networkidle",
});
await page.getByText("1 drift").waitFor();
await page.waitForTimeout(1500);

await page.getByRole("button", { name: /Issue \$45\.00 refund/ }).click();
await page.getByText("Signed execution receipt").waitFor();
await page.evaluate(() => {
  document
    .getElementById("signed-receipt")
    ?.scrollIntoView({ block: "center" });
});
await page.waitForTimeout(1500);

await page.getByRole("button", { name: "Verify receipt" }).click();
await page.getByText("Signature valid.").waitFor();
await page.waitForTimeout(2500);

await page.getByRole("button", { name: "Tamper with the amount" }).click();
await page.getByText("Invalid receipt.").waitFor();
await page.waitForTimeout(3000);

await context.close();
await browser.close();

const recorded = await video.path();
const target = resolve("out/settleye-verify.webm");
copyFileSync(recorded, target);
console.log(target);
