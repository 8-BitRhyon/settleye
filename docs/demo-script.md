# Settleye demo script (3:00)

The film is code-driven from `film/src/storyboard.ts`. This file is the spoken
script and the timing contract. The shipped cut uses a synthetic scratch
voiceover rendered by `film/voiceover.py`; replace it with a human take when
one is available.

- Runtime: 180 seconds, 1920x1080, 24 fps.
- Voice: one narrator, natural pace. Leave the tail of each beat silent.
- Placeholders: `[name]` is the presenter. `[dates]` is October 26 to November
  4, 2026.
- On-screen text already carries the full meaning with sound off.

## Beats

### 0:00-0:20 The hook

> Every AI support agent will eventually tell a customer "your refund is
> processed" when nothing was processed. The agent is not lying. It just never
> checks. Each phantom refund costs $45, plus a $128 chargeback. I'm [name],
> and this is Settleye: the auditor for AI agents.

### 0:20-0:45 The pain, quantified

> Air Canada's chatbot invented a refund policy and the tribunal made them honor
> it. Priceline's bot promised refunds on non-refundable bookings. One phantom
> refund a week leaks $2,340 a year per merchant, approaching $4,700 once
> chargebacks land.

### 0:45-1:30 The Meta core

> Watch the middle panel. The Meta model, muse-spark-open, reads the messy
> dialogue and returns structured promise objects: action, amount, order,
> system, confidence, and the exact quote. No regex anywhere. The model is the
> only path from words to promises. Output is Pydantic-validated, repairs
> itself twice, then fails loudly instead of guessing.

### 1:30-2:15 The fix

> One click executes the corrective refund against the test ledger. Receipt
> carries an idempotency key. Watch me click it again: same key, original
> receipt, ledger untouched. No double refunds, ever. Card flips to Verified,
> savings header moves to $45. That is the firewall: promise, proof, patch.

### 2:15-2:45 The numbers

> This inbox pays for itself the first time it fires in a month. Mid-market
> math: about $494 of monthly value against a $99 plan, six-day payback. Every
> $1 of dispute loss costs merchants $4.61 all-in. Our open eval scores 12 of
> 12 verdicts correct, and no retracted promise ever reported drift. And every
> save is itemized, not vibes.

### 2:45-3:00 Vision and end card

> Every payment needs a ledger. Every agent needs an auditor. The nightly sweep
> catches orders promised across several tickets. Built [dates] for this event
> on Meta open weights.

The end card on screen carries the repo link, setup time, and the synthetic
data and test-ledger scope.

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

## Re-render the voiceover

```bash
cd film
python3 voiceover.py --voice Samantha
```

Set the presenter name and dates in `voiceover.py` (they are substituted from
the `[name]` and `[dates]` placeholders). The script prints each scene's VO
duration and refuses to claim a fit when a take exceeds its scene. Upload the
voiced cut with:

```bash
gh release upload demo-v1 out/settleye-film.mp4 --clobber
```

Keep `out/settleye-film-silent.mp4` as the silent master.
