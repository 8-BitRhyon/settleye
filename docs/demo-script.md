# Settleye demo script (3:00)

This is the spoken script and the timing contract for the film. The film is
code-driven from `film/src/storyboard.ts`; the words below are the VO slots.

- Runtime: 180 seconds, 1920x1080, 24 fps.
- Voice: one narrator, natural pace. Do not speed-read to fill a beat.
- Read the short lines as sentences. `[pause]` means let the screen land.
- On-screen text already carries the full meaning with sound off.

## Read this, not the screen

The voiceover is a guide, not a transcript of the interface. Say the plain
version. Let the screen carry labels, JSON, and table numbers.

## Beat map

| Beat | Time | Words | Target read | Screen time |
|---|---|---:|---:|---:|
| Hook | 0:00-0:20 | 38 | 16-17s | 3-4s |
| Pain | 0:20-0:45 | 55 | 23-24s | 1-2s |
| Meta core | 0:45-1:30 | 83 | 34-37s | 8-11s |
| Fix | 1:30-2:15 | 84 | 35-37s | 8-10s |
| Numbers | 2:15-2:45 | 64 | 26-28s | 2-4s |
| Vision | 2:45-3:00 | 27 | 11-12s | 3-4s |

The read times assume 135-145 words per minute. The demo beats intentionally
leave 8-11 seconds of silence for the screen.

## 0:00-0:20 The hook

> Your AI agent told the customer, "Your refund is processed."
>
> [pause]
>
> The ticket closed. The ledger says zero dollars moved.
>
> The agent isn't lying. It just never checked.
>
> [pause]
>
> That gap is what we audit.
>
> I'm Rhyon. This is Settleye.

## 0:20-0:45 The pain

> Air Canada's chatbot invented a refund policy. A tribunal made them honor it.
>
> Priceline's bot promised refunds on bookings that weren't refundable.
>
> [pause]
>
> One phantom refund a week costs twenty-three hundred forty dollars a year.
> Add chargebacks, and it's closer to four thousand seven hundred.
>
> The industry grades the conversation. The customer waits for the money.

## 0:45-1:30 The Meta core

> Watch the screen.
>
> [pause]
>
> The transcript is messy. The model reads it and returns structured promises:
> the action, the amount, the order, the system, and the exact quote.
>
> That's the only job the model has. No regex. No guessing.
>
> Every reply is validated. If it doesn't fit the format, it fails loudly.
>
> Then a separate check compares the promise to the ledger.
>
> Here's the drift: the promise says forty-five dollars. The ledger says zero.
>
> The model never decides whether money moved. The ledger does.

## 1:30-2:15 The fix

> Here's the fix.
>
> One click refunds the exact shortfall against the test ledger.
>
> The receipt carries a retry key. Click again, and you get the same receipt.
> No second refund.
>
> [pause]
>
> Two clicks at once still produce one refund. A charge ceiling blocks a
> promise bigger than the order.
>
> The receipt is signed by Settleye and countersigned by the merchant. Change
> one digit, and the signature fails.
>
> The card flips to Verified. The recovered total moves to forty-five dollars.
>
> That's the firewall: promise, proof, patch.

## 2:15-2:45 The numbers

> The proof isn't a projection.
>
> Forty-four dollars caught live on one test order, in four seconds.
>
> Twelve of twelve eval verdicts. Eleven of twelve entities exact. Zero of
> eight real promises missed.
>
> Three hundred wild transcripts. Zero false binding promises.
>
> [pause]
>
> Then the fleet model: one hundred twenty-four thousand at ten thousand
> tickets. Twelve point five million at a million.
>
> Stated assumptions, not a guarantee.

The screen carries the fleet ladder: 10,000 tickets per month, $124,328.40
modeled annual exposure protected; 100,000, $1,256,604.96; 1,000,000,
$12,557,168.40. The label reads `TIER 3 / MODELED, NOT MEASURED`, and the
assumption line stays visible: 10.6% refund intent, 66.7% binding commitment,
4.0% execution failure, $52.50 average refund, 4.61x dispute cost, $128
chargeback fee. The 4.0% failure rate is an assumption, not a merchant
measurement.

## 2:45-3:00 Vision and end card

> Every payment needs a ledger. Every agent needs an auditor.
>
> [pause]
>
> A nightly sweep catches orders promised across several tickets.
>
> Built for this event on Meta open weights.

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

Record one full 3:00 take, or one take per beat. Keep the room quiet, the mic
close, and the level consistent. Do not compress or limit the file.

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

Per-beat files are also fine. Name them `00-hook`, `01-pain`, `02-extraction`,
`03-fix`, `04-math`, and `05-vision`. I will place each at its beat start.

## Re-render the visuals

```bash
cd film
npm run build
npm run capture:sample   # recapture the public sample UI states
npm run render           # silent master, out/settleye-film-v2-silent.mp4
python3 voiceover.py     # synthetic preview, out/settleye-film-v2-preview.mp4
```

Upload the human cut after you check it. Keep the silent master.
