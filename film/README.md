# Settleye product film (3:00, 1080p, code-driven)

A code-driven product film in the Polar style: storyboard as TypeScript
data, GSAP DOM scenes, Playwright frame-stepping into ffmpeg. No After
Effects, no screen-recording software, no faked app UI.

- Code scenes (GSAP): hook 0:00, pain 0:20, math 2:15, vision + end card 2:45.
- Real captured beats: extraction + explain 0:45, fix + idempotent re-click
  1:30. These are real screenshots and real API receipts from the live
  local stack, driven by `capture/capture.mjs`. Nothing in those beats is
  recreated markup.
- Every claim on screen already exists in `../docs/demo-script.md`.
- No audio track. A human voiceover is laid over later; each scene in
  `src/storyboard.ts` carries a verbatim `vo` slot paced to its beat, and
  kinetic text carries the full meaning with the sound off.

## Layout

- `src/storyboard.ts` - timed beats, cues, VO slots. Total 180s (24 fps).
- `src/main.ts` - builds scenes from the storyboard, exposes `window.__film.seek(t)`.
- `src/style.css` - brand tokens from `frontend/src/landing.css` @theme:
  cream #f7f6f3, ink #131316, pine #047857, alarm #b91c1c, gold #b45309;
  Chakra Petch display, system body, IBM Plex Mono for money.
- `capture/capture.mjs` - Playwright harness against the live stack.
- `render.mjs` - frame-steps the GSAP timeline and pipes frames to ffmpeg.
- `verify.mjs` - checks runtime (150-190s) and extracts 5 stills.
- `out/settleye-film.mp4` - rendered film (1920x1080, H.264, no audio).

## Render from scratch

Prerequisites: `ffmpeg` on PATH (`brew install ffmpeg`), Node + npm.

Terminal 1, backend with repo-root credentials (real model calls):

```bash
cd ../backend
set -a; source ../.env; set +a
uv run uvicorn app.main:app --port 8000
```

Terminal 2, frontend:

```bash
cd ../frontend
npm run dev -- --port 5173 --host 127.0.0.1
```

Terminal 3, film (deps live only in this folder):

```bash
cd ../film
npm install
npx playwright install chromium   # only if no Chromium is cached
npm run capture                   # real audit, explain, fix, re-click
npm run render                    # writes out/settleye-film.mp4
npm run verify                    # duration + stills to /tmp/settleye-film-*.png
```

Important: restart the backend before each `npm run capture`. The ledger
and the idempotency store are in-memory; a backend that already fixed
order #992 will (correctly) report Verified instead of drift, and capture
will stop instead of faking the beat.

If the stack or a model call fails, `capture.mjs` exits non-zero and says
exactly what blocked. Fix that; never hand-make a capture frame.

## Laying the voiceover later

1. Record one take per beat using the `vo` strings in `src/storyboard.ts`.
   Beats are 20s, 25s, 45s, 45s, 30s, 15s: read at a natural pace and
   leave the tail of each beat silent. The film was paced with that
   headroom; do not speed-read to fill it.
2. Replace `[name]` in the hook take with the presenter's name.
3. Mix under no music bed changes: the MP4 has no audio track, so lay the
   VO as the only track, or add music at low level in your editor.
4. Keep captions as rendered: they already carry the full meaning muted.
