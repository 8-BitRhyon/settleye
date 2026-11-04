"""Issuer key lifecycle: active signs, retired still verifies, revoked fails.

A receipt outlives the key that signed it. Rotation must not break history,
and revocation must not leave a usable key looking active.
"""

import json
import stat
from pathlib import Path

import pytest

from app import keyring as keyring_module
from app.keyring import (
    REVOKED_KEY,
    UNKNOWN_KEY,
    KeyRecord,
    KeyRegistry,
    KeyringError,
    init_registry,
    verify_with_registry,
)
from app.receipt import generate_keypair, sign_receipt
from app.signing import build_signer_from_env

from tests.test_signing import context, promise


def key_path(registry: Path) -> Path:
    return registry.with_name("issuer.key")


def initialized(
    registry: Path, key_id: str = "key-1"
) -> KeyRegistry:
    init_registry(registry, key_path(registry), key_id=key_id)
    return KeyRegistry(registry)


def signed_by_active() -> dict:
    signer = build_signer_from_env()
    assert signer is not None
    envelope = signer.sign(promise(), 45.0, "executed", context())
    assert envelope is not None
    return envelope


def test_init_writes_active_key_and_mode_0600(isolated_keyring: Path) -> None:
    registry = initialized(isolated_keyring)
    active = registry.active_key()
    assert active is not None
    assert active.key_id == "key-1"
    assert active.status == "active"
    assert len(active.public_key) >= 43

    mode = stat.S_IMODE(key_path(isolated_keyring).stat().st_mode)
    assert mode == 0o600

    # The file contains a PEM private key; the registry never does.
    assert "PRIVATE KEY" in key_path(isolated_keyring).read_text()
    raw_registry = isolated_keyring.read_text()
    assert "PRIVATE" not in raw_registry
    assert raw_registry.count("key-1") >= 1


def test_rotate_retires_old_key_and_old_receipts_still_verify(
    isolated_keyring: Path,
) -> None:
    registry = initialized(isolated_keyring)
    old_envelope = signed_by_active()

    new_record = registry.rotate("key-2", key_path(isolated_keyring))
    assert new_record.status == "active"
    assert registry.active_key().key_id == "key-2"  # type: ignore[union-attr]

    old_record = registry.get("key-1")
    assert old_record is not None
    assert old_record.status == "retired"
    assert old_record.retired_at is not None

    result = verify_with_registry(old_envelope, KeyRegistry(isolated_keyring))
    assert result.valid is True
    assert result.reason == "ok"
    assert result.status == "retired"
    assert result.note is not None and "retired" in result.note

    new_envelope = signed_by_active()
    active_result = verify_with_registry(
        new_envelope, KeyRegistry(isolated_keyring)
    )
    assert active_result.valid is True
    assert active_result.status == "active"
    assert active_result.note is None


def test_revoked_key_fails_closed(isolated_keyring: Path) -> None:
    registry = initialized(isolated_keyring)
    envelope = signed_by_active()
    registry.revoke("key-1")

    result = verify_with_registry(envelope, KeyRegistry(isolated_keyring))
    assert result.valid is False
    assert result.reason == REVOKED_KEY

    with pytest.raises(KeyringError):
        registry.revoke("missing-key")


def test_unknown_key_fails_even_when_self_signed(isolated_keyring: Path) -> None:
    initialized(isolated_keyring)
    private_key, _ = generate_keypair()
    foreign = sign_receipt(
        {
            "version": 1,
            "issued_at": "2026-11-04T12:00:00Z",
            "issuer": {"name": "Settleye", "key_id": "not-registered"},
            "agent": {"model_id": "m"},
            "transcript": {"sha256": "a" * 64, "turns": 1},
            "promise": {
                "action": "refund",
                "order_id": "992",
                "amount": "45.00",
                "target_system": "stripe",
                "terminal_status": "binding",
                "evidence_span": "x",
            },
            "ledger": {
                "system": "stripe",
                "order_id": "992",
                "shortfall_usd": "45.00",
                "summary": "x",
                "checked_at": "2026-11-04T12:00:00Z",
            },
            "remediation": {
                "idempotency_key": "refund:992:stripe:45.00",
                "amount_usd": "45.00",
                "status": "executed",
            },
        },
        private_key,
    )
    result = verify_with_registry(foreign, KeyRegistry(isolated_keyring))
    assert result.valid is False
    assert result.reason == UNKNOWN_KEY


def test_first_record_for_a_key_id_wins(isolated_keyring: Path) -> None:
    registry = initialized(isolated_keyring)
    original = registry.get("key-1")
    assert original is not None

    added = registry.add(
        KeyRecord(
            key_id="key-1",
            public_key="attacker-key",
            status="revoked",
            created_at="2026-11-04T12:00:00Z",
        )
    )
    assert added.public_key == original.public_key
    assert registry.get("key-1").status == "active"  # type: ignore[union-attr]
    assert len(KeyRegistry(isolated_keyring).records) == 1


def test_init_refuses_to_replace_without_force(isolated_keyring: Path) -> None:
    initialized(isolated_keyring)
    with pytest.raises(KeyringError, match="force"):
        init_registry(
            isolated_keyring, key_path(isolated_keyring), key_id="key-2"
        )
    replaced = init_registry(
        isolated_keyring,
        key_path(isolated_keyring),
        key_id="key-3",
        force=True,
    )
    assert replaced.key_id == "key-3"
    assert [record.key_id for record in KeyRegistry(isolated_keyring).records] == [
        "key-3"
    ]


def test_cli_init_list_rotate_revoke(
    isolated_keyring: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    private = key_path(isolated_keyring)

    assert (
        keyring_module.main(
            [
                "init",
                "--registry",
                str(isolated_keyring),
                "--private-key",
                str(private),
                "--key-id",
                "cli-1",
            ]
        )
        == 0
    )
    init_out = json.loads(capsys.readouterr().out)
    assert init_out["key_id"] == "cli-1"
    assert "PRIVATE" not in json.dumps(init_out)

    assert (
        keyring_module.main(
            ["list", "--registry", str(isolated_keyring)]
        )
        == 0
    )
    listed = json.loads(capsys.readouterr().out)
    assert [record["key_id"] for record in listed] == ["cli-1"]
    assert set(listed[0]) == {
        "key_id",
        "public_key",
        "status",
        "created_at",
        "retired_at",
        "revoked_at",
    }

    assert (
        keyring_module.main(
            [
                "rotate",
                "--registry",
                str(isolated_keyring),
                "--private-key",
                str(private),
                "--key-id",
                "cli-2",
            ]
        )
        == 0
    )
    rotate_out = json.loads(capsys.readouterr().out)
    assert rotate_out["key_id"] == "cli-2"

    states = {
        record["key_id"]: record["status"]
        for record in KeyRegistry(isolated_keyring).public_records()
    }
    assert states == {"cli-1": "retired", "cli-2": "active"}

    assert (
        keyring_module.main(
            [
                "revoke",
                "--registry",
                str(isolated_keyring),
                "--key-id",
                "cli-2",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["status"] == "revoked"


def test_cli_unknown_revoke_exits_nonzero(
    isolated_keyring: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    initialized(isolated_keyring)
    capsys.readouterr()
    assert (
        keyring_module.main(
            [
                "revoke",
                "--registry",
                str(isolated_keyring),
                "--key-id",
                "missing",
            ]
        )
        == 1
    )
    assert "Unknown key id" in capsys.readouterr().err
