"""Signed, portable execution receipts.

A receipt is a JSON envelope that binds one transcript digest, one promise,
the ledger state that contradicted it, the remediation idempotency key, and
the issuer identity. The envelope is canonicalized (sorted keys, no
whitespace, UTF-8) and signed with Ed25519. The receipt id is the SHA-256 of
the same canonical bytes, so any edit to any payload field changes both the
id and the signature.

A receipt may also carry a merchant countersignature in the envelope. The
merchant signs the receipt id, its key id, its role, and the acknowledgement
time. It does not sign the payload again, so the issuer id and signature stay
byte-identical when a countersignature is attached.

What this proves: the holder of each private key signed the bytes attributed
to it. What it does not prove: that the transcript is authentic, that the
ledger read was correct, or that money actually left Stripe. Those remain
claims by the issuer, and the signature only makes them attributable and
tamper evident.

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
MERCHANT_MISSING = "merchant_missing"
MERCHANT_KEY_ID_MISMATCH = "merchant_key_id_mismatch"
MERCHANT_KEY_MISMATCH = "merchant_key_mismatch"
MERCHANT_SIGNATURE_INVALID = "merchant_signature_invalid"
MERCHANT_PUBLIC_KEY_INVALID = "merchant_public_key_invalid"

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


class CounterSignature(_Strict):
    """A second party's acknowledgement of an already-signed receipt."""

    role: Literal["merchant"]
    key_id: str
    alg: str
    public_key: str
    acknowledged_at: str
    value: str


class ReceiptPayload(_Strict):
    """The signed half of the envelope: no id, signature, or countersigns."""

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
    countersignatures: list[CounterSignature] = Field(default_factory=list)


class VerifyResult(BaseModel):
    """Verification outcome. `receipt_id` is the recomputed id of the bytes."""

    valid: bool
    reason: str
    receipt_id: str | None = None
    key_id: str | None = None
    merchant_valid: bool | None = None
    merchant_key_id: str | None = None


def _b64u_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64u_decode(value: str) -> bytes:
    """Strict base64url decode: bad alphabet is an error, not noise."""
    if not isinstance(value, str) or not value:
        raise ValueError("empty base64url value")
    padding = "=" * (-len(value) % 4)
    return base64.b64decode(value + padding, altchars=b"-_", validate=True)


def canonical_payload(payload: Mapping[str, Any] | BaseModel) -> bytes:
    """Canonical bytes: sorted keys, no whitespace, UTF-8, no derived fields.

    `countersignatures` is envelope metadata, not issuer-signed content, so
    attaching a merchant signature cannot change the issuer bytes.
    """
    data: dict[str, Any] = (
        payload.model_dump(mode="json")
        if isinstance(payload, BaseModel)
        else dict(payload)
    )
    data.pop("receipt_id", None)
    data.pop("signature", None)
    data.pop("countersignatures", None)
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
    # Generated in memory, never a literal credential.
    private_key = Ed25519PrivateKey.generate()  # gitleaks:allow
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
    raw.pop("countersignatures", None)
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


