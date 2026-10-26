# Tangible Value by Tier: Random Seller to Enterprise

Written 2026-10-26. Rule: never promise a tier more than its incident math supports.

## Inputs (all sourced in prior reports)

- Average order value: ~$90. All-in dispute cost: $128 (Mastercard 2025, before goods).
- Prevention anchor: $15-40 merchants already pay to kill one dispute (Ethoca/RDR).
- Product records every save in the value ledger (`backend/app/value.py`): recovered dollars plus $128 per avoided dispute, totaled in the inbox header.

## Per-tier math

| Tier | Profile | Incident assumption | Monthly value | Price fit |
|---|---|---|---|---|
| Weekend seller | Under 50 orders/mo, solo | 1 phantom refund per quarter (~$45) | ~$15/mo | No subscription pays. Tangible result is episodic: "caught a $45 phantom this quarter." Serve via free tier or per-catch pricing, or say no. |
| SMB | 50-500 orders/mo, AI agent live | ~1 phantom/mo ($45-90) plus 1 dispute per quarter | ~$100-250/mo | $49-99/mo pays back roughly 1-2x. Core segment. |
| Mid-market | 500-5,000 orders/mo | 1 phantom/week ($90) plus 1 dispute per quarter plus 80 min labor saved | ~$494/mo | $99/mo, ~5x ROI, ~6-day payback. Best segment. |
| Enterprise / Plus | $1M+/yr GMV, compliance needs | 0.1% phantom rate on 10K orders = ~10 incidents/mo plus representment lift plus auditor hours | $900+/mo direct, more with win-rate lift | Custom $499-1,999/mo. Tangible result includes the exportable evidence pack, not just dollars. |

## What each tier sees in the product

- Everyone: inbox header totals ("Recovered $X across N fixes, Y disputes avoided worth $Z"), per-card evidence chain.
- SMB and up: month-to-date value vs plan cost on the dashboard. The number must exceed the price or the product has failed that merchant that month.
- Enterprise: representment-ready export (transcript snippet plus ledger snapshot plus remediation key) and quarterly reliability reporting.

## Honest boundaries

- Below ~50 orders/mo with no AI agent, there is no recurring pain and no honest subscription. Do not demo to that tier as a buyer; demo to them as the incident anecdote.
- All incident rates above are assumptions, not measurements. The reliability benchmark (planned) exists to replace them with observed drift rates.
- Dispute avoidance counts only when an alert or remediation demonstrably pre-empted a filing, never by default.
