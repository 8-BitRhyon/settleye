"""Signed receipt contract: the sample verifies, every edit fails closed.

The pinned fixture values are frozen on purpose. The frontend pins this
public key, so regenerating the keypair must break a test, not the demo.
"""

import copy
import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.receipt import (
    INVALID_PUBLIC_KEY,
    INVALID_SIGNATURE,
    KEY_ID_MISMATCH,
    MALFORMED,
    PINNED_KEY_MISMATCH,
    RECEIPT_ID_MISMATCH,
    SIGNATURE_INVALID,
    SAMPLE_TRANSCRIPT,
    UNSUPPORTED_ALG,
    canonical_payload,
    encode_public_key,
    generate_keypair,
    receipt_id_for,
    sign_receipt,
    verify_receipt,
)

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_RECEIPT = FIXTURES / "sample_receipt.json"
SAMPLE_PUBLIC_KEY = FIXTURES / "sample_receipt_public_key.txt"

FROZEN_PUBLIC_KEY = "iJhnbifaIiqARhsqgrjoXRgM2Y_oBYrAuAmBs2Sn5T0"
FROZEN_RECEIPT_ID = (
    "sha256:df3f410be43689329b69705c9534f14035a82b32c1b6383986788bf559e4347b"
)
KEY_ID = "settleye-demo-2026-11"


def sample() -> dict[str, Any]:
    return json.loads(SAMPLE_RECEIPT.read_text())


def pinned() -> str:
    return SAMPLE_PUBLIC_KEY.read_text().splitlines()[0].strip()


def test_sample_receipt_verifies_with_pinned_key() -> None:
    result = verify_receipt(
        sample(), pinned_public_key=pinned(), expected_key_id=KEY_ID
    )
    assert result.valid is True
    assert result.reason == "ok"
    assert result.receipt_id == FROZEN_RECEIPT_ID
    assert result.key_id == KEY_ID


def test_sample_binds_the_exact_transcript_bytes() -> None:
    envelope = sample()
    digest = hashlib.sha256(SAMPLE_TRANSCRIPT.encode("utf-8")).hexdigest()
    assert envelope["transcript"]["sha256"] == digest
    assert envelope["transcript"]["turns"] == SAMPLE_TRANSCRIPT.count("\n")
    assert envelope["issued_at"] == "2026-11-04T12:00:00Z"
    assert envelope["signature"]["alg"] == "Ed25519"
    assert envelope["issuer"] == {"name": "Settleye", "key_id": KEY_ID}


def test_pinned_fixture_values_are_frozen() -> None:
    envelope = sample()
    assert pinned() == FROZEN_PUBLIC_KEY
    assert envelope["signature"]["public_key"] == FROZEN_PUBLIC_KEY
    assert envelope["receipt_id"] == FROZEN_RECEIPT_ID
    assert receipt_id_for(envelope) == FROZEN_RECEIPT_ID


def test_tampered_promise_amount_fails() -> None:
    envelope = sample()
    envelope["promise"]["amount"] = "145.00"
    result = verify_receipt(envelope, pinned_public_key=pinned())
    assert result.valid is False
    assert result.reason == RECEIPT_ID_MISMATCH
    # The recomputed id exposes the real digest of the edited bytes.
    assert result.receipt_id != FROZEN_RECEIPT_ID


def test_tampered_payload_with_updated_id_still_fails_signature() -> None:
    envelope = sample()
    envelope["ledger"]["shortfall_usd"] = "0.00"
    envelope["receipt_id"] = receipt_id_for(envelope)
    result = verify_receipt(envelope, pinned_public_key=pinned())
    assert result.valid is False
    assert result.reason == SIGNATURE_INVALID


def test_wrong_public_key_fails() -> None:
    _, other_public_key = generate_keypair()
    result = verify_receipt(
        sample(), pinned_public_key=encode_public_key(other_public_key)
    )
    assert result.valid is False
    assert result.reason == PINNED_KEY_MISMATCH


def test_receipt_id_mismatch_fails() -> None:
    envelope = sample()
    envelope["receipt_id"] = "sha256:" + "0" * 64
    result = verify_receipt(envelope, pinned_public_key=pinned())
    assert result.valid is False
    assert result.reason == RECEIPT_ID_MISMATCH


def test_key_id_mismatch_fails() -> None:
    result = verify_receipt(
        sample(), pinned_public_key=pinned(), expected_key_id="settleye-other"
    )
    assert result.valid is False
    assert result.reason == KEY_ID_MISMATCH


