"""The Jev gate must save the generative call, not change the verdict.

If a transcript promises nothing, the gate returns early and no model tokens
are spent. If it might promise, the pipeline runs unchanged and the ledger
verdict is identical to the ungated path.
"""

import asyncio
import json
from pathlib import Path

import httpx

from app.audit import audit_transcript
from app.extract.client import MetaModelClient
from app.gate.jev import JevClient
from app.ledger.mock import MockLedgerAdapter

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"

PHANTOM = json.dumps(
    [
        {
            "action": "refund",
            "amount": 45.00,
            "order_id": "992",
            "target_system": "stripe",
            "asserted_state": "full refund processed",
            "confidence": 0.9,
            "evidence_span": "I have processed a full $45 refund for order #992.",
        }
    ]
)

CLEAN = "customer: where is my order\nagent: it ships Thursday"


class SpyModel:
    """Counts generative calls."""

    def __init__(self, reply: str) -> None:
        self.calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            self.calls += 1
            return httpx.Response(
                200,
                json={"choices": [{"message": {"content": reply}}], "model": "test"},
            )

        self.client = MetaModelClient(
            api_key="k", transport=httpx.MockTransport(handler)
        )


def jev_client(has_promise: float) -> JevClient:
    payload = {
        "answers": {
            "has_promise": {"type": "noul", "noul": has_promise},
            "modality": {
                "type": "choice",
                "choice": "info_only" if has_promise < 0.2 else "binding",
                "confidence": 0.9,
            },
        }
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    return JevClient(api_key="j", transport=httpx.MockTransport(handler))


def ledger() -> MockLedgerAdapter:
    return MockLedgerAdapter(
        json.loads((FIXTURES / "mock_ledger.json").read_text())
    )


def test_gate_skips_the_generative_call_when_no_promise() -> None:
    spy = SpyModel(CLEAN)
    report = asyncio.run(
        audit_transcript(CLEAN, spy.client, ledger(), jev_client(0.03))
    )
    assert spy.calls == 0
    assert report.verdict == "verified_green"
    assert report.promises == []


def test_gate_passes_through_and_verdict_is_unchanged() -> None:
    spy = SpyModel(PHANTOM)
    gated = asyncio.run(
        audit_transcript("refund $45 order #992", spy.client, ledger(), jev_client(0.97))
    )
    assert spy.calls >= 1
    assert gated.verdict == "drift_found"
    assert gated.total_at_risk_usd == 45.00


def test_ungated_path_still_works() -> None:
    spy = SpyModel(PHANTOM)
    report = asyncio.run(audit_transcript("refund $45 order #992", spy.client, ledger()))
    assert spy.calls >= 1
    assert report.total_at_risk_usd == 45.00
