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

Double refunding is the failure that ends a merchant relationship. Every remediation carries a key derived from the promise itself: `refund:<order>:<amount>`.

- A retried key returns the original receipt and does not touch the ledger.
- The Shopify write path sends the same key to `refundCreate`. A repeat with a different payload is rejected by the provider. It is never silently applied.
- Tests cover the double-call case directly, alongside an over-refund guard that refuses a request larger than the live shortfall.

## Autonomy boundary

The batch daemon is audit-only by default. `--auto-remediate` refuses to run against a live ledger. Scheduled autonomy only reads. Money moves only through a human action.

## What is not claimed

- No SOC 2 report. It is a roadmap item.
- No penetration test.
- No zero-retention guarantee from a model provider. The hosted gate is documented as a dependency, not as a compliance feature.

## Reporting

Open an issue on this repository. Do not include secrets, order data, or customer information in a report.
