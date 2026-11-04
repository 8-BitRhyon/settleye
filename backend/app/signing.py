"""Turn a reconciled drift plus audit provenance into a signed v1 receipt.

This module is the bridge between the audit report and the money-moving
service. It owns no cryptography of its own: `app.receipt` defines the
envelope and signs it. The signer only refuses to sign claims it cannot bind:
a digest that is not 64 lowercase hex, or a transcript with no turns.

Signing happens after the refund write. A signature failure is therefore an
attribution failure, not a money failure: the service keeps the durable
receipt and leaves the signed envelope empty rather than failing the call.
"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from app.keyring import (
    KeyRegistry,
    default_issuer_key_path,
    default_registry_path,
    load_private_key,
)
from app.models import PromiseEntity
from app.receipt import encode_public_key, sign_receipt

ISSUER_NAME = "Settleye"

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def utc_now_iso() -> str:
    """UTC ISO 8601 with a Z suffix, second precision."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class ReceiptContext:
    """Audit provenance a receipt binds. All values come from the report."""

    transcript_sha256: str
    transcript_turns: int
    audited_at: str
    ledger_summary: str
    model_id: str
    ledger_checked_at: str = ""


def _order_id(promise: PromiseEntity) -> str:
    """Receipts carry the bare ledger key, matching reconciliation."""
    return (promise.order_id or "").strip().lstrip("#") or "unknown"


class ReceiptSigner:
    """Signs v1 receipt payloads with one Ed25519 key and issuer identity."""

    def __init__(
        self,
        private_key: Ed25519PrivateKey,
        key_id: str,
        issuer: str = ISSUER_NAME,
    ) -> None:
        self._private_key = private_key
        self.key_id = key_id
        self.issuer = issuer

    def sign(
        self,
        promise: PromiseEntity,
        amount_usd: float,
        status: str,
        context: ReceiptContext | None,
    ) -> dict[str, Any] | None:
        """Sign one receipt body, or return None when the claim is unbindable.

        The fallback amount is the live shortfall, used only when the
        transcript never stated a number. It matches the key the remediation
        service already used, so a replay cannot produce a second key.
        """
        if context is None:
            return None
        digest = context.transcript_sha256 or ""
        if not _HEX64.fullmatch(digest):
            return None
        if context.transcript_turns < 1:
            return None

        # Function-level import: app.remediate.service imports this module,
        # so a top-level import would be circular. The key function is the
        # single owner of the idempotency formula and must not be copied.
        from app.remediate.service import promise_key

        issued_at = utc_now_iso()
        order_id = _order_id(promise)
        promise_amount = (
            promise.amount if promise.amount is not None else amount_usd
        )
        payload: dict[str, Any] = {
            "version": 1,
            "issued_at": issued_at,
            "issuer": {"name": self.issuer, "key_id": self.key_id},
            "agent": {"model_id": context.model_id},
            "transcript": {
                "sha256": digest,
                "turns": context.transcript_turns,
            },
            "promise": {
                "action": promise.action,
                "order_id": order_id,
                "amount": f"{promise_amount:.2f}",
                "target_system": promise.target_system,
                "terminal_status": promise.terminal_status,
                "evidence_span": promise.evidence_span,
            },
            "ledger": {
                "system": promise.target_system,
                "order_id": order_id,
                "shortfall_usd": f"{amount_usd:.2f}",
                "summary": context.ledger_summary,
                # The reconcile ran before the refund write; record when the
                # observed state was read, not when the signature was made.
                "checked_at": context.ledger_checked_at or issued_at,
            },
            "remediation": {
                "idempotency_key": promise_key(promise, amount_usd),
                "amount_usd": f"{amount_usd:.2f}",
                "status": status,
            },
        }
        return sign_receipt(payload, self._private_key)


def build_signer_from_env() -> ReceiptSigner | None:
    """Active key from the registry plus its private key, or None.

    Missing files, malformed JSON, an empty registry, a key mismatch, and an
    unreadable private key all mean "run unsigned". They must never stop the
    audit or remediation path from starting.
    """
    try:
        registry = KeyRegistry.load(default_registry_path())
        record = registry.active_key()
        if record is None:
            return None
        private_key = load_private_key(default_issuer_key_path())
        if encode_public_key(private_key.public_key()) != record.public_key:
            return None
        return ReceiptSigner(private_key=private_key, key_id=record.key_id)
    except Exception:
        return None
