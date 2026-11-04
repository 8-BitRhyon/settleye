"""Signed receipts in the money path: persist, reload, replay, never re-sign.

Signing happens after the refund. These tests pin the two guarantees that
matter: a signed envelope is durable and byte-identical on replay, and any
signing failure leaves the durable receipt in place with no second refund.
"""

import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.keyring import (
    KeyRegistry,
    default_issuer_key_path,
    default_registry_path,
    init_registry,
    verify_with_registry,
)
from app.ledger.mock import MockLedgerAdapter
from app.models import PromiseEntity, ReconciliationResult, RemediationReceipt
from app.remediate.service import RemediationService
from app.signing import ReceiptContext, build_signer_from_env
from app.value import ValueLedger

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"

TRANSCRIPT = (
    "Customer: The jacket arrived torn.\n"
    "Agent: I processed a $45 refund for order #992.\n"
)
DIGEST = hashlib.sha256(TRANSCRIPT.encode("utf-8")).hexdigest()
AUDITED_AT = "2026-01-01T00:00:00Z"
RECONCILED_SUMMARY = "Order 992: $0.00 settled of $45.00 promised."


def mock_ledger() -> MockLedgerAdapter:
    return MockLedgerAdapter(
        json.loads((FIXTURES / "mock_ledger.json").read_text())
    )


def drift_result(order_id: str = "992", amount: float = 45.00) -> ReconciliationResult:
    return ReconciliationResult(
        promise=PromiseEntity(
            action="refund",
            amount=amount,
            order_id=order_id,
            target_system="stripe",
            asserted_state="full refund processed",
            confidence=0.9,
            evidence_span="processed",
        ),
        verdict="drift",
        ledger_summary=f"Order {order_id}: $0.00 settled of ${amount:.2f} promised.",
        amount_at_risk_usd=amount,
    )


def context(**overrides: object) -> ReceiptContext:
    values: dict[str, object] = {
        "transcript_sha256": DIGEST,
        "transcript_turns": 2,
        "audited_at": AUDITED_AT,
        "ledger_summary": RECONCILED_SUMMARY,
        "model_id": "meta-models/muse-spark-open-1026",
    }
    values.update(overrides)
    return ReceiptContext(**values)  # type: ignore[arg-type]


def signer_for(key_id: str = "service-test-1"):
    init_registry(default_registry_path(), default_issuer_key_path(), key_id)
    signer = build_signer_from_env()
    assert signer is not None
    return signer


def receipt_lines(path: Path) -> list[str]:
    return [line for line in path.read_text().splitlines() if line.strip()]


def test_signed_receipt_persists_reloads_and_replays(tmp_path: Path) -> None:
    path = tmp_path / "receipts.jsonl"
    signer = signer_for()
    ledger = mock_ledger()
    value = ValueLedger()

    first = RemediationService(path, signer=signer).remediate(
        drift_result(), ledger, value, context=context()
    )
    assert first.status == "executed"
    assert first.receipt is not None
    assert ledger.refunded_usd("992") == 45.00
    assert len(receipt_lines(path)) == 1

    raw_line = json.loads(receipt_lines(path)[0])
    assert raw_line["receipt"] == first.receipt

    registry = KeyRegistry(default_registry_path())
    assert verify_with_registry(first.receipt, registry).valid is True

    # Restart: the envelope comes from the store, not from a new signature.
    restarted = RemediationService(path, signer=signer)
    found = restarted.find(first.idempotency_key)
    assert found is not None
    assert found.status == "already_executed"
    assert found.receipt == first.receipt

    replay = restarted.remediate(
        drift_result(), mock_ledger(), ValueLedger(), context=context()
    )
    assert replay.status == "already_executed"
    assert replay.receipt == first.receipt
    assert len(receipt_lines(path)) == 1


def test_signed_key_equals_durable_key_for_hash_prefixed_order(
    tmp_path: Path,
) -> None:
    """A signed envelope must never claim a key the service did not use."""
    signer = signer_for()
    result = drift_result(order_id="#992")
    ledger = mock_ledger()
    receipt = RemediationService(
        tmp_path / "receipts.jsonl", signer=signer
    ).remediate(result, ledger, ValueLedger(), context=context())
    assert receipt.receipt is not None
    assert receipt.receipt["remediation"]["idempotency_key"] == (
        receipt.idempotency_key
    )
    assert receipt.idempotency_key == "refund:992:stripe:45.00"
    # The ledger write used the bare id; the receipt kept the model's text.
    assert receipt.promise.order_id == "#992"
    assert ledger.refunded_usd("992") == 45.00


