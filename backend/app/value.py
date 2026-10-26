"""Tangible-value ledger: every remediation records dollars, not vibes.

Sources: DISPUTE_COST_USD is the Mastercard 2025 all-in internal plus
external cost per dispute ($82 + $46), before lost goods.
https://www.mastercard.com/us/en/news-and-trends/Insights/2025/what-s-the-true-cost-of-a-chargeback-in-2025.html
"""

from typing import Literal

from pydantic import BaseModel, Field

DISPUTE_COST_USD = 128.0


class Recovery(BaseModel):
    """One unit of value a remediation produced."""

    id: str
    amount_usd: float = Field(ge=0.0)
    kind: Literal["refund_recovered", "overcharge_blocked", "dispute_avoided"]


class ValueLedger(BaseModel):
    """Append-only record of what the auditor saved its merchant."""

    recoveries: list[Recovery] = Field(default_factory=list)


def summarize(ledger: ValueLedger) -> dict[str, float | int]:
    """Totals a ledger into headline numbers for the inbox header."""
    recovered = sum(
        r.amount_usd for r in ledger.recoveries if r.kind != "dispute_avoided"
    )
    avoided = sum(1 for r in ledger.recoveries if r.kind == "dispute_avoided")
    dispute_value = avoided * DISPUTE_COST_USD
    return {
        "total_recovered_usd": round(recovered, 2),
        "disputes_avoided": avoided,
        "dispute_cost_avoided_usd": round(dispute_value, 2),
        "grand_total_usd": round(recovered + dispute_value, 2),
    }