def test_value_coercion_cannot_normalize_a_tampered_byte() -> None:
    """A JSON edit that pydantic would coerce must still change the digest."""
    envelope = json.loads(SAMPLE_RECEIPT.read_text())
    envelope["transcript"]["turns"] = 3.0
    result = verify_receipt(envelope, pinned_public_key=pinned())
    assert result.valid is False
    assert result.reason == RECEIPT_ID_MISMATCH


def test_canonicalization_is_stable_under_key_reordering() -> None:
    envelope = sample()
    reversed_envelope = dict(reversed(list(envelope.items())))
    reversed_envelope["promise"] = dict(
        reversed(list(envelope["promise"].items()))
    )
    assert canonical_payload(envelope) == canonical_payload(reversed_envelope)
    assert receipt_id_for(envelope) == receipt_id_for(reversed_envelope)
    assert verify_receipt(reversed_envelope, pinned_public_key=pinned()).valid


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda e: e.pop("signature"), id="missing-signature"),
        pytest.param(lambda e: e.pop("promise"), id="missing-promise"),
        pytest.param(lambda e: e.pop("receipt_id"), id="missing-receipt-id"),
        pytest.param(lambda e: e.update(version=2), id="wrong-version"),
        pytest.param(lambda e: e.update(extra="x"), id="extra-field"),
        pytest.param(
            lambda e: e["signature"].update(alg="HS256"), id="wrong-alg"
        ),
        pytest.param(
            lambda e: e["signature"].update(value="not base64!"),
            id="garbage-signature",
        ),
        pytest.param(
            lambda e: e["signature"].update(public_key="AAAA"), id="short-key"
        ),
        pytest.param(
            lambda e: e["transcript"].update(sha256="zz"), id="bad-digest"
        ),
    ],
)
def test_malformed_envelopes_fail_closed(
    mutate: Callable[[dict[str, Any]], object],
) -> None:
    envelope = copy.deepcopy(sample())
    mutate(envelope)
    result = verify_receipt(envelope, pinned_public_key=pinned())
    assert result.valid is False
    assert result.reason in {
        MALFORMED,
        RECEIPT_ID_MISMATCH,
        UNSUPPORTED_ALG,
        INVALID_PUBLIC_KEY,
        INVALID_SIGNATURE,
        SIGNATURE_INVALID,
    }


@pytest.mark.parametrize("junk", [None, {}, [], "not-a-receipt", 42])
def test_non_envelope_input_fails_closed(junk: object) -> None:
    result = verify_receipt(junk, pinned_public_key=pinned())
    assert result.valid is False
    assert result.reason == MALFORMED
    assert result.receipt_id is None


def test_unpinned_accepts_self_signed_but_pin_rejects_it() -> None:
    """Without a pin, verification only proves internal consistency."""
    private_key, public_key = generate_keypair()
    forged = sign_receipt(sample(), private_key)
    assert verify_receipt(forged).valid is True
    assert verify_receipt(forged, pinned_public_key=pinned()).valid is False


def test_sign_receipt_does_not_mutate_the_payload() -> None:
    private_key, _ = generate_keypair()
    payload = {
        key: value
        for key, value in sample().items()
        if key not in {"receipt_id", "signature"}
    }
    before = copy.deepcopy(payload)
    signed = sign_receipt(payload, private_key)
    assert payload == before
    assert "receipt_id" not in payload
    assert signed["receipt_id"] == receipt_id_for(signed)


def test_verify_endpoint_accepts_wrapped_envelope() -> None:
    client = TestClient(app)
    response = client.post(
        "/receipt/verify",
        json={
            "receipt": sample(),
            "public_key": pinned(),
            "key_id": KEY_ID,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "valid": True,
        "reason": "ok",
        "receipt_id": FROZEN_RECEIPT_ID,
        "key_id": KEY_ID,
    }


def test_verify_endpoint_accepts_bare_envelope_and_rejects_tamper() -> None:
    client = TestClient(app)
    response = client.post("/receipt/verify", json=sample())
    assert response.status_code == 200
    assert response.json()["valid"] is True

    tampered = sample()
    tampered["promise"]["amount"] = "145.00"
    rejected = client.post("/receipt/verify", json=tampered)
    assert rejected.status_code == 200
    assert rejected.json()["valid"] is False
    assert rejected.json()["reason"] == RECEIPT_ID_MISMATCH
