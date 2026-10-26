"""Tests for the tangible-value ledger.

Every remediation records what it recovered or avoided, so any user from
a weekend seller to an enterprise ops lead sees dollars, not vibes.
"""

import pytest

from app.value import (
    DISPUTE_COST_USD,
    Recovery,
    ValueLedger,
    summarize,
)


def test_empty_ledger_summarizes_zero() -> None:
    summary = summarize(ValueLedger())
    assert summary["total_recovered_usd"] == 0.0
    assert summary["disputes_avoided"] == 0
    assert summary["grand_total_usd"] == 0.0


def test_phantom_refund_recovery_counts() -> None:
    ledger = ValueLedger(recoveries=[
        Recovery(id="r1", amount_usd=45.00, kind="refund_recovered"),
    ])
    summary = summarize(ledger)
    assert summary["total_recovered_usd"] == 45.00
    assert summary["grand_total_usd"] == 45.00


def test_avoided_dispute_uses_published_cost() -> None:
    assert DISPUTE_COST_USD == 128.0
    ledger = ValueLedger(recoveries=[
        Recovery(id="r1", amount_usd=0.0, kind="dispute_avoided"),
    ])
    summary = summarize(ledger)
    assert summary["disputes_avoided"] == 1
    assert summary["dispute_cost_avoided_usd"] == 128.0
    assert summary["grand_total_usd"] == 128.0


def test_mixed_month_totals() -> None:
    ledger = ValueLedger(recoveries=[
        Recovery(id="r1", amount_usd=45.00, kind="refund_recovered"),
        Recovery(id="r2", amount_usd=120.00, kind="overcharge_blocked"),
        Recovery(id="r3", amount_usd=0.0, kind="dispute_avoided"),
    ])
    summary = summarize(ledger)
    assert summary["total_recovered_usd"] == 165.00
    assert summary["disputes_avoided"] == 1
    assert summary["grand_total_usd"] == 165.00 + 128.0


def test_unknown_kind_rejected() -> None:
    with pytest.raises(ValueError):
        Recovery(id="r9", amount_usd=10.0, kind="time_travel")  # type: ignore[arg-type]
