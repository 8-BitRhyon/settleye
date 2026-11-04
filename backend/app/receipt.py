"""Signed, portable execution receipts.

A receipt is a JSON envelope that binds one transcript digest, one promise,
the ledger state that contradicted it, the remediation idempotency key, and
the issuer identity. The envelope is canonicalized (sorted keys, no
whitespace, UTF-8) and signed with Ed25519. The receipt id is the SHA-256 of
the same canonical bytes, so any edit to any field changes both the id and
the signature.

What this proves: the holder of the private key issued exactly these bytes.
What it does not prove: that the transcript is authentic, that the ledger
read was correct, or that money actually left Stripe. Those remain claims by
the issuer, and the signature only makes them attributable and tamper
evident.

Money is carried as strings on purpose: no float formatting can disagree
between the Python signer and a JavaScript verifier.
"""

import argparse
import base64
import binascii
import hashlib
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
)
from pydantic import BaseModel, ConfigDict, Field, ValidationError

RECEIPT_VERSION = 1
SIGNATURE_ALG = "Ed25519"

# Reason codes are part of the contract with the verifying frontend.
OK = "ok"
MALFORMED = "malformed_envelope"
RECEIPT_ID_MISMATCH = "receipt_id_mismatch"
UNSUPPORTED_ALG = "unsupported_alg"
INVALID_PUBLIC_KEY = "invalid_public_key"
INVALID_PINNED_KEY = "invalid_pinned_key"
INVALID_SIGNATURE = "invalid_signature"
SIGNATURE_INVALID = "signature_invalid"
PINNED_KEY_MISMATCH = "pinned_key_mismatch"
KEY_ID_MISMATCH = "key_id_mismatch"

# Exact text bound by transcript.sha256. The trailing newline is part of the
# binding: a verifier must hash these exact bytes, nothing normalized.
SAMPLE_TRANSCRIPT = (
    "Customer: The jacket I ordered (order #992) arrived with a torn seam."
    " I want a refund.\n"
    "Agent: I am sorry about the torn seam. I have processed a full $45"
    " refund for order #992.\n"
    "Customer: Great, thank you for sorting that out so fast.\n"
)


class _Strict(BaseModel):
    """Unknown keys are rejected: an unverified field must not ride along."""

    model_config = ConfigDict(extra="forbid")


class Issuer(_Strict):
    name: str
    key_id: str


class Agent(_Strict):
    model_id: str


class TranscriptRef(_Strict):
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    turns: int = Field(ge=1)


class PromiseClaim(_Strict):
    action: str
    order_id: str
    amount: str
    target_system: str
    terminal_status: str
    evidence_span: str


class LedgerState(_Strict):
    system: str
    order_id: str
    shortfall_usd: str
    summary: str
    checked_at: str


class RemediationRef(_Strict):
    idempotency_key: str
    amount_usd: str
    status: str


class ReceiptSignature(_Strict):
    alg: str
    public_key: str
    value: str


class ReceiptPayload(_Strict):
    """The signed half of the envelope: no receipt_id, no signature."""

    version: Literal[1] = RECEIPT_VERSION
    issued_at: str
    issuer: Issuer
    agent: Agent
    transcript: TranscriptRef
    promise: PromiseClaim
    ledger: LedgerState
    remediation: RemediationRef


class ReceiptEnvelope(ReceiptPayload):
    """A complete receipt: payload plus derived id and signature."""

    receipt_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    signature: ReceiptSignature


class VerifyResult(BaseModel):
    """Verification outcome. `receipt_id` is the recomputed id of the bytes."""

    valid: bool
    reason: str
    receipt_id: str | None = None
    key_id: str | None = None


def _b64u_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64u_decode(value: str) -> bytes:
    """Strict base64url decode: bad alphabet is an error, not noise."""
    if not isinstance(value, str) or not value:
        raise ValueError("empty base64url value")
    padding = "=" * (-len(value) % 4)
    return base64.b64decode(value + padding, altchars=b"-_", validate=True)


