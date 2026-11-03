"""End-to-end audit: transcript in, drift report out.

An optional Jev gate runs first. When it is present and the transcript is
unlikely to contain a financial promise, the generative extraction call is
skipped entirely. The gate never decides whether money moved; reconciliation
stays deterministic code.
"""

from app.extract.client import MetaModelClient
from app.extract.pipeline import extract_promises
from app.gate.jev import GateDecision, JevClient, gate_transcript
from app.ledger.base import LedgerAdapter
from app.models import AuditReport
from app.reconcile.engine import reconcile


async def audit_transcript(
    transcript: str,
    client: MetaModelClient,
    ledger: LedgerAdapter,
    gate_client: JevClient | None = None,
) -> AuditReport:
    """Extract promises and reconcile each against the ledger."""
    gate: GateDecision | None = None
    if gate_client is not None:
        gate = await gate_transcript(gate_client, transcript)
        if gate.skip_extraction:
            return AuditReport(
                promises=[],
                results=[],
                drifts=[],
                total_at_risk_usd=0.0,
                verdict="verified_green",
            )

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
