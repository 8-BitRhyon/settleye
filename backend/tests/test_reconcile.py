"""Tests for the promise-vs-ledger diff engine.

The mock adapter reads fixtures/mock_ledger.json: order 992 shows $0
refunded (the drift case), order 1043 shows a fully settled $120 refund
(the verified case). Only refunds are reconcilable today; every other
action reports unverifiable rather than faking a verdict.
"""

import json
from pathlib import Path

from app.ledger.mock import MockLedgerAdapter
from app.models import PromiseEntity
from app.reconcile.engine import reconcile

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def ledger() -> MockLedgerAdapter:
    data = json.loads((FIXTURES / "mock_ledger.json").read_text())
    return MockLedgerAdapter(data)


def refund_promise(amount: float | None, order_id: str | None) -> PromiseEntity:
    return PromiseEntity(
        action="refund",
        amount=amount,
        order_id=order_id,
        target_system="stripe",
        asserted_state="refund processed",
        confidence=0.9,
        evidence_span="refund processed",
    )


def test_settled_refund_verifies() -> None:
    result = reconcile(refund_promise(120.00, "1043"), ledger())
    assert result.verdict == "verified"
    assert result.amount_at_risk_usd == 0.0


def test_phantom_refund_is_drift() -> None:
    result = reconcile(refund_promise(45.00, "992"), ledger())
    assert result.verdict == "drift"
    assert result.amount_at_risk_usd == 45.00
    assert "992" in result.ledger_summary


def test_partial_refund_is_drift_for_remainder() -> None:
    adapter = ledger()
    adapter.record_refund(order_id="992", amount_usd=20.00)
    result = reconcile(refund_promise(45.00, "992"), adapter)
    assert result.verdict == "drift"
    assert result.amount_at_risk_usd == 25.00


def test_hash_prefixed_order_id_still_reconciles() -> None:
    promise = refund_promise(120.00, "#1043")
    result = reconcile(promise, ledger())
    assert result.verdict == "verified"


def test_missing_order_id_is_unverifiable() -> None:
    result = reconcile(refund_promise(45.00, None), ledger())
    assert result.verdict == "unverifiable"


def test_unknown_order_is_unverifiable() -> None:
    result = reconcile(refund_promise(45.00, "0000"), ledger())
    assert result.verdict == "unverifiable"


def test_non_refund_action_is_unverifiable_not_faked() -> None:
    promise = PromiseEntity(
        action="cancel",
        amount=None,
        order_id="992",
        target_system="shopify",
        asserted_state="subscription cancelled",
        confidence=0.8,
        evidence_span="cancelled",
    )
    result = reconcile(promise, ledger())
    assert result.verdict == "unverifiable"


def test_conditional_promise_is_not_binding() -> None:
    promise = PromiseEntity(
        action="refund",
        amount=45.00,
        order_id="992",
        target_system="stripe",
        asserted_state="refund once the carrier scans",
        confidence=0.7,
        evidence_span="once the carrier scans it",
        terminal_status="conditional",
    )
    result = reconcile(promise, ledger())
    assert result.verdict == "not_binding"
    assert result.amount_at_risk_usd == 0.0


def test_retracted_promise_is_not_binding() -> None:
    promise = PromiseEntity(
        action="refund",
        amount=45.00,
        order_id="992",
        target_system="stripe",
        asserted_state="retracted, final sale",
        confidence=0.9,
        evidence_span="final sale",
        terminal_status="retracted",
    )
    result = reconcile(promise, ledger())
    assert result.verdict == "not_binding"
