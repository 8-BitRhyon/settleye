"""Signed receipt contract: the sample verifies, every edit fails closed.

The pinned fixture values are frozen on purpose. The frontend pins this
public key, so regenerating the keypair must break a test, not the demo.
"""

import base64
import copy
import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
)
from fastapi.testclient import TestClient

from app.main import app
from app.receipt import (
    INVALID_PUBLIC_KEY,
    INVALID_SIGNATURE,
    KEY_ID_MISMATCH,
    MALFORMED,
    MERCHANT_KEY_ID_MISMATCH,
    MERCHANT_KEY_MISMATCH,
    MERCHANT_MISSING,
    MERCHANT_PUBLIC_KEY_INVALID,
    MERCHANT_SIGNATURE_INVALID,
    MERCHANT_UNPINNED,
    PINNED_KEY_MISMATCH,
    RECEIPT_ID_MISMATCH,
    SIGNATURE_INVALID,
    SAMPLE_TRANSCRIPT,
    UNSUPPORTED_ALG,
    canonical_payload,
    countersign_message,
    countersign_receipt,
    encode_public_key,
    generate_keypair,
    main,
    receipt_id_for,
    sign_receipt,
    verify_receipt,
)

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_RECEIPT = FIXTURES / "sample_receipt.json"
SAMPLE_PUBLIC_KEY = FIXTURES / "sample_receipt_public_key.txt"
SAMPLE_MERCHANT_PUBLIC_KEY = (
    FIXTURES / "sample_receipt_merchant_public_key.txt"
)

FROZEN_PUBLIC_KEY = "JExRZnUxqAtd4z8-56EFTbcUIb5p4MOriXHRtXmSk2A"
FROZEN_RECEIPT_ID = (
    "sha256:8551a4d8ad97c7585053d9b1259531be84ef4a8049751d4775b27aa741149d44"
)
FROZEN_ISSUER_SIGNATURE = (
    "ccTYMOeAndLWnyMf2SBOfQQyoqdiC3AU1YygVWJpP5LkDsTgURvn9_vlJn_0RavJDx1m"
    "ObJ2HMFAkgYh-YimBQ"
)
FROZEN_MERCHANT_PUBLIC_KEY = (
    "lwzdcKUKA7AsmR4nRWPD2jfUgO90rlzlP5l-9fkmjAU"
)
KEY_ID = "settleye-demo-2026-12"
MERCHANT_KEY_ID = "merchant-demo-2026-12"
MERCHANT_ACKED_AT = "2026-11-04T12:05:00Z"


def sample() -> dict[str, Any]:
    return json.loads(SAMPLE_RECEIPT.read_text())


def v1_sample() -> dict[str, Any]:
    """The sample as it looked before countersignatures existed."""
    envelope = sample()
    envelope.pop("countersignatures")
    return envelope


def pinned() -> str:
    return SAMPLE_PUBLIC_KEY.read_text().splitlines()[0].strip()


def merchant_pinned() -> str:
    return SAMPLE_MERCHANT_PUBLIC_KEY.read_text().splitlines()[0].strip()


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
    assert envelope["signature"]["value"] == FROZEN_ISSUER_SIGNATURE
    assert envelope["receipt_id"] == FROZEN_RECEIPT_ID
    assert receipt_id_for(envelope) == FROZEN_RECEIPT_ID
    assert merchant_pinned() == FROZEN_MERCHANT_PUBLIC_KEY
    assert envelope["countersignatures"][0]["key_id"] == MERCHANT_KEY_ID


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


def test_countersign_message_is_canonical() -> None:
    assert countersign_message(
        "sha256:abc", "merchant-x", "2026-11-04T12:05:00Z"
    ) == (
        b'{"acknowledged_at":"2026-11-04T12:05:00Z","key_id":"merchant-x",'
        b'"receipt_id":"sha256:abc","role":"merchant"}'
    )


def test_sample_verifies_issuer_and_merchant_with_pins() -> None:
    result = verify_receipt(
        sample(),
        pinned_public_key=pinned(),
        expected_key_id=KEY_ID,
        merchant_public_key=merchant_pinned(),
        expected_merchant_key_id=MERCHANT_KEY_ID,
        require_merchant=True,
    )
    assert result.valid is True
    assert result.reason == "ok"
    assert result.receipt_id == FROZEN_RECEIPT_ID
    assert result.key_id == KEY_ID
    assert result.merchant_valid is True
    assert result.merchant_key_id == MERCHANT_KEY_ID


