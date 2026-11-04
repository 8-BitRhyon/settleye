"""Issuer key registry: which public keys Settleye has used, and their state.

A receipt is only worth as much as the verifier's answer to "was this key
Settleye's, and was it valid when it signed?" The registry is that answer. Keys
move through three states:

- active: the current signing key.
- retired: rotated out. Old receipts must keep verifying, so the public key
  stays on file and verification reports the retirement as a note.
- revoked: compromised or withdrawn. Verification fails closed.

The private key never enters the registry. It lives in one file with mode
0600, written by `init` or `rotate`, and only the public half is published.
JSON is intentionally boring: a demo verifier can read it without a library.
"""

import argparse
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    load_pem_private_key,
)
from pydantic import BaseModel, Field, ValidationError

from app.receipt import (
    MALFORMED,
    ReceiptEnvelope,
    VerifyResult,
    encode_public_key,
    generate_keypair,
    verify_receipt,
)

KEYRING_PATH_ENV = "SETTLEYE_KEYRING_PATH"
ISSUER_KEY_PATH_ENV = "SETTLEYE_ISSUER_KEY_PATH"

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = _BACKEND_ROOT / ".tmp" / "keyring.json"
DEFAULT_ISSUER_KEY_PATH = _BACKEND_ROOT / ".tmp" / "issuer.key"

REGISTRY_VERSION = 1

# Registry-specific failure reasons, additive to the receipt contract.
UNKNOWN_KEY = "unknown_key"
REVOKED_KEY = "revoked_key"
REGISTRY_ERROR = "registry_error"


class KeyringError(Exception):
    """The registry or key file is unreadable, malformed, or inconsistent."""


def utc_now_iso() -> str:
    """UTC ISO 8601 with a Z suffix, second precision."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class KeyRecord(BaseModel):
    """One public key and its lifecycle state. Never holds private material."""

    key_id: str = Field(min_length=1)
    public_key: str
    status: Literal["active", "retired", "revoked"] = "active"
    created_at: str = ""
    retired_at: str | None = None
    revoked_at: str | None = None


class RegistryVerifyResult(VerifyResult):
    """Verification plus the registry's own verdict on the key's state."""

    status: str | None = None
    note: str | None = None


def generate_key_id() -> str:
    """A readable, collision-resistant default id: month plus random suffix."""
    month = datetime.now(timezone.utc).strftime("%Y%m")
    return f"settleye-{month}-{secrets.token_hex(3)}"


def write_private_key(path: str | Path, private_key: Ed25519PrivateKey) -> Path:
    """Write a PEM PKCS8 key with mode 0600, fsynced before returning."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = private_key.private_bytes(
        Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()
    )
    descriptor = os.open(
        target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600
    )
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(target, 0o600)
    return target


def load_private_key(path: str | Path) -> Ed25519PrivateKey:
    """Load the issuer's PEM private key. Never returns a non-Ed25519 key."""
    try:
        data = Path(path).read_bytes()
        key = load_pem_private_key(data, password=None)
    except (OSError, ValueError, TypeError, UnsupportedAlgorithm) as exc:
        raise KeyringError(f"Cannot read issuer key {path}: {exc}") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise KeyringError(f"Issuer key {path} is not an Ed25519 private key.")
    return key


