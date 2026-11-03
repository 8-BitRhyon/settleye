import { chromium } from "playwright";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 1,
});
await page.goto(pathToFileURL(resolve("capture/endcard.html")).href);
await page.evaluate(() => document.fonts.ready.then(() => true));
await page.screenshot({ path: resolve("out/proof-endcard.png") });
await browser.close();
console.log(resolve("out/proof-endcard.png"));
