"""Registry-backed verification and the public key endpoint.

No pin means the server's registry decides. A pin still wins for callers that
carry their own trust anchor. Merchant countersignature options pass through
without changing the issuer decision.
"""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.keyring import (
    REGISTRY_ERROR,
    REVOKED_KEY,
    UNKNOWN_KEY,
    default_issuer_key_path,
    default_registry_path,
    init_registry,
)
from app.main import app
from app.receipt import (
    MERCHANT_MISSING,
    PINNED_KEY_MISMATCH,
    countersign_receipt,
    encode_public_key,
    generate_keypair,
    sample_payload,
    sign_receipt,
)
from app.signing import build_signer_from_env

from tests.test_signing import context, promise


def client() -> TestClient:
    return TestClient(app)


def init_key(key_id: str = "api-key-1") -> str:
    record = init_registry(
        default_registry_path(), default_issuer_key_path(), key_id
    )
    return record.public_key


def signed_by_registered_key() -> dict:
    signer = build_signer_from_env()
    assert signer is not None
    envelope = signer.sign(promise(), 45.0, "executed", context())
    assert envelope is not None
    return envelope


def test_keys_endpoint_empty_without_registry() -> None:
    response = client().get("/receipt/keys")
    assert response.status_code == 200
    assert response.json() == []


def test_keys_endpoint_returns_public_records_only() -> None:
    public_key = init_key()
    response = client().get("/receipt/keys")
    assert response.status_code == 200
    records = response.json()
    assert len(records) == 1
    assert records[0]["key_id"] == "api-key-1"
    assert records[0]["public_key"] == public_key
    assert records[0]["status"] == "active"
    assert set(records[0]) == {
        "key_id",
        "public_key",
        "status",
        "created_at",
        "retired_at",
        "revoked_at",
    }
    body = json.dumps(records)
    assert "PRIVATE" not in body
    assert "private" not in body


def test_verify_uses_registry_when_no_pin_is_supplied() -> None:
    init_key()
    envelope = signed_by_registered_key()

    response = client().post("/receipt/verify", json={"receipt": envelope})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["reason"] == "ok"
    assert body["key_id"] == "api-key-1"
    assert body["status"] == "active"


def test_registry_revoked_and_unknown_keys_fail() -> None:
    from app.keyring import KeyRegistry

    init_key()
    envelope = signed_by_registered_key()
    KeyRegistry(default_registry_path()).revoke("api-key-1")

    revoked = client().post("/receipt/verify", json={"receipt": envelope})
    assert revoked.status_code == 200
    assert revoked.json()["valid"] is False
    assert revoked.json()["reason"] == REVOKED_KEY

    foreign_key, _ = generate_keypair()
    foreign = sign_receipt(sample_payload(), foreign_key)
    unknown = client().post("/receipt/verify", json={"receipt": foreign})
    assert unknown.status_code == 200
    assert unknown.json()["valid"] is False
    assert unknown.json()["reason"] == UNKNOWN_KEY


def test_malformed_registry_fails_closed_not_unpinned(
    isolated_keyring: Path,
) -> None:
    init_key()
    envelope = signed_by_registered_key()
    isolated_keyring.write_text("{not json")

    response = client().post("/receipt/verify", json={"receipt": envelope})
    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert response.json()["reason"] == REGISTRY_ERROR
    assert client().get("/receipt/keys").json() == []


def test_explicit_pin_still_wins_over_registry() -> None:
    public_key = init_key()
    envelope = signed_by_registered_key()

    pinned = client().post(
        "/receipt/verify",
        json={
            "receipt": envelope,
            "public_key": public_key,
            "key_id": "api-key-1",
        },
    )
    assert pinned.status_code == 200
    assert pinned.json()["valid"] is True

    _, other_public = generate_keypair()
    wrong = client().post(
        "/receipt/verify",
        json={
            "receipt": envelope,
            "public_key": encode_public_key(other_public),
        },
    )
    assert wrong.status_code == 200
    assert wrong.json()["valid"] is False
    assert wrong.json()["reason"] == PINNED_KEY_MISMATCH


def two_party_envelope() -> tuple[dict, str, str]:
    issuer_private, issuer_public = generate_keypair()
    merchant_private, merchant_public = generate_keypair()
    envelope = sign_receipt(sample_payload(), issuer_private)
    envelope = countersign_receipt(
        envelope,
        merchant_private,
        "merchant-1",
        "2026-11-04T12:00:00Z",
    )
    return (
        envelope,
        encode_public_key(issuer_public),
        encode_public_key(merchant_public),
    )


def test_two_party_envelope_verifies_with_both_pins() -> None:
    envelope, issuer_key, merchant_key = two_party_envelope()
    response = client().post(
        "/receipt/verify",
        json={
            "receipt": envelope,
            "public_key": issuer_key,
            "key_id": envelope["issuer"]["key_id"],
            "merchant_public_key": merchant_key,
            "merchant_key_id": "merchant-1",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["merchant_valid"] is True
    assert body["merchant_key_id"] == "merchant-1"


def test_require_merchant_fails_when_countersignature_is_missing() -> None:
    issuer_private, issuer_public = generate_keypair()
    envelope = sign_receipt(sample_payload(), issuer_private)

    response = client().post(
        "/receipt/verify",
        json={
            "receipt": envelope,
            "public_key": encode_public_key(issuer_public),
            "key_id": envelope["issuer"]["key_id"],
            "require_merchant": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["reason"] == MERCHANT_MISSING
    assert body["merchant_valid"] is False


def test_registry_path_passes_merchant_pins_through() -> None:
    init_key()
    envelope = signed_by_registered_key()
    merchant_private, merchant_public = generate_keypair()
    envelope = countersign_receipt(
        envelope,
        merchant_private,
        "merchant-2",
        "2026-11-04T12:00:00Z",
    )

    response = client().post(
        "/receipt/verify",
        json={
            "receipt": envelope,
            "merchant_public_key": encode_public_key(merchant_public),
            "merchant_key_id": "merchant-2",
            "require_merchant": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["merchant_valid"] is True
    assert body["merchant_key_id"] == "merchant-2"
