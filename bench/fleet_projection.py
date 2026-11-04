#!/usr/bin/env python3
"""Settleye enterprise fleet impact projection tool.

Models unexecuted agent drift volume, direct dollars at risk, card dispute
exposure, and chargeback fee savings across enterprise volume tiers.

Grounding parameters:
- 10.6% refund intent rate (ABCD dialogue baseline)
- 66.7% binding commitment rate (agent commitments)
- 4.0% agent tool-call execution failure rate (drift)
- $52.50 average refund commitment
- LexisNexis $4.61 true-cost-of-fraud/dispute multiplier
- $128 Mastercard dispute/chargeback admin fee

Usage:
    python3 bench/fleet_projection.py [--format {both,markdown,json}] [--tickets N]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Empirical constants
REFUND_INTENT_RATE = 0.106  # 10.6% tickets contain refund intent
BINDING_COMMITMENT_RATE = 0.667  # 66.7% of intent leads to binding commitment
EXECUTION_FAILURE_RATE = 0.040  # 4.0% agent tool execution failure / drift
AVG_REFUND_COMMITMENT_USD = 52.50  # Average refund commitment
LEXIS_NEXIS_MULTIPLIER = 4.61  # True cost multiplier per unfulfilled dollar
MASTERCARD_CHARGEBACK_FEE_USD = 128.00  # Card brand administrative dispute fee


@dataclass
class TierProjection:
    tier_name: str
    monthly_tickets: int
    annual_tickets: int
    monthly_drift_events: int
    annual_drift_events: int
    monthly_direct_dollars_usd: float
    annual_direct_dollars_usd: float
    monthly_dispute_exposure_usd: float
    annual_dispute_exposure_usd: float
    monthly_chargeback_fees_usd: float
    annual_chargeback_fees_usd: float
    monthly_total_savings_usd: float
    annual_total_savings_usd: float


def project_tier(name: str, monthly_tickets: int) -> TierProjection:
    """Calculate projected metrics for a monthly ticket volume tier."""
    refund_intent = monthly_tickets * REFUND_INTENT_RATE
    binding = refund_intent * BINDING_COMMITMENT_RATE
    monthly_drifts = round(binding * EXECUTION_FAILURE_RATE)
    annual_drifts = monthly_drifts * 12

    monthly_direct = round(monthly_drifts * AVG_REFUND_COMMITMENT_USD, 2)
    annual_direct = round(monthly_direct * 12, 2)

    monthly_dispute = round(monthly_direct * LEXIS_NEXIS_MULTIPLIER, 2)
    annual_dispute = round(monthly_dispute * 12, 2)

    monthly_cb = round(monthly_drifts * MASTERCARD_CHARGEBACK_FEE_USD, 2)
    annual_cb = round(monthly_cb * 12, 2)

    monthly_total = round(monthly_dispute + monthly_cb, 2)
    annual_total = round(monthly_total * 12, 2)

    return TierProjection(
        tier_name=name,
        monthly_tickets=monthly_tickets,
        annual_tickets=monthly_tickets * 12,
        monthly_drift_events=monthly_drifts,
        annual_drift_events=annual_drifts,
        monthly_direct_dollars_usd=monthly_direct,
        annual_direct_dollars_usd=annual_direct,
        monthly_dispute_exposure_usd=monthly_dispute,
        annual_dispute_exposure_usd=annual_dispute,
        monthly_chargeback_fees_usd=monthly_cb,
        annual_chargeback_fees_usd=annual_cb,
        monthly_total_savings_usd=monthly_total,
        annual_total_savings_usd=annual_total,
    )


def compute_projections(custom_tickets: int | None = None) -> dict[str, Any]:
    """Compute enterprise projection report across tiers."""
    tiers = [
        project_tier("Mid-Market", 10_000),
        project_tier("Large E-Commerce", 100_000),
        project_tier("Global Enterprise", 1_000_000),
    ]
    if custom_tickets is not None:
        tiers.append(project_tier("Custom Scope", custom_tickets))

    return {
        "model": "settleye_enterprise_impact_projection",
        "methodology": {
            "refund_intent_rate": f"{REFUND_INTENT_RATE * 100:.1f}% (ABCD dialogue corpus)",
            "binding_commitment_rate": f"{BINDING_COMMITMENT_RATE * 100:.1f}% (agent commitment rate)",
            "tool_call_failure_rate": f"{EXECUTION_FAILURE_RATE * 100:.1f}% (unexecuted action drift)",
            "average_refund_usd": f"${AVG_REFUND_COMMITMENT_USD:.2f}",
            "dispute_multiplier": f"{LEXIS_NEXIS_MULTIPLIER}x (LexisNexis True Cost of Fraud)",
            "chargeback_fee_usd": f"${MASTERCARD_CHARGEBACK_FEE_USD:.2f} (Mastercard dispute admin fee)",
        },
        "live_proof_anchor": {
            "order_id": "#1001",
            "amount_caught_usd": 44.00,
            "status": "drift_reconciled_live",
            "ledger": "shopify_dev_store",
            "context": "Empirical single-order catch verified live on Shopify test store.",
        },
        "tiers": [asdict(t) for t in tiers],
    }


def format_markdown_table(data: dict[str, Any]) -> str:
    """Format projections as a readable markdown table."""
    lines = [
        "### Settleye Enterprise Fleet Impact Projections",
        "",
        "| Volume Tier | Monthly Tickets | Annual Drift Events | Direct Dollars Caught | Dispute Loss Prevention | Chargeback Fee Savings | Total Annual Enterprise Value |",
        "|---|---|---|---|---|---|---|",
    ]
    for t in data["tiers"]:
        lines.append(
            f"| **{t['tier_name']}** "
            f"| {t['monthly_tickets']:,}/mo "
            f"| {t['annual_drift_events']:,} drifts/yr "
            f"| ${t['annual_direct_dollars_usd']:,.2f} "
            f"| ${t['annual_dispute_exposure_usd']:,.2f} "
            f"| ${t['annual_chargeback_fees_usd']:,.2f} "
            f"| **${t['annual_total_savings_usd']:,.2f}** |"
        )

    lines.extend([
        "",
        "#### Empirical Basis & Live Proof Anchor",
        "- **Live Proof Anchor**: Order #1001 ($44.00 unfulfilled refund caught in real time on live Shopify dev store).",
        "- **Drift Funnel**: 10.6% refund intent -> 66.7% binding commitment -> 4.0% agent tool-call execution failure.",
        "- **Dispute Multiplier**: LexisNexis 4.61x true cost of unfulfilled consumer claims (support churn, investigation, chargebacks).",
        "- **Card Network Fees**: $128.00 per formal chargeback filing under card brand dispute schedule.",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Settleye enterprise fleet impact projection tool."
    )
    parser.add_argument(
        "--format",
        choices=["both", "markdown", "json"],
        default="both",
        help="Output format: both, markdown, or json (default: both).",
    )
    parser.add_argument(
        "--tickets",
        type=int,
        default=None,
        help="Optional custom monthly ticket volume to project.",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Optional path to write JSON projection.",
    )
    args = parser.parse_args(argv)

    data = compute_projections(custom_tickets=args.tickets)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    if args.format in ("markdown", "both"):
        print(format_markdown_table(data))
        if args.format == "both":
            print()

    if args.format in ("json", "both"):
        print("```json")
        print(json.dumps(data, indent=2))
        print("```")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