def test_without_signer_keeps_receipt_none(tmp_path: Path) -> None:
    receipt = RemediationService(tmp_path / "receipts.jsonl").remediate(
        drift_result(), mock_ledger(), ValueLedger(), context=context()
    )
    assert receipt.receipt is None


def test_without_context_keeps_receipt_none(tmp_path: Path) -> None:
    signer = signer_for()
    receipt = RemediationService(
        tmp_path / "receipts.jsonl", signer=signer
    ).remediate(drift_result(), mock_ledger(), ValueLedger())
    assert receipt.receipt is None


def test_signer_returning_none_keeps_durable_receipt(tmp_path: Path) -> None:
    path = tmp_path / "receipts.jsonl"
    signer = signer_for()
    receipt = RemediationService(path, signer=signer).remediate(
        drift_result(),
        mock_ledger(),
        ValueLedger(),
        context=context(transcript_sha256="not-a-digest"),
    )
    assert receipt.receipt is None
    assert receipt.status == "executed"
    assert len(receipt_lines(path)) == 1


class ExplodingSigner:
    def sign(self, *args: object, **kwargs: object) -> None:
        raise RuntimeError("signing backend unavailable")


def test_signer_exception_never_fails_the_refund(tmp_path: Path) -> None:
    path = tmp_path / "receipts.jsonl"
    ledger = mock_ledger()
    receipt = RemediationService(path, signer=ExplodingSigner()).remediate(  # type: ignore[arg-type]
        drift_result(), ledger, ValueLedger(), context=context()
    )
    assert receipt.receipt is None
    assert receipt.status == "executed"
    assert ledger.refunded_usd("992") == 45.00
    assert len(receipt_lines(path)) == 1

    # The store still replays safely, without a second refund.
    restarted = RemediationService(path)
    replay = restarted.remediate(
        drift_result(), mock_ledger(), ValueLedger(), context=context()
    )
    assert replay.status == "already_executed"
    assert replay.receipt is None


def test_legacy_line_without_receipt_field_still_validates(
    tmp_path: Path,
) -> None:
    path = tmp_path / "receipts.jsonl"
    legacy = RemediationReceipt(
        idempotency_key="refund:992:stripe:45.00",
        promise=drift_result().promise,
        amount_usd=45.00,
        status="executed",
    )
    raw = legacy.model_dump(mode="json")
    raw.pop("receipt")
    path.write_text(json.dumps(raw) + "\n")

    restarted = RemediationService(path)
    found = restarted.find("refund:992:stripe:45.00")
    assert found is not None
    assert found.receipt is None


def test_live_remediate_signs_only_the_reconciled_ledger_summary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    signer = signer_for("live-path-key")
    main_module.app.state.ledger = mock_ledger()
    main_module.app.state.remediation = RemediationService(
        tmp_path / "receipts.jsonl", signer=signer
    )
    main_module.app.state.value = ValueLedger()
    client = TestClient(main_module.app)

    response = client.post(
        "/remediate",
        json={
            "promise": drift_result().promise.model_dump(),
            "amount_usd": 45.00,
            "transcript_sha256": DIGEST,
            "transcript_turns": 2,
            "audited_at": AUDITED_AT,
            # A client must not be able to get this string signed.
            "ledger_summary": "BOGUS: order already refunded in full.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "executed"
    envelope = body["receipt"]
    assert envelope is not None
    assert envelope["ledger"]["summary"] == RECONCILED_SUMMARY
    assert "BOGUS" not in envelope["ledger"]["summary"]
    assert envelope["ledger"]["checked_at"] == envelope["issued_at"]
    assert envelope["ledger"]["checked_at"] != AUDITED_AT

    registry = KeyRegistry(default_registry_path())
    assert verify_with_registry(envelope, registry).valid is True

    # The same route without provenance stays backward compatible: durable
    # receipt, no signed envelope, no extra refund.
    unsigned = client.post(
        "/remediate",
        json={
            "promise": drift_result("1042", 120.00).promise.model_dump(),
            "amount_usd": 120.00,
        },
    )
    assert unsigned.status_code == 200
    assert unsigned.json()["status"] == "executed"
    assert unsigned.json()["receipt"] is None
