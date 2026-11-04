"""End-to-end audit: transcript in, drift report out.

An optional Jev gate runs first. When it is present and the transcript is
unlikely to contain a financial promise, the generative extraction call is
skipped entirely. The gate never decides whether money moved; reconciliation
stays deterministic code.

Every report carries the audit provenance that a signed receipt binds:
SHA-256 of the exact transcript bytes, the non-empty line count, and the UTC
audit time. The gate-skip path reports the same provenance as the full path,
so an unsigned-looking report can still be told apart by its digest, never by
a missing field.
"""

import hashlib
from datetime import datetime, timezone

from app.extract.client import MetaModelClient
from app.extract.pipeline import extract_promises
from app.gate.jev import GateDecision, JevClient, gate_transcript
from app.ledger.base import LedgerAdapter
from app.models import AuditReport
from app.reconcile.engine import reconcile


def transcript_sha256(transcript: str) -> str:
    """SHA-256 hex of the exact transcript text, UTF-8 encoded."""
    return hashlib.sha256(transcript.encode("utf-8")).hexdigest()


def transcript_turns(transcript: str) -> int:
    """Count non-empty lines: blank separators are not turns."""
    return sum(1 for line in transcript.splitlines() if line.strip())


def utc_now_iso() -> str:
    """UTC ISO 8601 with a Z suffix, second precision."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


async def audit_transcript(
    transcript: str,
    client: MetaModelClient,
    ledger: LedgerAdapter,
    gate_client: JevClient | None = None,
) -> AuditReport:
    """Extract promises and reconcile each against the ledger."""
    digest = transcript_sha256(transcript)
    turns = transcript_turns(transcript)
    audited_at = utc_now_iso()

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
                transcript_sha256=digest,
                transcript_turns=turns,
                audited_at=audited_at,
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
        transcript_sha256=digest,
        transcript_turns=turns,
        audited_at=audited_at,
    )