def canonical_payload(payload: Mapping[str, Any] | BaseModel) -> bytes:
    """Canonical bytes: sorted keys, no whitespace, UTF-8, no derived fields."""
    data: dict[str, Any] = (
        payload.model_dump(mode="json")
        if isinstance(payload, BaseModel)
        else dict(payload)
    )
    data.pop("receipt_id", None)
    data.pop("signature", None)
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _receipt_id_for_bytes(canonical: bytes) -> str:
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def receipt_id_for(payload: Mapping[str, Any] | BaseModel) -> str:
    """Receipt id: SHA-256 over the canonical payload bytes."""
    return _receipt_id_for_bytes(canonical_payload(payload))


def encode_public_key(public_key: Ed25519PublicKey) -> str:
    """Raw 32-byte Ed25519 public key as unpadded base64url."""
    return _b64u_encode(public_key.public_bytes(Encoding.Raw, PublicFormat.Raw))


def generate_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """Fresh Ed25519 keypair. The caller owns the private key."""
    private_key = Ed25519PrivateKey.generate()
    return private_key, private_key.public_key()


def sign_receipt(
    payload: Mapping[str, Any] | BaseModel, private_key: Ed25519PrivateKey
) -> dict[str, Any]:
    """Validate a payload, then attach receipt_id and signature.

    Returns a JSON-ready dict. The input is never mutated.
    """
    raw: dict[str, Any] = (
        payload.model_dump(mode="json")
        if isinstance(payload, BaseModel)
        else dict(payload)
    )
    # Derived fields are recomputed, never accepted from the caller.
    raw.pop("receipt_id", None)
    raw.pop("signature", None)
    body = ReceiptPayload.model_validate(raw)
    canonical = canonical_payload(body)
    envelope = ReceiptEnvelope(
        **body.model_dump(),
        receipt_id=_receipt_id_for_bytes(canonical),
        signature=ReceiptSignature(
            alg=SIGNATURE_ALG,
            public_key=encode_public_key(private_key.public_key()),
            value=_b64u_encode(private_key.sign(canonical)),
        ),
    )
    return envelope.model_dump(mode="json")


def verify_receipt(
    envelope: Mapping[str, Any] | BaseModel,
    pinned_public_key: str | None = None,
    expected_key_id: str | None = None,
) -> VerifyResult:
    """Verify one envelope. Fails closed on any malformed input.

    Checks run in order: structure, receipt id, alg, signature, then the
    optional pin. A caller that pins a key gets issuer authenticity; a caller
    that does not only gets internal consistency.
    """
    try:
        parsed = ReceiptEnvelope.model_validate(envelope)
    except (ValidationError, TypeError, ValueError):
        return VerifyResult(valid=False, reason=MALFORMED)

    # Hash the bytes as supplied, not a re-serialized model: a pydantic
    # coercion (3 -> 3.0, say) must not turn an edited byte into a pass.
    try:
        canonical = canonical_payload(
            parsed if isinstance(envelope, BaseModel) else envelope
        )
    except (TypeError, ValueError):
        return VerifyResult(valid=False, reason=MALFORMED)

    recomputed = _receipt_id_for_bytes(canonical)
    key_id = parsed.issuer.key_id

    if parsed.receipt_id != recomputed:
        return VerifyResult(
            valid=False,
            reason=RECEIPT_ID_MISMATCH,
            receipt_id=recomputed,
            key_id=key_id,
        )

    if parsed.signature.alg != SIGNATURE_ALG:
        return VerifyResult(
            valid=False,
            reason=UNSUPPORTED_ALG,
            receipt_id=recomputed,
            key_id=key_id,
        )

    try:
        raw_public_key = _b64u_decode(parsed.signature.public_key)
        public_key = Ed25519PublicKey.from_public_bytes(raw_public_key)
    except (ValueError, TypeError, binascii.Error):
        return VerifyResult(
            valid=False,
            reason=INVALID_PUBLIC_KEY,
            receipt_id=recomputed,
            key_id=key_id,
        )

    try:
        signature = _b64u_decode(parsed.signature.value)
    except (ValueError, TypeError, binascii.Error):
        return VerifyResult(
            valid=False,
            reason=INVALID_SIGNATURE,
            receipt_id=recomputed,
            key_id=key_id,
        )

    try:
        public_key.verify(signature, canonical)
    except (InvalidSignature, ValueError):
        return VerifyResult(
            valid=False,
            reason=SIGNATURE_INVALID,
            receipt_id=recomputed,
            key_id=key_id,
        )

    if pinned_public_key is not None:
        try:
            pinned = _b64u_decode(pinned_public_key)
        except (ValueError, TypeError, binascii.Error):
            return VerifyResult(
                valid=False,
                reason=INVALID_PINNED_KEY,
                receipt_id=recomputed,
                key_id=key_id,
            )
        if pinned != raw_public_key:
            return VerifyResult(
                valid=False,
                reason=PINNED_KEY_MISMATCH,
                receipt_id=recomputed,
                key_id=key_id,
            )

    if expected_key_id is not None and expected_key_id != key_id:
        return VerifyResult(
            valid=False,
            reason=KEY_ID_MISMATCH,
            receipt_id=recomputed,
            key_id=key_id,
        )

    return VerifyResult(
        valid=True, reason=OK, receipt_id=recomputed, key_id=key_id
    )