def countersign_message(
    receipt_id: str, key_id: str, acknowledged_at: str
) -> bytes:
    """Canonical bytes a merchant signs.

    The payload is already bound through `receipt_id`, so the merchant only
    acknowledges this id in this role at this time.
    """
    return json.dumps(
        {
            "receipt_id": receipt_id,
            "role": "merchant",
            "key_id": key_id,
            "acknowledged_at": acknowledged_at,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def countersign_receipt(
    envelope: Mapping[str, Any] | BaseModel,
    private_key: Ed25519PrivateKey,
    key_id: str,
    acknowledged_at: str,
) -> dict[str, Any]:
    """Append a merchant countersignature to a valid receipt.

    Returns a JSON-ready dict. The input is never mutated and the issuer
    signature is untouched because the countersign field is not canonical.
    """
    try:
        parsed = ReceiptEnvelope.model_validate(envelope)
    except (ValidationError, TypeError, ValueError) as exc:
        raise ValueError("invalid receipt envelope") from exc

    # Only countersign a receipt whose issuer half already checks out.
    issuer_check = verify_receipt(parsed)
    if not issuer_check.valid:
        raise ValueError(
            f"invalid receipt envelope: {issuer_check.reason}"
        )

    body = parsed.model_dump(mode="json")
    signed = private_key.sign(
        countersign_message(parsed.receipt_id, key_id, acknowledged_at)
    )
    body["countersignatures"] = [
        *parsed.countersignatures,
        CounterSignature(
            role="merchant",
            key_id=key_id,
            alg=SIGNATURE_ALG,
            public_key=encode_public_key(private_key.public_key()),
            acknowledged_at=acknowledged_at,
            value=_b64u_encode(signed),
        ),
    ]
    return ReceiptEnvelope.model_validate(body).model_dump(mode="json")


def _merchant_failure(
    countersig: CounterSignature,
    receipt_id: str,
    merchant_public_key: str | None,
    expected_merchant_key_id: str | None,
) -> str | None:
    """Reason code for one countersignature, or None when it is valid."""
    if countersig.role != "merchant" or countersig.alg != SIGNATURE_ALG:
        return MERCHANT_SIGNATURE_INVALID

    if (
        expected_merchant_key_id is not None
        and expected_merchant_key_id != countersig.key_id
    ):
        return MERCHANT_KEY_ID_MISMATCH

    try:
        raw_merchant_key = _b64u_decode(countersig.public_key)
        merchant_key = Ed25519PublicKey.from_public_bytes(raw_merchant_key)
    except (ValueError, TypeError, binascii.Error):
        return MERCHANT_PUBLIC_KEY_INVALID

    if merchant_public_key is not None:
        try:
            pinned_merchant = _b64u_decode(merchant_public_key)
        except (ValueError, TypeError, binascii.Error):
            return MERCHANT_PUBLIC_KEY_INVALID
        if pinned_merchant != raw_merchant_key:
            return MERCHANT_KEY_MISMATCH

    try:
        signature = _b64u_decode(countersig.value)
    except (ValueError, TypeError, binascii.Error):
        return MERCHANT_SIGNATURE_INVALID

    message = countersign_message(
        receipt_id, countersig.key_id, countersig.acknowledged_at
    )
    try:
        merchant_key.verify(signature, message)
    except (InvalidSignature, ValueError):
        return MERCHANT_SIGNATURE_INVALID

    return None


def verify_receipt(
    envelope: Mapping[str, Any] | BaseModel,
    pinned_public_key: str | None = None,
    expected_key_id: str | None = None,
    merchant_public_key: str | None = None,
    expected_merchant_key_id: str | None = None,
    require_merchant: bool = False,
) -> VerifyResult:
    """Verify one envelope. Fails closed on any malformed input.

    Checks run in order: structure, receipt id, alg, signature, then the
    optional issuer pin. A caller that pins a key gets issuer authenticity; a
    caller that does not only gets internal consistency.

    Merchant countersignatures are checked next, against their own optional
    pin and key id. An invalid countersignature that is present always fails.
    A missing one fails only when `require_merchant` is set.
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

    if not parsed.countersignatures:
        if require_merchant:
            return VerifyResult(
                valid=False,
                reason=MERCHANT_MISSING,
                receipt_id=recomputed,
                key_id=key_id,
                merchant_valid=False,
            )
        return VerifyResult(
            valid=True, reason=OK, receipt_id=recomputed, key_id=key_id
        )

    for countersig in parsed.countersignatures:
        reason = _merchant_failure(
            countersig,
            parsed.receipt_id,
            merchant_public_key,
            expected_merchant_key_id,
        )
        if reason is not None:
            return VerifyResult(
                valid=False,
                reason=reason,
                receipt_id=recomputed,
                key_id=key_id,
                merchant_valid=False,
                merchant_key_id=countersig.key_id,
            )

    return VerifyResult(
        valid=True,
        reason=OK,
        receipt_id=recomputed,
        key_id=key_id,
        merchant_valid=True,
        merchant_key_id=parsed.countersignatures[-1].key_id,
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


def _load_private_key(path: str) -> Ed25519PrivateKey:
    """Read a base64url 32-byte Ed25519 seed. Never echo the seed."""
    seed = _b64u_decode(_read(path).splitlines()[0].strip())
    if len(seed) != 32:
        raise ValueError(
            "private key file must hold a base64url 32-byte Ed25519 seed"
        )
    return Ed25519PrivateKey.from_private_bytes(seed)


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
    merchant_pinned = args.merchant_public_key
    if args.merchant_public_key_file:
        merchant_pinned = _read(
            args.merchant_public_key_file
        ).splitlines()[0].strip()
    result = verify_receipt(
        envelope,
        pinned_public_key=pinned,
        expected_key_id=args.key_id,
        merchant_public_key=merchant_pinned,
        expected_merchant_key_id=args.merchant_key_id,
        require_merchant=args.require_merchant,
    )
    sys.stdout.write(result.model_dump_json(indent=2) + "\n")
    return 0 if result.valid else 1


def _cmd_countersign(args: argparse.Namespace) -> int:
    try:
        private_key = _load_private_key(args.private_key_file)
        envelope = json.loads(_read(args.file))
        countersigned = countersign_receipt(
            envelope, private_key, args.key_id, args.acknowledged_at
        )
        Path(args.out).expanduser().write_text(
            json.dumps(countersigned, indent=2) + "\n"
        )
    except (OSError, ValueError, ValidationError) as exc:
        sys.stderr.write(f"countersign failed: {exc}\n")
        return 1

    # Only public material is reported: the seed never leaves the file.
    result = verify_receipt(countersigned)
    sys.stdout.write(
        json.dumps(
            {
                "out": args.out,
                "receipt_id": countersigned["receipt_id"],
                "key_id": args.key_id,
                "public_key": countersigned["countersignatures"][-1][
                    "public_key"
                ],
                "valid": result.valid,
                "merchant_valid": result.merchant_valid,
            },
            indent=2,
        )
        + "\n"
    )
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
    verify.add_argument(
        "--merchant-public-key", default=None, help="pinned base64url"
    )
    verify.add_argument(
        "--merchant-public-key-file", default=None, help="one-line pin"
    )
    verify.add_argument(
        "--merchant-key-id", default=None, help="expected merchant key id"
    )
    verify.add_argument(
        "--require-merchant",
        action="store_true",
        help="fail when no merchant countersignature exists",
    )
    verify.set_defaults(func=_cmd_verify)

    countersign = sub.add_parser(
        "countersign", help="attach a merchant signature to a receipt"
    )
    countersign.add_argument(
        "--file", required=True, help="envelope JSON path"
    )
    countersign.add_argument(
        "--private-key-file", required=True, help="base64url Ed25519 seed"
    )
    countersign.add_argument("--key-id", required=True, help="merchant key id")
    countersign.add_argument(
        "--acknowledged-at", required=True, help="ISO 8601 timestamp"
    )
    countersign.add_argument("--out", required=True, help="output JSON path")
    countersign.set_defaults(func=_cmd_countersign)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
