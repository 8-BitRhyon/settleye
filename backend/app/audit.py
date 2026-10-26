"""End-to-end audit: transcript in, drift report out."""

from app.extract.client import MetaModelClient
from app.extract.pipeline import extract_promises
from app.ledger.base import LedgerAdapter
from app.models import AuditReport
from app.reconcile.engine import reconcile


async def audit_transcript(
    transcript: str, client: MetaModelClient, ledger: LedgerAdapter
) -> AuditReport:
    """Extract promises and reconcile each against the ledger."""
    promises = await extract_promises(transcript, client)
    results = [reconcile(promise, ledger) for promise in promises]
    drifts = [result for result in results if result.verdict == "drift"]
    total = round(sum(drift.amount_at_risk_usd for drift in drifts), 2)
    return AuditReport(
        promises=promises,
        results=results,
        drifts=drifts,
        total_at_risk_usd=total,
        verdict="drift_found" if drifts else "verified_green",
    )
