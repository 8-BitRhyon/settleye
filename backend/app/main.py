"""Settleye API entry point."""

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.audit import audit_transcript
from app.extract.client import MODEL_ID, MetaModelClient, model_id
from app.ledger.mock import MockLedgerAdapter
from app.models import AuditReport, PromiseEntity, RemediationReceipt
from app.remediate.service import RemediationError, RemediationService
from app.value import ValueLedger, summarize

app = FastAPI(title="Settleye", version="0.1.0")

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
        data = json.loads(fixture_path().read_text())
        ledger = MockLedgerAdapter(data)
        app.state.ledger = ledger
    return ledger


def get_remediation() -> RemediationService:
    service = getattr(app.state, "remediation", None)
    if service is None:
        service = RemediationService()
        app.state.remediation = service
    return service


def get_value() -> ValueLedger:
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
    from app.remediate.service import idempotency_key

    service = get_remediation()
    key = idempotency_key(
        request.promise.action, request.promise.order_id, request.amount_usd
    )
    # Key first: a retried request returns the original receipt without
    # touching the ledger, even though the drift is now settled.
    if (existing := service.find(key)) is not None:
        return existing
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
        return service.remediate(result, get_ledger(), get_value())
    except RemediationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/value")
def value() -> dict[str, float | int]:
    return summarize(get_value())


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
