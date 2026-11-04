"""Tests for audit orchestration and one-click remediation.

The mock transport stands in for the Meta model; the mock ledger stands in
for Stripe test mode. Double-execution is the cardinal sin under test: the
second identical remediation must be a no-op receipt, never a second refund.
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.extract.client import MetaModelClient
from app.ledger.mock import MockLedgerAdapter
from app.models import PromiseEntity, ReconciliationResult, RemediationReceipt
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


class RecordingLedger(MockLedgerAdapter):
    """Mock ledger that remembers every refund write."""

    def __init__(self, data: dict) -> None:
        super().__init__(data)
        self.refunds: list[tuple[str, float]] = []

    def record_refund(self, order_id: str, amount_usd: float) -> dict:
        self.refunds.append((order_id, amount_usd))
        return super().record_refund(order_id, amount_usd)


def recording_ledger() -> RecordingLedger:
    return RecordingLedger(json.loads((FIXTURES / "mock_ledger.json").read_text()))


def partial_result(promised: float, shortfall: float) -> ReconciliationResult:
    """A refund promise with a live shortfall that can move after a partial."""
    return ReconciliationResult(
        promise=PromiseEntity(
            action="refund",
            amount=promised,
            order_id="992",
            target_system="stripe",
            asserted_state="partial refund processed",
            confidence=0.9,
            evidence_span="I processed part of the refund.",
        ),
        verdict="drift",
        ledger_summary=(
            f"Order 992: ${promised - shortfall:.2f} settled of "
            f"${promised:.2f} promised."
        ),
        amount_at_risk_usd=shortfall,
    )


def receipt_lines(path: Path) -> list[str]:
    return [line for line in path.read_text().splitlines() if line.strip()]


def test_receipts_survive_process_restart(tmp_path) -> None:
    path = tmp_path / "receipts.jsonl"
    first_ledger = recording_ledger()
    first = RemediationService(path).remediate(
        drift_result(), first_ledger, ValueLedger()
    )
    assert first.status == "executed"
    assert first_ledger.refunds == [("992", 45.00)]

    # A new process: fresh service and fresh ledger, same receipt store.
    second_ledger = recording_ledger()
    second = RemediationService(path).remediate(
        drift_result(), second_ledger, ValueLedger()
    )
    assert second.status == "already_executed"
    assert second.idempotency_key == first.idempotency_key
    assert second_ledger.refunds == []
    assert len(receipt_lines(path)) == 1


def test_hash_prefixed_order_reaches_the_ledger_without_the_hash(
    tmp_path,
) -> None:
    """The model speaks "#992"; reconciliation and writes use the bare key."""
    path = tmp_path / "receipts.jsonl"
    ledger = recording_ledger()
    service = RemediationService(path)
    result = drift_result().model_copy(
        update={
            "promise": drift_result().promise.model_copy(
                update={"order_id": "#992"}
            )
        }
    )

    first = service.remediate(result, ledger, ValueLedger())
    assert first.status == "executed"
    assert first.promise.order_id == "#992"
    assert first.idempotency_key == "refund:992:stripe:45.00"
    assert ledger.refunds == [("992", 45.00)]
    assert ledger.refunded_usd("992") == 45.00

    replay = service.remediate(result, ledger, ValueLedger())
    assert replay.status == "already_executed"
    assert replay.idempotency_key == first.idempotency_key
    assert ledger.refunds == [("992", 45.00)]
    assert len(receipt_lines(path)) == 1


def test_hash_prefix_and_bare_order_share_one_key(tmp_path) -> None:
    """The same order cannot mint two keys by changing "#992" to "992"."""
    path = tmp_path / "receipts.jsonl"
    ledger = recording_ledger()
    service = RemediationService(path)
    hashed = drift_result().model_copy(
        update={
            "promise": drift_result().promise.model_copy(
                update={"order_id": "#992"}
            )
        }
    )

    first = service.remediate(hashed, ledger, ValueLedger())
    second = service.remediate(drift_result(), ledger, ValueLedger())

    assert first.idempotency_key == "refund:992:stripe:45.00"
    assert second.idempotency_key == first.idempotency_key
    assert second.status == "already_executed"
    assert ledger.refunds == [("992", 45.00)]
    assert len(receipt_lines(path)) == 1


def test_legacy_hash_key_is_still_found(tmp_path) -> None:
    """A store written before normalization must not forget a refund."""
    path = tmp_path / "receipts.jsonl"
    legacy = RemediationReceipt(
        idempotency_key="refund:#992:stripe:45.00",
        promise=drift_result().promise,
        amount_usd=45.00,
        status="executed",
    )
    path.write_text(legacy.model_dump_json() + "\n")
    service = RemediationService(path)

    found = service.find("refund:992:stripe:45.00")
    assert found is not None
    assert found.status == "already_executed"
    assert found.idempotency_key == "refund:#992:stripe:45.00"


def test_partial_refund_never_authorizes_a_second_refund(tmp_path) -> None:
    path = tmp_path / "receipts.jsonl"
    ledger = recording_ledger()
    value = ValueLedger()
    service = RemediationService(path)

    first = service.remediate(partial_result(50.00, 44.00), ledger, value)
    second = service.remediate(partial_result(50.00, 30.00), ledger, value)

    assert first.status == "executed"
    assert first.idempotency_key == "refund:992:stripe:50.00"
    assert second.status == "already_executed"
    assert second.idempotency_key == first.idempotency_key
    assert second.amount_usd == 44.00
    assert ledger.refunds == [("992", 44.00)]
    assert len(receipt_lines(path)) == 1
    assert len(value.recoveries) == 1


def test_two_different_promises_append_two_receipts(tmp_path) -> None:
    path = tmp_path / "receipts.jsonl"
    ledger = recording_ledger()
    value = ValueLedger()
    service = RemediationService(path)

    first = service.remediate(drift_result(), ledger, value)
    second_result = drift_result().model_copy(
        update={
            "promise": drift_result().promise.model_copy(
                update={"order_id": "1042", "amount": 120.00}
            ),
            "amount_at_risk_usd": 120.00,
            "ledger_summary": "Order 1042: $0.00 settled of $120.00 promised.",
        }
    )
    second = service.remediate(second_result, ledger, value)

    assert first.idempotency_key != second.idempotency_key
    assert ledger.refunds == [("992", 45.00), ("1042", 120.00)]
    assert len(receipt_lines(path)) == 2

    reloaded = RemediationService(path)
    assert reloaded.find(first.idempotency_key) is not None
    assert reloaded.find(second.idempotency_key) is not None


def test_non_drift_refuses_and_writes_nothing(tmp_path) -> None:
    path = tmp_path / "receipts.jsonl"
    ledger = recording_ledger()
    verified = drift_result().model_copy(
        update={"verdict": "verified", "amount_at_risk_usd": 0.0}
    )

    with pytest.raises(RemediationError):
        RemediationService(path).remediate(verified, ledger, ValueLedger())

    assert ledger.refunds == []
    assert not path.exists()


def test_corrupt_receipt_file_fails_closed(tmp_path) -> None:
    path = tmp_path / "receipts.jsonl"
    path.write_text("this is not json\n")

    with pytest.raises(RemediationError, match="corrupt"):
        RemediationService(path)


def test_wrong_shape_receipt_file_fails_closed(tmp_path) -> None:
    path = tmp_path / "receipts.jsonl"
    path.write_text('{"idempotency_key": "refund:992:stripe:45.00"}\n')

    with pytest.raises(RemediationError, match="corrupt"):
        RemediationService(path)


def test_api_receipts_survive_restart(isolated_receipts) -> None:
    path = isolated_receipts
    ledger = mock_ledger()
    main_module.app.state.ledger = ledger
    main_module.app.state.remediation = RemediationService(path)
    main_module.app.state.value = ValueLedger()
    client = TestClient(main_module.app)

    first = client.post(
        "/remediate",
        json={
            "promise": drift_result().promise.model_dump(),
            "amount_usd": 45.00,
        },
    )
    assert first.status_code == 200
    assert first.json()["status"] == "executed"

    # Restart the service against the same store; the ledger stays settled.
    main_module.app.state.remediation = RemediationService(path)
    second = client.post(
        "/remediate",
        json={
            "promise": drift_result().promise.model_dump(),
            "amount_usd": 45.00,
        },
    )
    assert second.status_code == 200
    assert second.json()["status"] == "already_executed"
    assert ledger.refunded_usd("992") == 45.00
    assert len(receipt_lines(path)) == 1


def test_api_reuses_service_key_after_partial_refund(isolated_receipts) -> None:
    path = isolated_receipts
    ledger = mock_ledger()

    # The service already executed the first pass on a $50 promise,
    # leaving $44 settled and a live shortfall of $6.
    RemediationService(path).remediate(
        partial_result(50.00, 44.00), ledger, ValueLedger()
    )
    assert ledger.refunded_usd("992") == 44.00
    main_module.app.state.ledger = ledger
    main_module.app.state.remediation = RemediationService(path)
    main_module.app.state.value = ValueLedger()

    # The live shortfall is now $6, but the key must still be the promise.
    response = TestClient(main_module.app).post(
        "/remediate",
        json={
            "promise": partial_result(50.00, 30.00).promise.model_dump(),
            "amount_usd": 6.00,
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "already_executed"
    assert ledger.refunded_usd("992") == 44.00
    assert len(receipt_lines(path)) == 1


def test_tampered_amount_rejected_without_receipt(
    monkeypatch, isolated_receipts
) -> None:
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
    assert not isolated_receipts.exists()


def test_tampered_amount_rejected_even_after_execution(isolated_receipts) -> None:
    path = isolated_receipts
    ledger = mock_ledger()
    main_module.app.state.ledger = ledger
    main_module.app.state.remediation = RemediationService(path)
    main_module.app.state.value = ValueLedger()
    client = TestClient(main_module.app)

    first = client.post(
        "/remediate",
        json={
            "promise": drift_result().promise.model_dump(),
            "amount_usd": 45.00,
        },
    )
    assert first.status_code == 200

    over = client.post(
        "/remediate",
        json={
            "promise": drift_result().promise.model_dump(),
            "amount_usd": 999.00,
        },
    )
    assert over.status_code == 422
    assert "mismatch" in over.json()["detail"]
    assert ledger.refunded_usd("992") == 45.00
    assert len(receipt_lines(path)) == 1



def test_concurrent_identical_remediations_move_money_once(tmp_path) -> None:
    """Two threads that both pass `find` must not both reach the ledger."""
    class SlowLedger(RecordingLedger):
        def record_refund(self, order_id: str, amount_usd: float) -> dict:
            time.sleep(0.1)
            return super().record_refund(order_id, amount_usd)

    path = tmp_path / "receipts.jsonl"
    ledger = SlowLedger(json.loads((FIXTURES / "mock_ledger.json").read_text()))
    service = RemediationService(path)
    result = drift_result()

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(
            pool.map(
                lambda _: service.remediate(
                    result, ledger, ValueLedger()
                ).status,
                range(2),
            )
        )

    assert sorted(statuses) == ["already_executed", "executed"]
    assert ledger.refunds == [("992", 45.00)]
    assert len(receipt_lines(path)) == 1


def test_forged_promise_cannot_refund_past_the_charge() -> None:
    """A larger promise after a full refund must not unlock more money."""
    client = fresh_app_state()
    first = client.post(
        "/remediate",
        json={
            "promise": drift_result().promise.model_dump(),
            "amount_usd": 45.00,
            "transcript_sha256": "a" * 64,
            "transcript_turns": 3,
        },
    )
    assert first.status_code == 200

    forged_promise = drift_result().promise.model_dump()
    forged_promise["amount"] = 90.00
    forged = client.post(
        "/remediate",
        json={
            "promise": forged_promise,
            "amount_usd": 45.00,
            "transcript_sha256": "a" * 64,
            "transcript_turns": 3,
        },
    )
    assert forged.status_code == 422
    assert "exceed the original charge" in forged.json()["detail"]
    assert main_module.app.state.ledger.refunded_usd("992") == 45.00


def test_legacy_pre_rail_key_is_still_found(tmp_path) -> None:
    """A store from before the rail-qualified key must not re-execute."""
    path = tmp_path / "receipts.jsonl"
    legacy = RemediationReceipt(
        idempotency_key="refund:992:45.00",
        promise=drift_result().promise,
        amount_usd=45.00,
        status="executed",
    )
    path.write_text(legacy.model_dump_json() + "\n")
    service = RemediationService(path)

    found = service.find("refund:992:stripe:45.00")
    assert found is not None
    assert found.status == "already_executed"
    assert found.idempotency_key == "refund:992:45.00"
