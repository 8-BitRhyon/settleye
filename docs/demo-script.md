# Demo Script (3:00)

Read verbatim on camera. Every claim below is already true in the repo.

## 0:00-0:20 The hook (Impact)

> "Every AI support agent, yours, mine, Grok, Atlas, any of them, will eventually tell a customer 'your refund is processed' when nothing was processed. The agent is not lying. It just never checks. Each phantom refund costs $45, plus a $128 chargeback when the customer gives up waiting. I'm [name], and this is Settleye: the auditor for AI agents."

Why this opening: it preempts the biggest judge objection (why not just use another bot?) in the first twenty seconds. Those tools ARE agents. Every agent drifts. Switching agents changes which agent you verify, never whether verification is needed.

## 0:20-0:45 The pain, quantified

> "Air Canada's chatbot invented a refund policy and the tribunal made them honor it. Priceline's bot promised refunds on non-refundable bookings. One phantom refund a week leaks $2,340 a year per merchant, approaching $4,700 once chargebacks land."

On screen: inbox header with savings totals.

## 0:45-1:30 The Meta core (Tooling plus Depth)

Paste the transcript. Click Audit.

> "Watch the middle panel. The Meta model, muse-spark-open, reads the messy dialogue and returns structured promise objects: action, amount, order, system, confidence, and the exact quote. No regex anywhere. The model is the only path from words to promises. Output is Pydantic-validated, repairs itself twice, then fails loudly instead of guessing."

On screen: model ID visible, raw JSON, then the side-by-side diff: transcript quote on the left, live ledger row on the right, red MISMATCH badge. Ledger shows $0.00 settled of $45.00 promised. Click "Why does this matter?" The model explains the mismatch in one merchant sentence.

## 1:30-2:15 The fix

Click "Issue $45.00 refund."

> "One click executes the corrective refund against the test ledger. Receipt carries an idempotency key. Watch me click it again: same key, original receipt, ledger untouched. No double refunds, ever. Card flips to Verified, savings header moves to $45. That is the firewall: promise, proof, patch."

On screen: receipt, flipped card, updated totals.

## 2:15-2:45 The numbers (Impact)

> "This inbox pays for itself the first time it fires in a month. Mid-market math: about $494 of monthly value against a $99 plan, six-day payback. Every $1 of dispute loss costs merchants $4.61 all-in. Our open eval scores 12 of 12 verdicts correct, and no retracted promise ever reported drift. And every save is itemized, not vibes."

## 2:45-3:00 Vision plus compliance (end card on screen)

> "Every payment needs a ledger. Every agent needs an auditor. The nightly sweep already catches orders promised across several tickets. Built [dates] for this event on Meta open weights. Repo link, setup under five minutes, synthetic data only, no live payments."

End card: GitHub URL, model ID, `uv run pytest` plus `npm run build` green.

## Judge objections, one line each

- Why not just use Grok, Atlas, or Hermes instead? Those are agents. The premise, proven by Air Canada and Priceline, is that every agent drifts. Settleye audits all of them.
- Why not Gorgias guardrails or Decagon audit trails? Guardrails prevent before send for one vendor. Trails log tool calls without checking ledger truth. We verify after execution, across vendors.
- What stops Shopify or Stripe building it? They verify their own rails and never read transcripts. Neutrality is the product.
- Is the model decorative? The video shows raw transcript to raw model JSON to diff with no cuts. Model ID stays on screen. A wire-level test pins the ID on every request.
- What did you build this week? Everything in this repo, greenfield, timestamped commits. Nothing pre-existed.
