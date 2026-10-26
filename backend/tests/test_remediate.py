"""Tests for audit orchestration and one-click remediation.

The mock transport stands in for the Meta model; the mock ledger stands in
for Stripe test mode. Double-execution is the cardinal sin under test: the
second identical remediation must be a no-op receipt, never a second refund.
"""

import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.extract.client import MetaModelClient
from app.ledger.mock import MockLedgerAdapter
from app.models import PromiseEntity, ReconciliationResult
from app.remediate.service import RemediationError, RemediationService
from app.value import ValueLedger

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"

PHANTOM_JSON = json.dumps([
    {
        "action": "refund",
        "amount": 45.00,
        "order_id": "992",
        "target_system": "stripe",
        "asserted_state": "full refund processed",
        "confidence": 0.9,
        "evidence_span": "I have processed a full $45 refund for order #992.",
    }
])


def mock_client(reply: str) -> MetaModelClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": reply}}], "model": "test"},
        )

    return MetaModelClient(api_key="k", transport=httpx.MockTransport(handler))


def mock_ledger() -> MockLedgerAdapter:
    data = json.loads((FIXTURES / "mock_ledger.json").read_text())
    return MockLedgerAdapter(data)


def drift_result() -> ReconciliationResult:
    return ReconciliationResult(
        promise=PromiseEntity(
            action="refund",
            amount=45.00,
            order_id="992",
            target_system="stripe",
            asserted_state="full refund processed",
            confidence=0.9,
            evidence_span="processed",
        ),
        verdict="drift",
        ledger_summary="Order 992: $0.00 settled of $45.00 promised.",
        amount_at_risk_usd=45.00,
    )


def test_remediate_executes_and_closes_drift() -> None:
    ledger = mock_ledger()
    service = RemediationService()
    receipt = service.remediate(drift_result(), ledger, ValueLedger())
    assert receipt.status == "executed"
    assert receipt.amount_usd == 45.00
    assert ledger.refunded_usd("992") == 45.00


def test_remediate_twice_is_idempotent() -> None:
    ledger = mock_ledger()
    service = RemediationService()
    value = ValueLedger()
    first = service.remediate(drift_result(), ledger, value)
    second = service.remediate(drift_result(), ledger, value)
    assert second.status == "already_executed"
    assert second.idempotency_key == first.idempotency_key
    assert ledger.refunded_usd("992") == 45.00
    assert len(value.recoveries) == 1


def test_remediate_non_drift_raises() -> None:
    verified = drift_result().model_copy(update={"verdict": "verified"})
    with pytest.raises(RemediationError):
        RemediationService().remediate(verified, mock_ledger(), ValueLedger())


async def test_audit_phantom_transcript_reports_drift() -> None:
    from app.audit import audit_transcript

    report = await audit_transcript(
        "I have processed a full $45 refund for order #992.",
        mock_client(PHANTOM_JSON),
        mock_ledger(),
    )
    assert len(report.promises) == 1
    assert len(report.drifts) == 1
    assert report.total_at_risk_usd == 45.00


async def test_audit_happy_transcript_is_green() -> None:
    from app.audit import audit_transcript

    report = await audit_transcript(
        "Order shipped, thanks, bye.", mock_client("[]"), mock_ledger()
    )
    assert report.promises == []
    assert report.drifts == []
    assert report.verdict == "verified_green"


def fresh_app_state() -> TestClient:
    main_module.app.state.ledger = mock_ledger()
    main_module.app.state.remediation = RemediationService()
    main_module.app.state.value = ValueLedger()
    return TestClient(main_module.app)


def test_routes_audit_and_remediate_and_value(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module, "build_client", lambda: mock_client(PHANTOM_JSON)
    )
    client = fresh_app_state()
    audit = client.post(
        "/audit", json={"transcript": "refund $45 order #992, done."}
    )
    assert audit.status_code == 200
    assert audit.json()["total_at_risk_usd"] == 45.00

    fix = client.post(
        "/remediate",
        json={
            "promise": drift_result().promise.model_dump(),
            "amount_usd": 45.00,
        },
    )
    assert fix.status_code == 200
    assert fix.json()["status"] == "executed"

    again = client.post(
        "/remediate",
        json={
            "promise": drift_result().promise.model_dump(),
            "amount_usd": 45.00,
        },
    )
    assert again.json()["status"] == "already_executed"

    value = client.get("/value")
    assert value.json()["grand_total_usd"] == 45.00


def test_routes_reject_garbage_extraction(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module, "build_client", lambda: mock_client("garbage{{{")
    )
    client = fresh_app_state()
    response = client.post("/audit", json={"transcript": "whatever"})
    assert response.status_code == 422


def test_routes_reject_over_refund(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module, "build_client", lambda: mock_client(PHANTOM_JSON)
    )
    client = fresh_app_state()
    response = client.post(
        "/remediate",
        json={
            "promise": drift_result().promise.model_dump(),
            "amount_usd": 999.00,
        },
    )
    assert response.status_code == 422
    assert "mismatch" in response.json()["detail"]
