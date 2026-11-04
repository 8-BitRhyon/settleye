"""Settleye API entry point."""

import json
import os
import threading
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict

from app.audit import audit_transcript, utc_now_iso
from app.extract.client import MODEL_ID, MetaModelClient, model_id
from app.keyring import (
    REGISTRY_ERROR,
    KeyRegistry,
    KeyringError,
    default_registry_path,
    verify_with_registry,
)
from app.ledger.mock import MockLedgerAdapter
from app.models import AuditReport, PromiseEntity, RemediationReceipt
from app.receipt import (
    INVALID_PINNED_KEY,
    KEY_ID_MISMATCH,
    UNPINNED,
    VerifyResult,
    verify_receipt,
)
from app.remediate.service import (
    RemediationError,
    RemediationService,
    promise_key,
)
from app.signing import ReceiptContext, build_signer_from_env
from app.value import ValueLedger, summarize

app = FastAPI(title="Settleye", version="0.1.0")

# Lazy singletons are created on the first request. Without a creation lock,
# several cold-start requests can each build a separate service and lock.
_init_lock = threading.Lock()

# The judging demo runs the dashboard (Vite dev or static hosting) on a
# different origin than the API. Extra origins come from ALLOWED_ORIGINS
# as a comma-separated list; localhost:5173 is always allowed for dev.
_extra_origins = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", *_extra_origins],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


class AuditRequest(BaseModel):
    transcript: str


class RemediateRequest(BaseModel):
    promise: PromiseEntity
    amount_usd: float
    # Optional audit provenance. When digest and turns are present, the
    # service attaches a signed v1 receipt; when absent, the durable receipt
    # still works and stays unsigned for backward compatibility.
    transcript_sha256: str | None = None
    transcript_turns: int | None = None
    audited_at: str | None = None
    ledger_summary: str | None = None


class ExplainRequest(BaseModel):
    promise: PromiseEntity
    ledger_summary: str = ""
    amount_usd: float


def fixture_path() -> Path:
    return Path(__file__).resolve().parents[2] / "fixtures" / "mock_ledger.json"


def build_client() -> MetaModelClient:
    api_key = os.environ.get("BASETEN_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=503, detail="BASETEN_API_KEY is not configured."
        )
    return MetaModelClient(api_key=api_key, model=model_id())


def get_ledger() -> MockLedgerAdapter:
    ledger = getattr(app.state, "ledger", None)
    if ledger is None:
        with _init_lock:
            ledger = getattr(app.state, "ledger", None)
            if ledger is None:
                data = json.loads(fixture_path().read_text())
                ledger = MockLedgerAdapter(data)
                app.state.ledger = ledger
    return ledger


def get_remediation() -> RemediationService:
    service = getattr(app.state, "remediation", None)
    if service is None:
        with _init_lock:
            service = getattr(app.state, "remediation", None)
            if service is None:
                service = RemediationService(signer=build_signer_from_env())
                app.state.remediation = service
    return service


def load_key_registry() -> KeyRegistry | None:
    """Registry at the configured path, or None when no keys are configured.

    A file that exists but holds no records is a broken trust root, not an
    invitation to fall back to unpinned verification. Raise so the caller can
    fail closed.
    """
    path = default_registry_path()
    if not path.exists():
        return None
    registry = KeyRegistry.load(path)
    if not registry.records:
        raise KeyringError(f"Key registry {path} exists but has no records.")
    return registry


def get_value() -> ValueLedger:
    value = getattr(app.state, "value", None)
    if value is None:
        with _init_lock:
            value = getattr(app.state, "value", None)
            if value is None:
                value = ValueLedger()
                app.state.value = value
    return value


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/audit", response_model=AuditReport)
async def audit(request: AuditRequest) -> AuditReport:
    from app.extract.pipeline import ExtractionError

    try:
        return await audit_transcript(
            request.transcript, build_client(), get_ledger()
        )
    except ExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.post("/remediate", response_model=RemediationReceipt)
