# Settleye submission

**Your AI agent promised a refund. Did the money move?**

Settleye is the execution auditor for AI support agents. It extracts binding
promises from transcripts, reconciles each one against Stripe or Shopify ledger
state, surfaces the gap in an exception inbox, and fixes the shortfall with a
durable, idempotent receipt.

## Links

- Live landing page: https://8-bitrhyon.github.io/settleye/landing.html
- No-install sample inbox: https://8-bitrhyon.github.io/settleye/index.html?sample=1
- 3-minute film with voiceover: https://github.com/8-BitRhyon/settleye/releases/download/demo-v1/settleye-film.mp4
- 15-second proof: https://github.com/8-BitRhyon/settleye/releases/download/demo-v1/settleye-proof.mp4
- Repository: https://github.com/8-BitRhyon/settleye

## 60-second judge path

1. Open the sample inbox. It renders a real recorded audit with `1 drift · $45.00 at risk`.
2. Click `Issue $45.00 refund`. The receipt shows `refund:992:45.00`, `$45.00 refunded`, and `Ledger matches`.
3. Click `Retry the same fix`. It returns `Already executed. $0.00 additional movement.` with the same key.
4. Watch the 15-second proof, then the 3-minute film for the full story.
5. The live dev-store proof: order `#1001` has `$6.00` settled of a `$50.00` promise, and the daemon reports `$44.00` at risk in about 4 seconds.

## The wedge

The support industry grades the conversation. The money only settles at the
ledger. Nobody joins the two per order.

- Guardrails check words before send.
- QA tools sample transcripts for tone.
- Dispute vendors act after the chargeback, often for 25% of recovered money.

Settleye sits after execution and before the dispute. It is not a better
chatbot. It is the proof layer between what the agent said and what the ledger
did.

## Why this is hard to copy

Extraction is commodity. The refusal path is not:

- Reconcile server-side before moving money.
- Clamp the refund to the live shortfall, even if the client sends a different amount.
- Persist receipts in an append-only JSONL store keyed by action, order, rail, and promised amount.
- A partial refund cannot mint a second key. A restart cannot forget the receipt.
- A corrupt receipt store fails closed.
- A retry returns the original receipt and moves $0.

## Evidence

- `12 of 12` eval verdicts correct; `11 of 12` entities exact.
- `0 of 4` non-binding cases reached drift: retracted, conditional, superseded, info-only.
- Live dev-store order `#1001`: `$44.00` at risk in about 4 seconds, audit-only.
- `116` backend checks and `37` frontend checks green.
- Frontier comparison: same prompt, same 12 cases. Both matched `11 of 12`; the frontier arm invented an order id that appears nowhere in the transcript. Settleye returned nothing.
- Free-gate bench: a 55 MB TinyBERT fine-tune kept `10 of 10` commitments on the eval, but on 10,042 real ABCD support dialogues it discarded only `0.9` to `1.7` percent. Safe, not a cost saver. The negative result is documented rather than hidden.

## Scope

- Fixtures are synthetic. Ledgers are Stripe and Shopify test mode.
- No live payments. No real merchant savings claimed.
- The product path needs a transcript export and read-only ledger keys. The
  public sample and the 15-second proof need no install and no credentials.
- SOC 2 is a roadmap item, not a claim.

## Stack

- Meta Muse Spark Open (`meta-models/muse-spark-open-1026`) via Baseten.
- FastAPI, Python 3.12, Pydantic v2.
- React, TypeScript, Vite, Tailwind.
- Stripe and Shopify test-mode adapters.
- Append-only JSONL remediation receipt store.
- Open-weight TinyBERT gate benchmark, kept out of the product path.

## Short pitch for the form

> AI support agents tell customers a refund is processed, then the tool call
> fails silently. Settleye pulls every binding promise from the transcript,
> diffs it against Stripe and Shopify ledger state, and fixes the shortfall with
> an idempotent receipt that survives restarts. Resolved is not settled. We
> prove it on a live dev store and a no-install public sample.

## What the judge should remember

**Resolved is not Settled.**

Settleye is the receipt between an AI agent's promise and the money that
actually moved.
