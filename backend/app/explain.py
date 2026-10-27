"""Per-drift plain-English explanations, on demand only.

The auditor already proves drift with numbers; this module says what the
numbers mean in merchant words. It fires once per drift when a human asks
(POST /explain or the inbox Explain button), never during the sweep, so a
batch of clean transcripts costs zero extra model calls. The reply is
display-only and still untrusted: empty output raises, long output is
capped, and the prompt binds the model to its inputs.
"""

from app.extract.client import MetaModelClient
from app.models import PromiseEntity

MAX_CHARS = 500

EXPLAIN_SYSTEM_PROMPT = """You explain one flagged refund mismatch to a busy store owner in one or two short sentences. Plain words, no jargon. Use only the facts given below: what the agent said, what the ledger shows, and the amount at risk. Do not invent order details, policies, or next steps."""


class ExplainError(Exception):
    """The model produced no usable explanation within the retry budget."""


async def explain_drift(
    promise: PromiseEntity,
    ledger_summary: str,
    amount_at_risk_usd: float,
    client: MetaModelClient,
) -> str:
    """Return a capped plain-English explanation of one drift."""
    evidence = promise.evidence_span or promise.asserted_state
    user_text = (
        f"Agent said: {evidence}\n"
        f"Ledger shows: {ledger_summary}\n"
        f"Amount at risk: ${amount_at_risk_usd:.2f}\n"
        "Explain what happened in one or two short sentences."
    )
    raw = await client.chat(
        [
            {"role": "system", "content": EXPLAIN_SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        temperature=0.2,
    )
    text = " ".join(raw.split())
    if not text:
        raise ExplainError("Model returned no explanation text.")
    if len(text) > MAX_CHARS:
        text = text[: MAX_CHARS - 1].rstrip() + "…"
    return text
