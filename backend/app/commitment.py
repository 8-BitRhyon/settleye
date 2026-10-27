"""Commitment-state guards: what reaches the ledger join, and with what proof.

Only net-binding, un-retracted commitments are reconcilable. Conditionals,
supersessions, retractions, and policy explanations resolve without ever
touching the ledger, so they can neither drift nor burn remediation money.
Evidence quotes must occur verbatim in the transcript; an invented quote
fails the join before anything else runs.
"""

from app.models import PromiseEntity


def is_binding(promise: PromiseEntity) -> bool:
    """True only when the commitment survived the dialogue intact."""
    return promise.terminal_status == "binding"


def verify_citation(transcript: str, promise: PromiseEntity) -> bool:
    """True when the evidence quote occurs verbatim in the transcript."""
    quote = promise.evidence_span.strip()
    return bool(quote) and quote in transcript