def test_countersign_preserves_issuer_signature_and_receipt_id() -> None:
    original = v1_sample()
    private_key, public_key = generate_keypair()
    updated = countersign_receipt(
        original, private_key, MERCHANT_KEY_ID, MERCHANT_ACKED_AT
    )
    assert updated["receipt_id"] == original["receipt_id"]
    assert updated["receipt_id"] == FROZEN_RECEIPT_ID
    assert updated["signature"] == original["signature"]
    assert updated["signature"]["value"] == FROZEN_ISSUER_SIGNATURE
    assert receipt_id_for(updated) == FROZEN_RECEIPT_ID

    result = verify_receipt(
        updated,
        pinned_public_key=pinned(),
        expected_key_id=KEY_ID,
        merchant_public_key=encode_public_key(public_key),
        expected_merchant_key_id=MERCHANT_KEY_ID,
        require_merchant=True,
    )
    assert result.valid is True
    assert result.merchant_valid is True


def test_countersign_does_not_mutate_input() -> None:
    original = v1_sample()
    before = copy.deepcopy(original)
    private_key, _ = generate_keypair()
    countersign_receipt(
        original, private_key, MERCHANT_KEY_ID, MERCHANT_ACKED_AT
    )
    assert original == before


def test_countersign_rejects_a_tampered_receipt() -> None:
    envelope = v1_sample()
    envelope["promise"]["amount"] = "145.00"
    private_key, _ = generate_keypair()
    with pytest.raises(ValueError):
        countersign_receipt(
            envelope, private_key, MERCHANT_KEY_ID, MERCHANT_ACKED_AT
        )


def test_tampered_merchant_signature_fails() -> None:
    envelope = sample()
    envelope["countersignatures"][0]["value"] = (
        base64.urlsafe_b64encode(b"\x00" * 64).decode("ascii").rstrip("=")
    )
    result = verify_receipt(
        envelope,
        pinned_public_key=pinned(),
        merchant_public_key=merchant_pinned(),
    )
    assert result.valid is False
    assert result.reason == MERCHANT_SIGNATURE_INVALID
    assert result.merchant_valid is False


def test_edited_acknowledged_at_fails_merchant_signature() -> None:
    envelope = sample()
    envelope["countersignatures"][0]["acknowledged_at"] = (
        "2026-11-04T12:06:00Z"
    )
    result = verify_receipt(
        envelope,
        pinned_public_key=pinned(),
        merchant_public_key=merchant_pinned(),
    )
    assert result.valid is False
    assert result.reason == MERCHANT_SIGNATURE_INVALID


def test_edited_merchant_key_id_fails_merchant_signature() -> None:
    envelope = sample()
    envelope["countersignatures"][0]["key_id"] = "merchant-other"
    result = verify_receipt(
        envelope,
        pinned_public_key=pinned(),
        merchant_public_key=merchant_pinned(),
    )
    assert result.valid is False
    assert result.reason == MERCHANT_SIGNATURE_INVALID


def test_wrong_merchant_pin_fails() -> None:
    _, other_public_key = generate_keypair()
    result = verify_receipt(
        sample(),
        pinned_public_key=pinned(),
        merchant_public_key=encode_public_key(other_public_key),
    )
    assert result.valid is False
    assert result.reason == MERCHANT_KEY_MISMATCH
    assert result.merchant_key_id == MERCHANT_KEY_ID


def test_wrong_merchant_key_id_fails() -> None:
    result = verify_receipt(
        sample(),
        pinned_public_key=pinned(),
        merchant_public_key=merchant_pinned(),
        expected_merchant_key_id="merchant-other-2026-11",
    )
    assert result.valid is False
    assert result.reason == MERCHANT_KEY_ID_MISMATCH


def test_missing_merchant_fails_when_required() -> None:
    result = verify_receipt(
        v1_sample(),
        pinned_public_key=pinned(),
        expected_key_id=KEY_ID,
        require_merchant=True,
    )
    assert result.valid is False
    assert result.reason == MERCHANT_MISSING
    assert result.merchant_valid is False
    assert result.merchant_key_id is None


def test_v1_receipt_without_countersignatures_still_verifies() -> None:
    result = verify_receipt(
        v1_sample(), pinned_public_key=pinned(), expected_key_id=KEY_ID
    )
    assert result.valid is True
    assert result.reason == "ok"
    assert result.receipt_id == FROZEN_RECEIPT_ID
    assert result.merchant_valid is None
    assert result.merchant_key_id is None


