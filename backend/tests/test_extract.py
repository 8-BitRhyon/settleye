"""Tests for the Meta-model promise extraction pipeline.

All model I/O goes through httpx.MockTransport: no network, no credits,
deterministic. The wire-level tests also pin the canonical model ID so the
nonexistent `-1026` suffixed ID can never ship again.
"""

import json

import httpx
import pytest

from app.extract.client import MODEL_ID, MetaModelClient
from app.extract.pipeline import ExtractionError, extract_promises
from app.models import PromiseEntity

CANONICAL_MODEL_ID = "meta-models/muse-spark-open-1026"

PHANTOM_JSON = json.dumps([
    {
        "action": "refund",
        "amount": 45.00,
        "order_id": "992",
        "target_system": "stripe",
        "asserted_state": "full refund processed",
        "confidence": 0.9,
        "evidence_span": "I have processed a full $45 refund for order #992.",
    }
])


def make_client(replies: list[str], seen: list[dict]) -> MetaModelClient:
    """Client whose transport replays canned replies and records payloads."""

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content.decode()))
        body = {
            "choices": [{"message": {"content": replies.pop(0)}}],
            "model": CANONICAL_MODEL_ID,
        }
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    return MetaModelClient(api_key="test-key", transport=transport)


def test_model_id_is_canonical() -> None:
    assert MODEL_ID == CANONICAL_MODEL_ID
    assert MODEL_ID == "meta-models/muse-spark-open-1026"


async def test_wire_sends_canonical_model_id() -> None:
    seen: list[dict] = []
    client = make_client(["[]"], seen)
    await client.chat([{"role": "user", "content": "hi"}])
    assert seen[0]["model"] == CANONICAL_MODEL_ID


async def test_happy_transcript_extracts_nothing() -> None:
    seen: list[dict] = []
    client = make_client(["[]"], seen)
    result = await extract_promises("Order shipped, thanks, bye.", client)
    assert result == []
    assert len(seen) == 1


async def test_phantom_refund_extracts_promise() -> None:
    seen: list[dict] = []
    client = make_client([PHANTOM_JSON], seen)
    result = await extract_promises(
        "I have processed a full $45 refund for order #992.", client
    )
    assert len(result) == 1
    promise = result[0]
    assert isinstance(promise, PromiseEntity)
    assert promise.action == "refund"
    assert promise.amount == 45.00
    assert promise.order_id == "992"


async def test_code_fences_are_stripped() -> None:
    seen: list[dict] = []
    client = make_client(["```json\n" + PHANTOM_JSON + "\n```"], seen)
    result = await extract_promises("refund $45 order #992, done.", client)
    assert len(result) == 1
    assert result[0].order_id == "992"


async def test_garbage_then_repaired() -> None:
    seen: list[dict] = []
    client = make_client(["not json at all {{{", PHANTOM_JSON], seen)
    result = await extract_promises("refund $45 order #992, done.", client)
    assert len(result) == 1
    assert len(seen) == 2


async def test_unrepairable_raises_after_bounded_retries() -> None:
    seen: list[dict] = []
    client = make_client(["garbage"] * 5, seen)
    with pytest.raises(ExtractionError):
        await extract_promises("refund $45 order #992, done.", client)
    # 1 initial attempt plus exactly MAX_REPAIRS repairs, never unbounded.
    assert len(seen) == 3


async def test_health_check_true_on_200() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": []})

    client = MetaModelClient(api_key="k", transport=httpx.MockTransport(handler))
    assert await client.health_check() is True


async def test_health_check_false_on_transport_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    client = MetaModelClient(api_key="k", transport=httpx.MockTransport(handler))
    assert await client.health_check() is False
