# Settleye demo script (3:00)

The film is code-driven from `film/src/storyboard.ts`. This file is the
spoken script and the timing contract. The visual system now matches
`frontend/landing.html`: ink, cream, mint, alarm, Fraunces, Manrope,
JetBrains Mono.

- Runtime: 180 seconds, 1920x1080, 24 fps.
- Voice: one narrator, natural pace. Leave the tail of each beat silent.
- Placeholders: `[name]` is the presenter. `[dates]` is October 26 to
  November 4, 2026.
- On-screen text already carries the full meaning with sound off.

## Beats

### 0:00-0:20 The hook

> Your AI support agent told the customer the refund was processed. The ticket
> closed. The ledger says zero dollars moved. The agent is not lying. It just
> never checks. Each phantom refund is forty-five dollars, plus a chargeback.
> I'm [name], and this is Settleye.

### 0:20-0:45 The pain, quantified

> Air Canada's chatbot invented a refund policy. A tribunal made them honor it.
> Priceline's bot promised refunds on non-refundable bookings. One phantom
> refund a week leaks two thousand three hundred forty dollars a year. Add
> chargebacks and it approaches four thousand seven hundred. The industry
> grades the conversation. The customer waits for the money.

### 0:45-1:30 The Meta core

> Watch the screen. Muse Spark Open reads the messy dialogue and returns
> structured promises: action, amount, order, system, confidence, and the exact
> quote. No regex. The model is the only path from words to promises. Every
> reply is Pydantic-validated, repaired at most twice, then fails loudly. The
> model never decides whether money moved. Reconciliation is deterministic code.

### 1:30-2:15 The fix

> One click executes the corrective refund against the test ledger. The receipt
> carries an idempotency key. Click again: same key, original receipt, ledger
> untouched. A concurrent duplicate is serialized. A charge ceiling stops a
> forged promise. The card flips to Verified, the recovered total moves to
> forty-five dollars. That is the firewall: promise, proof, patch.

### 2:15-2:45 The numbers

> The proof is not a projection. Forty-four dollars caught live on one test
> order in four seconds. Twelve of twelve eval verdicts, eleven of twelve exact
> entities, zero non-binding promises drifted. Three hundred wild transcripts,
> zero false binding promises. Every dollar of dispute loss costs four sixty-one
> all-in. This is evidence, not vibes.

### 2:45-3:00 Vision and end card

> Every payment needs a ledger. Every agent needs an auditor. The nightly sweep
> catches orders promised across several tickets. Built [dates] for this event
> on Meta open weights.

The end card carries the sample inbox, repo, and model ID.

## 15-second proof

Recorded from the public sample inbox by `film/capture/proof20.mjs`.

> The agent promised a forty-five dollar refund. The ledger shows zero settled.
> Settleye catches the drift. One click fixes it. Click again: same key, zero
> dollars more. Resolved is not settled.

End card: `Resolved is not Settled.` / `SETTLEYE`.

## 16-second receipt verification

Recorded from the public sample by `film/capture/verify20.mjs`.

> Every fix gets a signed receipt. Settleye signs it. The merchant
> countersigns it. Verify both in your browser. Change one digit, and the
> signature fails. That is proof, not a screenshot.

End card: `Resolved is not Settled.` / `SETTLEYE`.

## Record the human voiceover

Record one full 3:00 take, or one take per beat. Do not speed-read to fill a
beat; the film has headroom. Keep the room quiet, the mic close, and the level
consistent.

Full take:

```bash
cd film
python3 voiceover.py \
  --audio ~/Downloads/settleye-vo.wav \
  --film out/settleye-film-v2-silent.mp4 \
  --output out/settleye-film-v2-human.mp4
```

The script normalizes to about -16 LUFS, pads or trims to 180 seconds, and
copies the video track without re-encoding. Check the result:

```bash
FILM_PATH=out/settleye-film-v2-human.mp4 npm run verify
```

If a take is too long for its beat, shorten the read, not the visual. The
timings above are the contract.

## Re-render the visuals

```bash
cd film
npm run build
npm run capture:sample   # recapture the public sample UI states
npm run render           # silent master, out/settleye-film-v2-silent.mp4
python3 voiceover.py     # synthetic preview, out/settleye-film-v2-preview.mp4
```

Upload the human cut after you check it. Keep the silent master.
