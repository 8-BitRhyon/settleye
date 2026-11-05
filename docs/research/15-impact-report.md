# Borrowed impact inputs

This note records the external numbers used on the landing page and in the fleet projection model. These are borrowed inputs, not merchant measurements. The underlying reports are external and are not redistributed in this repository.

## Inputs

| Input | Value | Source | Qualifier |
|---|---|---|---|
| Chargeback administrative cost | about $128 per incident before goods | Mastercard 2025 chargeback research | Fees plus internal labor. Excludes the lost order. |
| Total cost per dollar of loss | $4.61 | LexisNexis True Cost of Fraud, 2025, N=569 | Fraud and dispute loss across retail and e-commerce, including goods and labor. Not specific to unissued refunds. |
| Klarna auto-chargeback window | 96 hours after agreeing an adjustment | Klarna merchant dispute rules | Applies to agreed order adjustments on return-not-refunded inquiries. |
| Visa 13.6 win-rate uplift | about 25% to 45% with policy plus refund-attempt evidence | Travel and hospitality benchmarks | Travel and hospitality vertical. Not general retail. |

## How the model uses them

- The `$128` fee is applied once per modeled drift in the chargeback-fee column.
- The `4.61x` multiplier is applied to modeled direct refund exposure in the dispute column.
- The Klarna window explains why a fast settlement matters for agreed adjustments.
- The Visa range informs the dispute-evidence argument. It is not used as a projection input.

## What this note does not claim

- These numbers are not measured on a Settleye merchant.
- They do not guarantee a recovery, a win rate, or a savings amount.
- They do not replace a merchant's own fee schedule, dispute history, or refund policy.
- The fleet table is a projection from stated assumptions. It is not a merchant result.

## Where the numbers appear

- `docs/research/20-claims.md`: claim ledger with scope notes.
- `bench/fleet_projection.py`: deterministic projection model.
- `frontend/landing.html`: sources and scope strip.
- `README.md`: modeled fleet table and assumptions.
