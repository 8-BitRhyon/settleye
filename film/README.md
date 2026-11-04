# Settleye product film (3:00, 1080p, code-driven)

A code-driven product film matched to the live landing page: ink, cream,
mint, alarm, Fraunces display, Manrope body, JetBrains Mono labels and money.
Storyboard as TypeScript data, GSAP DOM scenes, Playwright frame-stepping into
ffmpeg. No After Effects, no stock footage, no generative video.

- Code scenes: hook, pain, proof, end card.
- Real product beats: the redesigned sample inbox, drift, explain, verified
  state, and signed receipt, captured by `capture/sample-captures.mjs`.
- Voiceover: synthetic scratch take from `voiceover.py`, or a human take muxed
  with `--audio`.

## Layout

- `src/storyboard.ts` - timed beats, cues, facts, VO slots. Total 180s, 24 fps.
- `src/main.ts` - builds the landing-style scenes, exposes `window.__film.seek(t)`.
- `src/style.css` - landing tokens: ink #0a1014, cream #e9ece6, mint #9fd8c2,
  alarm #f0837f, gold #d6a45e. Fraunces, Manrope, JetBrains Mono.
- `render.mjs` - frame-steps the GSAP timeline and pipes frames to ffmpeg.
- `capture/sample-captures.mjs` - recaptures the public sample UI states.
- `capture/receipt20.mjs` - captures the signed receipt card at 2x.
- `voiceover.py` - synthetic scratch VO or human audio mux.
- `verify.mjs` - checks runtime and extracts stills.

## Render the new cut

```bash
cd film
npm install
npx playwright install chromium
npm run build
npm run capture:sample   # expects the built app on 127.0.0.1:8091
npm run render           # out/settleye-film-v2-silent.mp4
python3 voiceover.py     # out/settleye-film-v2-preview.mp4
```

`capture:sample` needs the frontend preview server:

```bash
cd frontend
npm run build
python3 -m http.server 8091 --bind 127.0.0.1 --directory dist
```

The capture uses the public sample path, so no model key and no backend are
needed. It never fakes a product state.

## Human voiceover

Record one full 3:00 take with the script in `../docs/demo-script.md`.

```bash
cd film
python3 voiceover.py \
  --audio ~/Downloads/settleye-vo.wav \
  --film out/settleye-film-v2-silent.mp4 \
  --output out/settleye-film-v2-human.mp4
FILM_PATH=out/settleye-film-v2-human.mp4 npm run verify
```

The mux normalizes to about -16 LUFS, pads or trims to 180 seconds, and copies
the video track. Keep `out/settleye-film-v2-silent.mp4` as the master.

## 15-second proof

`capture/proof20.mjs` records the public sample inbox: drift, issue refund,
receipt, retry, already executed. The shipped cut is `out/settleye-proof.mp4`
and the release asset `settleye-proof.mp4`.

## 16-second receipt verification

`capture/verify20.mjs` records the sample card: issuer valid, merchant
countersigned, tamper invalid, reset valid. The shipped cut is
`out/settleye-verify3.mp4` and the release asset `settleye-verify.mp4`.

## Notes

- The old `out/settleye-film.mp4` is the previous cut. The new master is
  `out/settleye-film-v2-silent.mp4`; the synthetic preview is
  `out/settleye-film-v2-preview.mp4`; the human cut is
  `out/settleye-film-v2-human.mp4`.
- Every on-screen claim exists in `../docs/demo-script.md` or the claim ledger.
- The sample is a test-ledger demo. No real merchant data or live payments.
