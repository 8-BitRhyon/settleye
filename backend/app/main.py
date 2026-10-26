"""PromiseCheck API entry point."""

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.audit import audit_transcript
from app.extract.client import MODEL_ID, MetaModelClient
from app.ledger.mock import MockLedgerAdapter
from app.models import AuditReport, PromiseEntity, RemediationReceipt
from app.remediate.service import RemediationError, RemediationService
from app.value import ValueLedger, summarize

app = FastAPI(title="PromiseCheck", version="0.1.0")


class AuditRequest(BaseModel):
    transcript: str


class RemediateRequest(BaseModel):
    promise: PromiseEntity
    amount_usd: float


def fixture_path() -> Path:
    return Path(__file__).resolve().parents[2] / "fixtures" / "mock_ledger.json"


def build_client() -> MetaModelClient:
    api_key = os.environ.get("BASETEN_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=503, detail="BASETEN_API_KEY is not configured."
        )
    return MetaModelClient(api_key=api_key, model=MODEL_ID)


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
