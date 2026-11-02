---
name: Pilot request
about: Ask for a managed shadow audit over your support transcripts
title: "Pilot request"
labels: pilot
---

## What a pilot is

A read-only audit. You bring a transcript export and test-mode Stripe or
Shopify keys. I reconcile every refund or cancellation promise in the sample
against what the ledger actually settled, and hand back a leakage ledger:
dollars promised against dollars moved, one row per drift, with the transcript
quote and the ledger reference.

No write access until you approve an individual fix.

## What the audit needs

- Roughly how many tickets per month your AI agent handles.
- Which helpdesk you use (Gorgias, Zendesk, Intercom, other).
- Whether you can export transcripts as JSON, CSV, or text.
- Whether you are willing to use test-mode keys for the first pass.

## What you get back

- The leakage ledger for the sample you provide.
- Every drift cited to a transcript span and a ledger record.
- A count of promises that settled, promises that drifted, and promises that
  never bound (conditional, retracted, policy explanation).

Delete anything you do not want to share. Synthetic or redacted transcripts are
fine for a first pass.
