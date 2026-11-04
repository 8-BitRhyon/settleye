# Settleye submission

**Your AI agent promised a refund. Did the money move?**

Settleye is the execution auditor for AI support agents. It extracts binding
promises from transcripts, reconciles each one against Stripe or Shopify ledger
state, surfaces the gap in an exception inbox, and fixes the shortfall with a
durable, signed, idempotent receipt.

## Links

- Live landing page: https://8-bitrhyon.github.io/settleye/landing.html
- No-install sample inbox: https://8-bitrhyon.github.io/settleye/index.html?sample=1
- 3-minute film with voiceover: https://github.com/8-BitRhyon/settleye/releases/download/demo-v1/settleye-film.mp4
- 15-second proof: https://github.com/8-BitRhyon/settleye/releases/download/demo-v1/settleye-proof.mp4
- Receipt verification clip: https://github.com/8-BitRhyon/settleye/releases/download/demo-v1/settleye-verify.mp4
- Repository: https://github.com/8-BitRhyon/settleye

## 60-second judge path

1. Open the sample inbox. It renders a real recorded audit with `1 drift · $45.00 at risk`.
2. Click `Issue $45.00 refund`. One `Remediation receipt` appears with `Issuer signature valid`, `Merchant countersigned`, the receipt id, and `refund:992:stripe:45.00`.
3. Click `Retry the same fix`. It returns `Already executed. $0.00 additional movement.` with the same key.
4. Click `Try tamper demo`. Both signature rows turn invalid and the card reports the altered payload. `Reset` restores both valid rows.
5. Watch the 15-second proof, the receipt verification clip, and the 3-minute film.
6. The live dev-store proof: order `#1001` has `$6.00` settled of a `$50.00` promise, and the daemon reports `$44.00` at risk in about 4 seconds.

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
- A signed, canonical receipt binds the transcript digest, promise, ledger observation, idempotency key, and result to a pinned issuer key.

## The new artifact: two-party execution receipts

A fix can emit a portable, tamper-evident receipt. It binds the transcript
digest, the promise, the ledger observation, the idempotency key, and the
remediation result. Settleye signs the canonical payload with Ed25519. A
merchant can countersign the receipt id, so both parties acknowledge the same
execution.

- The browser verifier pins the issuer and merchant keys and checks both
  signatures locally.
- The live `/remediate` path returns the signed envelope when an issuer key and
  audit context are configured. A replay returns the original envelope and
  moves $0.
- The issuer key registry supports `active`, `retired`, and `revoked` states.
  Rotated keys still verify old receipts. Revoked and unknown keys fail closed.
- `GET /receipt/keys` publishes public keys only. `POST /receipt/verify`
  verifies with a caller pin or the registry.
- Change one digit of the promised amount and the issuer signature fails.
  Change the merchant acknowledgement time and the merchant signature fails.

Spec: `docs/receipt-spec.md`.

This is the frontier claim. Not another audit dashboard. A two-party proof
artifact for agent execution.

## Evidence

- `12 of 12` eval verdicts correct; `11 of 12` entities exact.
- `0 of 4` non-binding cases reached drift: retracted, conditional, superseded, info-only.
- Live dev-store order `#1001`: `$44.00` at risk in about 4 seconds, audit-only.
- `222` backend checks and `76` frontend checks green.
- Live signed path, exercised on a real keyring: a binding refund for `#992` returned a signed envelope, `POST /receipt/verify` accepted it through the published active key, a restarted service returned the same envelope, and the replay moved `$0.00`.
- Key lifecycle: a retired key still verifies its historical receipt, a revoked key fails with `revoked_key`, and an unregistered key fails with `unknown_key`.
- Two-party sample: issuer and merchant both verify in the browser; a one-digit amount change breaks the issuer signature; a changed merchant acknowledgement time breaks the merchant signature.
- Shadow-audit proxy on the 12-case eval: `12` tickets, `5` drifts, `$285.50` at risk, `$23,791.67` per 1,000 tickets, `0 of 8` false clears. This is recorded-output replay on synthetic cases with a mock ledger, not a merchant pilot.
- Frontier comparison: same prompt, same 12 cases. Both matched `11 of 12`; the frontier arm invented an order id that appears nowhere in the transcript. Settleye returned nothing.
- Free-gate bench: a 55 MB TinyBERT fine-tune kept `10 of 10` commitments on the eval, but on 10,042 real ABCD support dialogues it discarded only `0.9` to `1.7` percent. Safe, not a cost saver. The negative result is documented rather than hidden.

## Scope

- Fixtures are synthetic. Ledgers are Stripe and Shopify test mode.
- No live payments. No real merchant savings claimed.
- The public sample receipt is signed by a demo issuer key and countersigned by a demo merchant key. The signatures prove those keys issued and acknowledged the payload; they do not independently prove Stripe or Shopify state.
- The live `/remediate` path signs only when `backend/.tmp/keyring.json` and the issuer private key are configured and the request carries audit context. Without them, the durable receipt is still recorded and `receipt` is `null`.
- The live path trusts the caller's transcript digest and audit time; it does not re-hash a stored audit. The signature binds the claim but does not prove the audit produced it.
- The published key registry is a local JSON file and a read-only endpoint, not a hosted certificate authority. Rotation and revocation are CLI operations.
- The shadow audit is a 12-case recorded-output replay, not a real merchant measurement. A real pilot needs a transcript export plus a Shopify read-only token or an exported ledger snapshot. The Stripe adapter is test-mode only, so a live Stripe pilot needs a new read-only adapter. The exact blocker and command are in `docs/research/23-shadow-audit.md`.
- The product path needs a transcript export and read-only ledger keys. The public sample and the 15-second proof need no install and no credentials.
- SOC 2 is a roadmap item, not a claim.

## Stack

- Meta Muse Spark Open (`meta-models/muse-spark-open-1026`) via Baseten.
- FastAPI, Python 3.12, Pydantic v2.
- Ed25519 receipts, canonical JSON, issuer key registry, merchant countersignatures.
- React, TypeScript, Vite, Tailwind.
- Stripe and Shopify test-mode adapters.
- Append-only JSONL remediation receipt store.
- Open-weight TinyBERT gate benchmark, kept out of the product path.

## Short pitch for the form

> AI support agents tell customers a refund is processed, then the tool call
> fails silently. Settleye pulls every binding promise from the transcript,
> diffs it against Stripe and Shopify ledger state, and fixes the shortfall with
> an idempotent receipt that survives restarts. The live fix emits a signed
> Ed25519 receipt; a merchant can countersign it, and the browser verifies both.
> Resolved is not settled. We prove it on a live dev store and a no-install
> public sample.

## What the judge should remember

**Resolved is not Settled.**

Settleye is the receipt between an AI agent's promise and the money that
actually moved.