class KeyRegistry:
    """Ordered public-key registry backed by one JSON file.

    List order is append order. `get` and updates resolve the first record for
    a key id, so a later line cannot silently override an existing key.
    """

    def __init__(
        self,
        path: str | Path,
        records: list[KeyRecord] | None = None,
    ) -> None:
        self._path = Path(path)
        if records is None:
            self._records: list[KeyRecord] = []
            self._load()
        else:
            self._records = list(records)

    @classmethod
    def load(cls, path: str | Path) -> "KeyRegistry":
        """Load a registry; a missing file is an empty registry, not an error."""
        return cls(path)

    @classmethod
    def init(
        cls,
        registry_path: str | Path,
        private_key_path: str | Path,
        key_id: str | None = None,
        force: bool = False,
    ) -> "KeyRegistry":
        """Create a fresh registry and keypair, replacing only with force."""
        init_registry(registry_path, private_key_path, key_id=key_id, force=force)
        return cls(registry_path)

    @property
    def path(self) -> Path:
        return self._path

    @property
    def records(self) -> list[KeyRecord]:
        return list(self._records)

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise KeyringError(
                f"Key registry {self._path} is unreadable: {exc}."
            ) from exc
        raw_records = payload.get("keys") if isinstance(payload, dict) else payload
        if not isinstance(raw_records, list):
            raise KeyringError(
                f"Key registry {self._path} has no keys list."
            )
        try:
            self._records = [
                KeyRecord.model_validate(record) for record in raw_records
            ]
        except (ValidationError, TypeError) as exc:
            raise KeyringError(
                f"Key registry {self._path} has a malformed record: {exc}."
            ) from exc

    def save(self) -> Path:
        """Atomically replace the registry file with the current records."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        body = {
            "version": REGISTRY_VERSION,
            "keys": [record.model_dump(mode="json") for record in self._records],
        }
        temporary = self._path.with_name(self._path.name + ".tmp")
        try:
            temporary.write_text(
                json.dumps(body, indent=2) + "\n", encoding="utf-8"
            )
            os.replace(temporary, self._path)
        except OSError as exc:
            raise KeyringError(
                f"Could not write key registry {self._path}: {exc}."
            ) from exc
        return self._path

    def get(self, key_id: str) -> KeyRecord | None:
        """First record for a key id wins."""
        for record in self._records:
            if record.key_id == key_id:
                return record
        return None

    def active_key(self) -> KeyRecord | None:
        """The newest active key, or None when no key may sign."""
        for record in reversed(self._records):
            if record.status == "active":
                return record
        return None

    def add(self, record: KeyRecord) -> KeyRecord:
        """Append a public record. An existing key id is returned unchanged."""
        existing = self.get(record.key_id)
        if existing is not None:
            return existing
        self._records.append(record)
        self.save()
        return record

    def _update(self, key_id: str, **changes: object) -> KeyRecord:
        for index, record in enumerate(self._records):
            if record.key_id == key_id:
                updated = record.model_copy(update=changes)
                self._records[index] = updated
                self.save()
                return updated
        raise KeyringError(f"Unknown key id: {key_id}.")

    def rotate(
        self, new_key_id: str, private_key_path: str | Path
    ) -> KeyRecord:
        """Generate a replacement key, retire the old active one, save both."""
        if not new_key_id:
            raise KeyringError("A non-empty key id is required for rotation.")
        if self.get(new_key_id) is not None:
            raise KeyringError(f"Key id already registered: {new_key_id}.")
        private_key, public_key = generate_keypair()
        now = utc_now_iso()
        for index, record in enumerate(self._records):
            if record.status == "active":
                self._records[index] = record.model_copy(
                    update={"status": "retired", "retired_at": now}
                )
        write_private_key(private_key_path, private_key)
        record = KeyRecord(
            key_id=new_key_id,
            public_key=encode_public_key(public_key),
            status="active",
            created_at=now,
        )
        self._records.append(record)
        self.save()
        return record

    def revoke(self, key_id: str) -> KeyRecord:
        """Mark a key revoked. Later verifications fail closed."""
        existing = self.get(key_id)
        if existing is None:
            raise KeyringError(f"Unknown key id: {key_id}.")
        if existing.status == "revoked":
            return existing
        return self._update(key_id, status="revoked", revoked_at=utc_now_iso())

    def public_records(self) -> list[dict[str, object]]:
        """JSON-ready public half only: no private path exists to leak."""
        return [record.model_dump(mode="json") for record in self._records]


def init_registry(
    registry_path: str | Path,
    private_key_path: str | Path,
    key_id: str | None = None,
    force: bool = False,
) -> KeyRecord:
    """Write one active keypair and a one-record registry.

    Refuses to overwrite an existing populated registry without force, so a
    stray command cannot orphan the key that signed already-issued receipts.
    """
    path = Path(registry_path)
    if path.exists() and not force:
        existing = KeyRegistry.load(path)
        if existing.records:
            raise KeyringError(
                f"Key registry {path} already has keys. Use --force to replace."
            )
    chosen_id = key_id or generate_key_id()
    private_key, public_key = generate_keypair()
    write_private_key(private_key_path, private_key)
    record = KeyRecord(
        key_id=chosen_id,
        public_key=encode_public_key(public_key),
        status="active",
        created_at=utc_now_iso(),
    )
    KeyRegistry(path, records=[record]).save()
    return record


def verify_with_registry(
    envelope: object,
    registry: KeyRegistry,
    merchant_public_key: str | None = None,
    expected_merchant_key_id: str | None = None,
    require_merchant: bool = False,
) -> RegistryVerifyResult:
    """Verify an envelope against the registry's public key for its key id.

    Unknown and revoked keys fail before the signature check: a valid
    self-signature by an unknown key must never count as Settleye's. Retired
    keys still verify because receipts outlive rotations, but the result says
    so in `note`. Merchant countersignature options pass through unchanged.
    """
    try:
        parsed = ReceiptEnvelope.model_validate(envelope)
    except (ValidationError, TypeError, ValueError):
        return RegistryVerifyResult(valid=False, reason=MALFORMED)

    key_id = parsed.issuer.key_id
    record = registry.get(key_id)
    if record is None:
        return RegistryVerifyResult(
            valid=False, reason=UNKNOWN_KEY, key_id=key_id
        )
    if record.status == "revoked":
        return RegistryVerifyResult(
            valid=False, reason=REVOKED_KEY, key_id=key_id
        )

    result = verify_receipt(
        envelope,
        pinned_public_key=record.public_key,
        expected_key_id=record.key_id,
        merchant_public_key=merchant_public_key,
        expected_merchant_key_id=expected_merchant_key_id,
        require_merchant=require_merchant,
    )
    note = None
    if result.valid and record.status == "retired":
        note = "retired key: signature valid, key no longer active"
    return RegistryVerifyResult(
        **result.model_dump(), status=record.status, note=note
    )


def default_registry_path() -> Path:
    return Path(os.environ.get(KEYRING_PATH_ENV) or DEFAULT_REGISTRY_PATH)


def default_issuer_key_path() -> Path:
    return Path(os.environ.get(ISSUER_KEY_PATH_ENV) or DEFAULT_ISSUER_KEY_PATH)


def _emit(payload: object) -> None:
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def _cmd_init(args: argparse.Namespace) -> int:
    record = init_registry(
        args.registry,
        args.private_key,
        key_id=args.key_id,
        force=args.force,
    )
    _emit(
        {
            "key_id": record.key_id,
            "public_key": record.public_key,
            "registry": str(args.registry),
        }
    )
    return 0


def _cmd_rotate(args: argparse.Namespace) -> int:
    registry = KeyRegistry.load(args.registry)
    if not registry.records:
        raise KeyringError(
            f"No registry at {args.registry}. Run init before rotate."
        )
    record = registry.rotate(
        args.key_id or generate_key_id(), args.private_key
    )
    _emit(
        {
            "key_id": record.key_id,
            "public_key": record.public_key,
            "registry": str(args.registry),
        }
    )
    return 0


def _cmd_revoke(args: argparse.Namespace) -> int:
    registry = KeyRegistry.load(args.registry)
    record = registry.revoke(args.key_id)
    _emit(record.model_dump(mode="json"))
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    registry = KeyRegistry.load(args.registry)
    _emit(registry.public_records())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.keyring",
        description="Manage the Settleye issuer key registry.",
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--registry", default=str(DEFAULT_REGISTRY_PATH), help="registry JSON"
    )
    common.add_argument(
        "--private-key",
        default=str(DEFAULT_ISSUER_KEY_PATH),
        help="issuer private key path (0600)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser(
        "init", parents=[common], help="create a keypair and registry"
    )
    init.add_argument("--key-id", default=None)
    init.add_argument(
        "--force", action="store_true", help="replace a populated registry"
    )
    init.set_defaults(func=_cmd_init)

    rotate = sub.add_parser(
        "rotate", parents=[common], help="generate a new active key"
    )
    rotate.add_argument("--key-id", default=None)
    rotate.set_defaults(func=_cmd_rotate)

    revoke = sub.add_parser(
        "revoke", parents=[common], help="mark a key revoked"
    )
    revoke.add_argument("--key-id", required=True)
    revoke.set_defaults(func=_cmd_revoke)

    list_keys = sub.add_parser(
        "list", parents=[common], help="print public key records"
    )
    list_keys.set_defaults(func=_cmd_list)

    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyringError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
