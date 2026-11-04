# Security

Settleye reads support transcripts and reconciles money promises against a live ledger. That shape invites three fair questions. This file answers them without hedging.

## What this build touches

- Test-mode Stripe keys (`sk_test_`) and a Shopify dev-store token only.
- Synthetic fixtures. No real customer transcripts, no real orders, no real money.
- No PAN, no card data, no customer PII beyond what a fixture writes.

Live keys never enter this repository. `.env` is gitignored. `.env.example` carries placeholders only, and a secret scan runs on every push over full history.

## Data minimization

The auditor never needs a card number. It needs an order id, a promised amount, and whether a settlement exists. Anything else is scope we refuse to inherit.

- Transcripts are processed in memory. They are not persisted.
- Ledger reads pull refund ids, amounts, timestamps, and refund status only.
- The gate and extraction layers never decide whether money moved. Reconciliation is deterministic code over ledger facts.

## Idempotency

Double refunding is the failure that ends a merchant relationship. Every remediation carries a durable key derived from the promise itself: `<action>:<order>:<rail>:<amount>`, for example `refund:992:stripe:45.00`.

- Order ids are normalized at the key boundary, so `#992` and `992` produce the same key.
- A retried key returns the original receipt and does not touch the ledger. Stores written before normalization are still checked for the legacy `#`-prefixed key.
- The Shopify write path passes its provider idempotency key, `refund:<order>:<amount>`, to the `@idempotent` directive. The rail is implicit in that adapter.
- Tests cover the double-call case directly, alongside an over-refund guard that refuses a request larger than the live shortfall.

## Autonomy boundary

The batch daemon is audit-only by default. `--auto-remediate` refuses to run against a live ledger. Scheduled autonomy only reads.

The HTTP one-click fix is a local demo, not a production service. It has no authentication, selects the mock ledger, and trusts the caller's promise shape. A charge ceiling blocks refunds beyond the captured amount, and a process-local lock stops concurrent duplicate calls, but a real deployment needs authentication, a server-stored audit binding, and a shared lock across workers. Run the demo on localhost.

## Receipt trust boundary

A receipt signature proves the pinned issuer key signed the exact payload and that nothing changed after signing. It does not prove the transcript is authentic, that the ledger read was correct, or that money left a real rail. The live request's `audited_at` is transport metadata and is not signed. The registry is a local JSON file, not a certificate authority.

## What is not claimed

- No SOC 2 report. It is a roadmap item.
- No penetration test.
- No zero-retention guarantee from a model provider. The hosted gate is documented as a dependency, not as a compliance feature.

## Reporting

Open an issue on this repository. Do not include secrets, order data, or customer information in a report.