def sample_payload() -> dict[str, Any]:
    """The fixed demo receipt body, before signing."""
    return {
        "version": RECEIPT_VERSION,
        "issued_at": "2026-11-04T12:00:00Z",
        "issuer": {"name": "Settleye", "key_id": "settleye-demo-2026-11"},
        "agent": {"model_id": "meta-models/muse-spark-open-1026"},
        "transcript": {
            "sha256": hashlib.sha256(
                SAMPLE_TRANSCRIPT.encode("utf-8")
            ).hexdigest(),
            "turns": 3,
        },
        "promise": {
            "action": "refund",
            "order_id": "992",
            "amount": "45.00",
            "target_system": "stripe",
            "terminal_status": "binding",
            "evidence_span": (
                "I have processed a full $45 refund for order #992. It should "
                "appear on your statement within 5 to 10 business days."
            ),
        },
        "ledger": {
            "system": "stripe",
            "order_id": "992",
            "shortfall_usd": "45.00",
            "summary": "Order 992: $0.00 settled of $45.00 promised.",
            "checked_at": "2026-11-04T12:00:00Z",
        },
        "remediation": {
            "idempotency_key": "refund:992:45.00",
            "amount_usd": "45.00",
            "status": "executed",
        },
    }


def _read(path: str) -> str:
    return Path(path).expanduser().read_text().strip()


def _cmd_demo(_args: argparse.Namespace) -> int:
    # Ephemeral key: this is a live demonstration, not the pinned fixture.
    private_key, public_key = generate_keypair()
    receipt = sign_receipt(sample_payload(), private_key)
    json.dump(
        {
            "receipt": receipt,
            "public_key": encode_public_key(public_key),
            "note": "ephemeral demo key, not the pinned sample key",
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    envelope = json.loads(_read(args.file))
    pinned = args.public_key
    if args.public_key_file:
        pinned = _read(args.public_key_file).splitlines()[0].strip()
    result = verify_receipt(
        envelope, pinned_public_key=pinned, expected_key_id=args.key_id
    )
    sys.stdout.write(result.model_dump_json(indent=2) + "\n")
    return 0 if result.valid else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.receipt",
        description="Sign or verify Settleye execution receipts.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="sign the sample receipt with a new key")
    demo.set_defaults(func=_cmd_demo)

    verify = sub.add_parser("verify", help="verify one receipt envelope")
    verify.add_argument("--file", required=True, help="envelope JSON path")
    verify.add_argument("--public-key", default=None, help="pinned base64url")
    verify.add_argument("--public-key-file", default=None, help="one-line pin")
    verify.add_argument("--key-id", default=None, help="expected issuer key id")
    verify.set_defaults(func=_cmd_verify)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
