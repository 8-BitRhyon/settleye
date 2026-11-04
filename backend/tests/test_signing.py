"""Signer behavior: bind exactly the audit + fresh ledger facts, or refuse.

The signer is the last place where the issuer can decline a claim, so every
validation here is a fail-closed rule, not a convenience.
"""

import hashlib

from app.keyring import (
    KeyRegistry,
    default_issuer_key_path,
    default_registry_path,
    init_registry,
    write_private_key,
)
from app.models import PromiseEntity
from app.receipt import generate_keypair, verify_receipt
from app.signing import (
    ReceiptContext,
    ReceiptSigner,
    build_signer_from_env,
)

TRANSCRIPT = (
    "Customer: The jacket arrived torn.\n"
    "Agent: I processed a $45 refund for order #992.\n"
)
DIGEST = hashlib.sha256(TRANSCRIPT.encode("utf-8")).hexdigest()
AUDITED_AT = "2026-01-01T00:00:00Z"
MODEL = "meta-models/muse-spark-open-1026"


def promise(amount: float | None = 45.0) -> PromiseEntity:
    return PromiseEntity(
        action="refund",
        amount=amount,
        order_id="#992",
        target_system="stripe",
        asserted_state="full refund processed",
        confidence=0.9,
        evidence_span="I processed a $45 refund for order #992.",
    )


def context(**overrides: object) -> ReceiptContext:
    values: dict[str, object] = {
        "transcript_sha256": DIGEST,
        "transcript_turns": 2,
        "audited_at": AUDITED_AT,
        "ledger_summary": "Order 992: $0.00 settled of $45.00 promised.",
        "model_id": MODEL,
    }
    values.update(overrides)
    return ReceiptContext(**values)  # type: ignore[arg-type]


def registered_signer(key_id: str = "signer-test-1") -> ReceiptSigner:
    init_registry(default_registry_path(), default_issuer_key_path(), key_id)
    signer = build_signer_from_env()
    assert signer is not None
    return signer


def test_envelope_verifies_against_its_registered_public_key() -> None:
    signer = registered_signer()
    envelope = signer.sign(promise(), 45.0, "executed", context())
    assert envelope is not None

    record = KeyRegistry(default_registry_path()).active_key()
    assert record is not None
    result = verify_receipt(
        envelope,
        pinned_public_key=record.public_key,
        expected_key_id=record.key_id,
    )
    assert result.valid is True
    assert result.reason == "ok"

    assert envelope["issuer"] == {"name": "Settleye", "key_id": record.key_id}
    assert envelope["agent"]["model_id"] == MODEL
    assert envelope["transcript"] == {"sha256": DIGEST, "turns": 2}
    assert envelope["promise"]["order_id"] == "992"
    assert envelope["promise"]["amount"] == "45.00"
    # The signed key must equal the durable receipt's key, which the service
    # derives from the raw promise order id. The payload may normalize the
    # display order id, but the idempotency key is never rewritten.
    assert envelope["remediation"] == {
        "idempotency_key": "refund:#992:stripe:45.00",
        "amount_usd": "45.00",
        "status": "executed",
    }
    assert (
        envelope["ledger"]["summary"]
        == "Order 992: $0.00 settled of $45.00 promised."
    )


def test_checked_at_is_signing_time_not_older_audit_time() -> None:
    signer = registered_signer()
    envelope = signer.sign(promise(), 45.0, "executed", context())
    assert envelope is not None
    assert envelope["ledger"]["checked_at"] == envelope["issued_at"]
    assert envelope["ledger"]["checked_at"] != AUDITED_AT
    assert envelope["ledger"]["checked_at"].endswith("Z")


def test_bad_digest_or_zero_turns_returns_none() -> None:
    signer = registered_signer()
    assert signer.sign(promise(), 45.0, "executed", context()) is not None

    for bad_digest in ("", "xyz", "A" * 64, "a" * 63, "a" * 65, f" {DIGEST}"):
        assert (
            signer.sign(
                promise(),
                45.0,
                "executed",
                context(transcript_sha256=bad_digest),
            )
            is None
        )
    assert (
        signer.sign(promise(), 45.0, "executed", context(transcript_turns=0))
        is None
    )
    assert signer.sign(promise(), 45.0, "executed", context(transcript_turns=-1)) is None


def test_missing_context_returns_none() -> None:
    signer = registered_signer()
    assert signer.sign(promise(), 45.0, "executed", None) is None


def test_fallback_amount_when_promise_has_no_amount() -> None:
    signer = registered_signer()
    envelope = signer.sign(promise(amount=None), 30.0, "executed", context())
    assert envelope is not None
    assert envelope["promise"]["amount"] == "30.00"
    assert envelope["remediation"]["idempotency_key"] == (
        "refund:#992:stripe:30.00"
    )


def test_build_signer_without_files_returns_none() -> None:
    assert build_signer_from_env() is None


def test_build_signer_with_mismatched_private_key_returns_none() -> None:
    registered_signer()
    other_private, _ = generate_keypair()
    write_private_key(default_issuer_key_path(), other_private)
    assert build_signer_from_env() is None