def test_valid_merchant_without_pins_is_unverified() -> None:
    result = verify_receipt(sample())
    assert result.valid is True
    assert result.merchant_valid is None
    assert result.merchant_key_id == MERCHANT_KEY_ID


def test_require_merchant_without_a_pin_fails_closed() -> None:
    result = verify_receipt(sample(), require_merchant=True)
    assert result.valid is False
    assert result.reason == MERCHANT_UNPINNED
    assert result.merchant_valid is False
    assert result.merchant_key_id == MERCHANT_KEY_ID


def test_any_invalid_countersignature_fails_the_receipt() -> None:
    envelope = sample()
    bad = copy.deepcopy(envelope["countersignatures"][0])
    bad["value"] = base64.urlsafe_b64encode(b"\x01" * 64).decode().rstrip("=")
    envelope["countersignatures"].append(bad)
    result = verify_receipt(
        envelope,
        pinned_public_key=pinned(),
        merchant_public_key=merchant_pinned(),
    )
    assert result.valid is False
    assert result.reason == MERCHANT_SIGNATURE_INVALID


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        pytest.param(
            lambda c: c.pop("value"), MALFORMED, id="missing-value"
        ),
        pytest.param(
            lambda c: c.update(role="issuer"), MALFORMED, id="wrong-role"
        ),
        pytest.param(
            lambda c: c.update(alg="HS256"),
            MERCHANT_SIGNATURE_INVALID,
            id="wrong-alg",
        ),
        pytest.param(
            lambda c: c.update(public_key="AAAA"),
            MERCHANT_PUBLIC_KEY_INVALID,
            id="short-merchant-key",
        ),
        pytest.param(
            lambda c: c.update(value="not base64!"),
            MERCHANT_SIGNATURE_INVALID,
            id="garbage-merchant-signature",
        ),
        pytest.param(
            lambda c: c.update(extra="x"), MALFORMED, id="extra-field"
        ),
    ],
)
def test_malformed_countersignature_fails_closed(
    mutate: Callable[[dict[str, Any]], object], reason: str
) -> None:
    envelope = sample()
    mutate(envelope["countersignatures"][0])
    result = verify_receipt(
        envelope,
        pinned_public_key=pinned(),
        merchant_public_key=merchant_pinned(),
    )
    assert result.valid is False
    assert result.reason == reason


def test_non_list_countersignatures_fail_closed() -> None:
    envelope = sample()
    envelope["countersignatures"] = "nope"
    result = verify_receipt(envelope, pinned_public_key=pinned())
    assert result.valid is False
    assert result.reason == MALFORMED


def test_countersign_cli_writes_envelope_and_never_prints_seed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Ephemeral test seed under pytest's temp dir. The demo merchant key is
    # never persisted anywhere.
    private_key, public_key = generate_keypair()
    seed = private_key.private_bytes(
        Encoding.Raw, PrivateFormat.Raw, NoEncryption()
    )
    seed_b64 = base64.urlsafe_b64encode(seed).decode("ascii").rstrip("=")
    seed_file = tmp_path / "merchant.seed"
    seed_file.write_text(seed_b64 + "\n")
    source = tmp_path / "receipt.json"
    source.write_text(json.dumps(v1_sample()))
    out = tmp_path / "countersigned.json"

    code = main(
        [
            "countersign",
            "--file",
            str(source),
            "--private-key-file",
            str(seed_file),
            "--key-id",
            "merchant-cli-test",
            "--acknowledged-at",
            MERCHANT_ACKED_AT,
            "--out",
            str(out),
        ]
    )
    assert code == 0
    stdout = capsys.readouterr().out
    assert seed_b64 not in stdout
    assert "private_key" not in stdout.lower()

    written = json.loads(out.read_text())
    assert written["receipt_id"] == FROZEN_RECEIPT_ID
    result = verify_receipt(
        written,
        pinned_public_key=pinned(),
        merchant_public_key=encode_public_key(public_key),
        expected_merchant_key_id="merchant-cli-test",
        require_merchant=True,
    )
    assert result.valid is True


def test_verify_cli_requires_merchant_when_flagged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "v1.json"
    source.write_text(json.dumps(v1_sample()))
    code = main(
        [
            "verify",
            "--file",
            str(source),
            "--public-key-file",
            str(SAMPLE_PUBLIC_KEY),
            "--key-id",
            KEY_ID,
            "--require-merchant",
        ]
    )
    assert code == 1
    assert MERCHANT_MISSING in capsys.readouterr().out


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
        "merchant_valid": None,
        "merchant_key_id": MERCHANT_KEY_ID,
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
