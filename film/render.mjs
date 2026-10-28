/**
 * Render: Playwright frame-stepping to ffmpeg (Polar-style, no After Effects).
 *
 * Loads index.html, seeks the paused GSAP timeline deterministically to
 * every frame at FPS, screenshots it, and pipes JPEG frames straight into
 * ffmpeg (libx264, yuv420p, 1920x1080). No audio track: a human voiceover
 * is laid over later (see README VO slots).
 */
import { chromium } from "playwright";
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, readFileSync } from "node:fs";
import { createServer } from "node:http";
import { dirname, extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const FPS = 24;
const DURATION = 180;
const OUT = join(here, "out", "settleye-film.mp4");

for (const f of ["capture/01-inbox.png", "capture/03-drift.png", "capture/04-explain.png", "capture/05-verified.png", "capture/receipts.json", "dist/main.js"]) {
  if (!existsSync(join(here, f))) {
    console.error(`BLOCKED: missing ${f}. Run: npm run build && npm run capture (with the live stack up).`);
    process.exit(2);
  }
}
mkdirSync(join(here, "out"), { recursive: true });

const ffmpeg = spawn("ffmpeg", [
  "-y", "-f", "image2pipe", "-framerate", String(FPS), "-i", "-",
  "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", String(FPS),
  "-crf", "18", "-preset", "medium", "-movflags", "+faststart", OUT,
], { stdio: ["pipe", "inherit", "inherit"] });
const ffDone = new Promise((res, rej) => { ffmpeg.on("close", (c) => (c === 0 ? res() : rej(new Error(`ffmpeg exited ${c}`)))); });

// ES modules and fetch() do not work under file://, so serve film/ locally.
const MIME = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".png": "image/png" };
const server = createServer((req, res) => {
  const path = normalize(join(here, decodeURIComponent((req.url || "/").split("?")[0])));
  if (!path.startsWith(here)) { res.writeHead(403); return res.end(); }
  try {
    const data = readFileSync(path === here ? join(here, "index.html") : path);
    res.writeHead(200, { "Content-Type": MIME[extname(path)] || "application/octet-stream" });
    res.end(data);
  } catch { res.writeHead(404); res.end("not found"); }
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const filmUrl = `http://127.0.0.1:${server.address().port}/index.html`;

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
page.on("pageerror", (e) => console.error("pageerror:", e.message));
await page.goto(filmUrl, { waitUntil: "networkidle", timeout: 60000 });
await page.evaluate(() => document.fonts.ready);
await page.waitForFunction(() => window.__film && window.__film.ready, { timeout: 30000 });

const total = FPS * DURATION;
const started = Date.now();
for (let frame = 0; frame < total; frame++) {
  const t = frame / FPS;
  await page.evaluate((tt) => window.__film.seek(tt), t);
  const shot = await page.screenshot({ type: "jpeg", quality: 86 });
  if (!ffmpeg.stdin.write(shot)) await new Promise((r) => ffmpeg.stdin.once("drain", r));
  if (frame % (FPS * 15) === 0) console.log(`frame ${frame}/${total} t=${t.toFixed(1)}s elapsed=${((Date.now() - started) / 1000).toFixed(0)}s`);
}
ffmpeg.stdin.end();
await ffDone;
await browser.close();
server.close();
console.log("Rendered:", OUT);
