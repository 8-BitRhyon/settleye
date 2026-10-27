"""Tests for commitment-state handling (Gemini report, Candidate C).

Only net-binding, un-retracted commitments reach the ledger join.
Conditionals, retractions, supersessions, and policy explanations resolve
to `not_binding`, never to drift. Evidence quotes must occur verbatim.
"""

from app.commitment import verify_citation
from app.models import PromiseEntity

STATUSES = ("binding", "conditional", "superseded", "retracted", "info_only")


def binding_refund(**overrides) -> PromiseEntity:
    fields: dict = {
        "action": "refund",
        "amount": 45.00,
        "order_id": "992",
        "target_system": "stripe",
        "asserted_state": "full refund processed",
        "confidence": 0.9,
        "evidence_span": "I have processed a full $45 refund for order #992.",
    }
    fields.update(overrides)
    return PromiseEntity(**fields)


def test_all_terminal_statuses_validate() -> None:
    for status in STATUSES:
        assert binding_refund(terminal_status=status).terminal_status == status


def test_missing_status_defaults_to_binding() -> None:
    raw = binding_refund().model_dump()
    del raw["terminal_status"]
    assert PromiseEntity.model_validate(raw).terminal_status == "binding"


def test_verbatim_quote_verifies() -> None:
    transcript = "Agent: I have processed a full $45 refund for order #992."
    assert verify_citation(transcript, binding_refund()) is True


def test_invented_quote_fails() -> None:
    assert (
        verify_citation(
            "Agent: let me look into that.",
            binding_refund(),
        )
        is False
    )


def test_empty_quote_fails() -> None:
    entity = binding_refund(evidence_span="")
    assert verify_citation("Agent: refund processed.", entity) is False
