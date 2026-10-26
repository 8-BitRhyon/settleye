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


class ReconciliationResult(BaseModel):
    """Outcome of diffing one promise against ledger state."""

    promise: PromiseEntity
    verdict: Literal["verified", "drift", "unverifiable"]
    ledger_summary: str = ""
    amount_at_risk_usd: float = 0.0
