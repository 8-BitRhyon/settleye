"""Core schemas: what the agent promised vs what the ledger recorded."""

from typing import Literal

from pydantic import BaseModel, Field


class PromiseEntity(BaseModel):
    """One discrete promise extracted from a support transcript."""

    action: Literal["refund", "cancel", "reship", "credit", "other"]
    amount: float | None = Field(default=None, description="USD amount, if stated")
    order_id: str | None = None
    target_system: Literal["stripe", "shopify", "unknown"] = "unknown"
    asserted_state: str = Field(description="What the agent claimed is now true")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_span: str = Field(default="", description="Verbatim transcript quote")
    terminal_status: Literal[
        "binding", "conditional", "superseded", "retracted", "info_only"
    ] = Field(
        default="binding",
        description="Dialogue end-state of the commitment. Only binding reaches the ledger join.",
    )


class ReconciliationResult(BaseModel):
    """Outcome of diffing one promise against ledger state."""

    promise: PromiseEntity
    verdict: Literal["verified", "drift", "unverifiable", "not_binding"]
    ledger_summary: str = ""
    amount_at_risk_usd: float = 0.0


class RemediationReceipt(BaseModel):
    """Proof that a drift was acted on, safe to retry and show on camera."""

    idempotency_key: str
    promise: PromiseEntity
    amount_usd: float
    status: Literal["executed", "already_executed"]


class RepeatOrder(BaseModel):
    """One order promised across several transcripts: memory, not model."""

    order_id: str = Field(description="Normalized ledger key, no # prefix")
    sources: list[str] = Field(default_factory=list)
    occurrences: int = 0
    total_at_risk_usd: float = 0.0


class AuditReport(BaseModel):
    """One transcript audited end to end: promises, drifts, totals."""

    promises: list[PromiseEntity] = Field(default_factory=list)
    results: list[ReconciliationResult] = Field(default_factory=list)
    drifts: list[ReconciliationResult] = Field(default_factory=list)
    total_at_risk_usd: float = 0.0
    verdict: Literal["verified_green", "drift_found"] = "verified_green"


class BatchItemReport(BaseModel):
    """One transcript inside a daemon sweep: report or isolated error."""

    source: str = Field(description="Transcript filename or feed identifier")
    report: AuditReport | None = None
    error: str | None = None


class BatchReport(BaseModel):
    """A whole daemon sweep: every item plus money-sorted drift."""

    items: list[BatchItemReport] = Field(default_factory=list)
    drifts: list[ReconciliationResult] = Field(default_factory=list)
    repeat_orders: list[RepeatOrder] = Field(default_factory=list)
    total_at_risk_usd: float = 0.0
    remediated: int = 0
    remediation_errors: list[str] = Field(default_factory=list)
    verdict: Literal["verified_green", "drift_found", "batch_error"] = (
        "verified_green"
    )
