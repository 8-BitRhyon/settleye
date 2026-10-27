# Eval results: 12-case extraction and gating set

Run: 2026-10-27. Model: `meta-models/muse-spark-open-1026` via Baseten.
Ledger: `fixtures/mock_ledger.json` (992 owes $45, 1042 clean, 1043 settled).
Method: daemon sweep (`app.daemon --dir fixtures/eval --ledger mock`, 42.92s)
plus per-case audit for scoring. Deterministic gating pins live in
`backend/tests/test_eval.py` (CI-safe, mocked transport).

## Headline

- Verdict and total-at-risk accuracy: **12 of 12**.
- Exact entity match vs manifest: **11 of 12**. The one miss (t07) is
  outcome-identical: the model returned `[]` where the manifest holds an
  `info_only` entity. Both reconcile to green with $0 at risk.
- Non-binding commitments (retracted, conditional, superseded, info_only)
  reached drift **0 times in 4 chances**. Failures never report success.

## Per case

| Case | Shape | Extracted | Verdict | At risk | Match |
|---|---|---|---|---|---|
| t01 | phantom $45, #992 | refund 45 binding | drift_found | $45.00 | yes |
| t02 | phantom $120, #1042 | refund 120 binding | drift_found | $120.00 | yes |
| t03 | status check | none | verified_green | $0 | yes |
| t04 | settled $120, #1043 | refund 120 binding | verified_green | $0 | yes |
| t05 | retracted refund | refund 45 retracted | verified_green | $0 | yes |
| t06 | conditional refund | refund 45 conditional | verified_green | $0 | yes |
| t07 | policy explanation | none (manifest: info_only) | verified_green | $0 | outcome-only |
| t08 | $45 corrected to $30 | superseded 45, binding 30 | drift_found | $30.00 | yes |
| t09 | no order number | refund 60, no order | verified_green | $0 | yes |
| t10 | cancellation | cancel, binding | verified_green | $0 | yes |
| t11 | status plus refund | refund 45 binding | drift_found | $45.00 | yes |
| t12 | decimal $45.50 | refund 45.50 binding | drift_found | $45.50 | yes |

## Notes

- t01 and t04 return `order_id` with a `#` prefix (`#992`, `#1043`).
  Reconcile normalizes once, so ledger keys always hit. Covered by test.
- The daemon sweep total ($285.50) equaled the manifest sum exactly:
  45 + 120 + 30 + 45 + 45.50.
- Nothing here touches real money. The mock ledger mirrors Stripe
  test-mode shapes. Live-store proof is recorded separately.
