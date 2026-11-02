# Claim ledger

Every number the landing page shows, where it comes from, and what it does not cover. If a claim is not here, it does not ship.

## Our measurements

| Claim | Value | Source | Scope |
|---|---|---|---|
| Eval verdicts | 12 of 12 | `docs/research/12-eval-results.md` | Our own 12-case set, written by us |
| Exact entity matches | 11 of 12 | `fixtures/eval_live_output.json`, `backend/tests/test_eval_replay.py` | One documented miss: t07 returns an empty list where the manifest holds an info-only entity. Both are green |
| Non-binding cases that drifted | 0 of 4 | `docs/research/12-eval-results.md` | Retracted, conditional, superseded, info-only |
| Wild transcripts processed | 300 of 300 | `docs/research/19-hf-benchmark.md` | Bitext sample, seed 7. Zero crashes, zero false binding promises |
| Live drift caught | $44.00 on order #1001 in 4.07s | `README.md` | Single test-mode dev-store order. Not a fleet sample |
| Automated checks | 86 backend, 20 frontend | CI | Counted at the commit named in the run |

## Borrowed numbers, with qualifiers

| Claim | Value | Source | Qualifier that must appear with it |
|---|---|---|---|
| Chargeback administrative cost | about $128 per incident before goods | Mastercard 2025 chargeback research, via `docs/research/15-impact-report.md` | Fees plus internal labor. Excludes the lost order |
| Total cost per dollar of loss | $4.61 | LexisNexis True Cost of Fraud, 2025, N=569 | Fraud and dispute loss across retail and e-commerce, including goods and labor. Not specific to unissued refunds |
| Klarna auto-chargeback window | 96 hours after agreeing an adjustment | Klarna merchant dispute rules, via `docs/research/15-impact-report.md` | Applies to agreed order adjustments on return-not-refunded inquiries |
| Visa 13.6 win-rate uplift | about 25% to 45% with policy plus refund-attempt evidence | Travel and hospitality benchmarks, via `docs/research/15-impact-report.md` | Travel and hospitality vertical. Not general retail |

## Claims we will not make

- Prevent every agent error. We verify after execution.
- Work with every ledger. Stripe and Shopify are the rails today.
- SOC 2 certified. It is a roadmap item.
- Real merchant savings. Every proof above uses synthetic fixtures or test-mode data.
- Fully automate production remediation. Auto-remediate runs against the mock ledger only.
- Replace guardrails. We sit after execution, not before the send.

## Two numbers we retired

- The $4.61 figure was earlier written as "$5.00 and rising" from a second edition. The edition we can cite says $4.61.
- An earlier version said "100% deterministic ledger state". Reconciliation is deterministic code. Extraction is model output that is validated and fails loudly. The page now separates the two.
