"""Audit provenance: digest, turn count, and audit time on every path.

The signed receipt binds these values, so they must be present and correct
whether extraction ran or the Jev gate skipped it.
"""

import hashlib
import json
import re
from pathlib import Path

import httpx

from app.audit import audit_transcript
from app.extract.client import MetaModelClient
from app.gate.jev import JevClient
from app.ledger.mock import MockLedgerAdapter

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
TRANSCRIPT = (
    "Customer: The jacket arrived torn.\n"
    "\n"
    "Agent: I processed a $45 refund for order #992.\n"
)
EMPTY_JSON = "[]"


def mock_client(reply: str = EMPTY_JSON) -> MetaModelClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": reply}}], "model": "t"},
        )

    return MetaModelClient(api_key="k", transport=httpx.MockTransport(handler))


def mock_ledger() -> MockLedgerAdapter:
    return MockLedgerAdapter(
        json.loads((FIXTURES / "mock_ledger.json").read_text())
    )


def low_promise_gate() -> JevClient:
    """A gate that always skips extraction."""

    def gate_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "answers": {
                    "has_promise": {"noul": 0.01},
                    "modality": {
                        "choice": "info_only",
                        "confidence": 0.99,
                    },
                }
            },
        )

    return JevClient(api_key="jev", transport=httpx.MockTransport(gate_handler))


def unreachable_model() -> MetaModelClient:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("model called on gate skip")

    return MetaModelClient(api_key="k", transport=httpx.MockTransport(handler))


def assert_provenance(report, transcript: str) -> None:
    assert report.transcript_sha256 == hashlib.sha256(
        transcript.encode("utf-8")
    ).hexdigest()
    assert report.transcript_turns == 2
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", report.audited_at
    )


async def test_normal_path_reports_provenance() -> None:
    report = await audit_transcript(TRANSCRIPT, mock_client(), mock_ledger())
    assert_provenance(report, TRANSCRIPT)


async def test_gate_skip_path_reports_same_provenance() -> None:
    report = await audit_transcript(
        TRANSCRIPT,
        unreachable_model(),
        mock_ledger(),
        gate_client=low_promise_gate(),
    )
    assert report.promises == []
    assert report.verdict == "verified_green"
    assert_provenance(report, TRANSCRIPT)


async def test_blank_lines_are_not_turns() -> None:
    transcript = "one\n\n  \ntwo\nthree\n"
    report = await audit_transcript(transcript, mock_client(), mock_ledger())
    assert report.transcript_turns == 3
    assert report.transcript_sha256 == hashlib.sha256(
        transcript.encode("utf-8")
    ).hexdigest()


async def test_digest_changes_with_one_byte() -> None:
    first = await audit_transcript(TRANSCRIPT, mock_client(), mock_ledger())
    second = await audit_transcript(
        TRANSCRIPT + " ", mock_client(), mock_ledger()
    )
    assert first.transcript_sha256 != second.transcript_sha256
    assert first.transcript_turns == second.transcript_turns
