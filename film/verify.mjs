/** Extract 5 stills across the beats for visual confirmation. */
import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const mp4 = join(here, "out", "settleye-film.mp4");
if (!existsSync(mp4)) { console.error("BLOCKED: no MP4. Run npm run render first."); process.exit(2); }
const dur = Number(execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4]).toString().trim());
console.log(`duration=${dur.toFixed(2)}s`);
if (!(dur >= 150 && dur <= 190)) { console.error("FAIL: runtime outside 150-190s"); process.exit(3); }
const marks = [
  ["hook", 8], ["pain", 30], ["extraction", 70], ["fix", 115], ["endcard", 174],
];
for (const [name, t] of marks) {
  const out = `/tmp/settleye-film-${name}.png`;
  execFileSync("ffmpeg", ["-y", "-v", "error", "-ss", String(t), "-i", mp4, "-frames:v", "1", out]);
  console.log(out, `t=${t}s`);
}
console.log("OK: runtime in range, 5 stills extracted to /tmp/settleye-film-*.png");
