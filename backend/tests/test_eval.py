"""Deterministic eval: commitment gating and reconcile wiring per case.

Each eval transcript carries a marker (EVAL01..EVAL12). The routing mock
replies with the manifest's expected entities, so these tests prove the
downstream contract: given these entities, the verdict and totals must be
exactly X. Retracted, conditional, superseded, and info_only commitments
must never reach the ledger join; only binding refunds with an order and
an amount reconcile.

Live-model accuracy (did the model actually extract these entities?) is
measured separately by sweeping fixtures/eval/ with the daemon against the
mock ledger; numbers land in docs/research/12-eval-results.md.
"""

import asyncio
import json
from pathlib import Path

import httpx

from app.audit import audit_transcript
from app.extract.client import MetaModelClient
from app.ledger.mock import MockLedgerAdapter

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
EVAL_DIR = FIXTURES / "eval"
EXPECTED = json.loads((FIXTURES / "eval_expected.json").read_text())


def canned_reply(filename: str) -> str:
    """Manifest entities reshaped as a model reply, with canned metadata."""
    items = []
    for promise in EXPECTED[filename]["promises"]:
        items.append(
            {
                "action": promise["action"],
                "amount": promise["amount"],
                "order_id": promise["order_id"],
                "target_system": "stripe",
                "asserted_state": "canned",
                "confidence": 0.9,
                "evidence_span": "canned",
                "terminal_status": promise["terminal_status"],
            }
        )
    return json.dumps(items)


def routing_client(filenames: list[str]) -> MetaModelClient:
    markers = {name: f"EVAL{i + 1:02d}" for i, name in enumerate(filenames)}
    replies = {name: canned_reply(name) for name in filenames}

    def handler(request: httpx.Request) -> httpx.Response:
        body = request.content.decode()
        for name, reply in replies.items():
            if markers[name] in body:
                return httpx.Response(
                    200,
                    json={
                        "choices": [{"message": {"content": reply}}],
                        "model": "test",
                    },
                )
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "[]"}}], "model": "test"},
        )

    return MetaModelClient(api_key="k", transport=httpx.MockTransport(handler))


def mock_ledger() -> MockLedgerAdapter:
    data = json.loads((FIXTURES / "mock_ledger.json").read_text())
    return MockLedgerAdapter(data)


def load_text(path: Path) -> str:
    payload = json.loads(path.read_text())
    return "\n".join(
        f"{turn.get('role', '?')}: {turn.get('text', '')}"
        for turn in payload.get("turns", [])
    )


def test_eval_manifest_covers_every_transcript() -> None:
    files = sorted(path.name for path in EVAL_DIR.glob("*.json"))
    assert files, "eval directory must not be empty"
    assert set(files) == set(EXPECTED), (
        f"manifest drift: files={files} expected={sorted(EXPECTED)}"
    )
    assert len(files) == 12


def test_eval_gating_contract_per_case() -> None:
    files = sorted(path.name for path in EVAL_DIR.glob("*.json"))
    client = routing_client(files)
    for name in files:
        want = EXPECTED[name]
        report = asyncio.run(
            audit_transcript(load_text(EVAL_DIR / name), client, mock_ledger())
        )
        got_entities = [
            (
                p.action,
                p.order_id,
                p.amount,
                p.terminal_status,
            )
            for p in report.promises
        ]
        want_entities = [
            (
                p["action"],
                p["order_id"],
                p["amount"],
                p["terminal_status"],
            )
            for p in want["promises"]
        ]
        assert got_entities == want_entities, f"{name}: entities"
        assert report.verdict == want["verdict"], f"{name}: verdict"
        assert report.total_at_risk_usd == want["total_at_risk_usd"], (
            f"{name}: total"
        )


def test_non_binding_never_drifts() -> None:
    files = sorted(path.name for path in EVAL_DIR.glob("*.json"))
    client = routing_client(files)
    for name in files:
        report = asyncio.run(
            audit_transcript(load_text(EVAL_DIR / name), client, mock_ledger())
        )
        for result in report.results:
            if result.promise.terminal_status != "binding":
                assert result.verdict == "not_binding", name