def remediate(request: RemediateRequest) -> RemediationReceipt:
    from app.reconcile.engine import reconcile

    service = get_remediation()
    # Same key function as the service: promise identity, never the live
    # shortfall, so a partial refund cannot mint a second key.
    key = promise_key(request.promise, request.amount_usd)
    # Never authorize more than the promise, even on a replay: a tampered
    # amount must not look settled just because the original receipt exists.
    if (
        request.promise.amount is not None
        and request.amount_usd > request.promise.amount + 0.005
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Amount mismatch: promise is ${request.promise.amount:.2f}, "
                f"request asked ${request.amount_usd:.2f}."
            ),
        )
    # Hold the service lock across find, reconcile, and write so a concurrent
    # twin can never observe a moved ledger without its receipt.
    with service.lock:
        # Key first: a retried request returns the original receipt without
        # touching the ledger, even though the drift is now settled.
        if (existing := service.find(key)) is not None:
            return existing
        ledger_checked_at = utc_now_iso()
        result = reconcile(request.promise, get_ledger())
        if result.verdict != "drift":
            raise HTTPException(
                status_code=422, detail=f"Nothing to remediate: {result.verdict}."
            )
        # Never refund more than the live shortfall, no matter what the client
        # claims. A mismatch means the ledger moved under the request.
        if abs(result.amount_at_risk_usd - request.amount_usd) > 0.005:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Amount mismatch: ledger shows ${result.amount_at_risk_usd:.2f} "
                    f"at risk, request asked ${request.amount_usd:.2f}."
                ),
            )
        try:
            context: ReceiptContext | None = None
            if (
                request.transcript_sha256
                and request.transcript_turns is not None
            ):
                context = ReceiptContext(
                    transcript_sha256=request.transcript_sha256,
                    transcript_turns=request.transcript_turns,
                    audited_at=request.audited_at or "",
                    # Never sign a client-supplied observation. The issuer signs
                    # only the ledger summary its own reconcile just produced.
                    ledger_summary=result.ledger_summary,
                    ledger_checked_at=ledger_checked_at,
                    model_id=model_id(),
                )
            return service.remediate(
                result, get_ledger(), get_value(), context=context
            )
        except RemediationError as exc:
            raise HTTPException(status_code=422, detail=str(exc))


@app.get("/value")
def value() -> dict[str, float | int]:
    return summarize(get_value())


class ReceiptVerifyRequest(BaseModel):
    """Verify body: a wrapped envelope, or the bare envelope itself."""

    model_config = ConfigDict(extra="allow")

    receipt: dict[str, Any] | None = None
    public_key: str | None = None
    key_id: str | None = None
    merchant_public_key: str | None = None
    merchant_key_id: str | None = None
    require_merchant: bool = False

    def envelope(self) -> dict[str, Any]:
        if self.receipt is not None:
            return self.receipt
        return dict(self.model_extra or {})


@app.get("/receipt/keys")
def receipt_keys() -> list[dict[str, Any]]:
    """Public key history only: ids, base64url keys, states, timestamps."""
    try:
        registry = load_key_registry()
    except KeyringError as exc:
        raise HTTPException(
            status_code=503, detail=f"Key registry unavailable: {exc}"
        ) from exc
    if registry is None:
        return []
    return registry.public_records()


@app.post("/receipt/verify", response_model=None)
def verify_execution_receipt(request: ReceiptVerifyRequest) -> dict[str, Any]:
    """Pure verification: no model call, no ledger read, always HTTP 200.

    A supplied public key is a real pin. A `key_id` alone is not a trust
    anchor: with a registry it is checked against the published record, and
    without one the request fails closed. With no pin, a configured registry
    decides which public key may have signed; otherwise verification remains
    unpinned and only proves internal consistency.
    """
    if request.public_key is not None:
        return verify_receipt(
            request.envelope(),
            pinned_public_key=request.public_key,
            expected_key_id=request.key_id,
            merchant_public_key=request.merchant_public_key,
            expected_merchant_key_id=request.merchant_key_id,
            require_merchant=request.require_merchant,
        ).model_dump()
    try:
        registry = load_key_registry()
    except KeyringError:
        return VerifyResult(valid=False, reason=REGISTRY_ERROR).model_dump()
    if registry is not None:
        result = verify_with_registry(
            request.envelope(),
            registry,
            merchant_public_key=request.merchant_public_key,
            expected_merchant_key_id=request.merchant_key_id,
            require_merchant=request.require_merchant,
        )
        if (
            request.key_id is not None
            and result.key_id is not None
            and result.key_id != request.key_id
        ):
            return VerifyResult(
                valid=False,
                reason=KEY_ID_MISMATCH,
                receipt_id=result.receipt_id,
                key_id=result.key_id,
            ).model_dump()
        return result.model_dump()
    if request.key_id is not None:
        return VerifyResult(
            valid=False,
            reason=INVALID_PINNED_KEY,
            key_id=request.key_id,
        ).model_dump()
    result = verify_receipt(
        request.envelope(),
        merchant_public_key=request.merchant_public_key,
        expected_merchant_key_id=request.merchant_key_id,
        require_merchant=request.require_merchant,
    )
    if result.valid:
        # No caller pin and no registry: the signature is internally
        # consistent but has no issuer attribution. Do not certify it.
        return VerifyResult(
            valid=False,
            reason=UNPINNED,
            receipt_id=result.receipt_id,
            key_id=result.key_id,
        ).model_dump()
    return result.model_dump()


class ExplainResponse(BaseModel):
    explanation: str


@app.post("/explain", response_model=ExplainResponse)
async def explain(request: ExplainRequest) -> ExplainResponse:
    from app.explain import ExplainError, explain_drift

    try:
        text = await explain_drift(
            request.promise,
            request.ledger_summary,
            request.amount_usd,
            build_client(),
        )
    except ExplainError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return ExplainResponse(explanation=text)
