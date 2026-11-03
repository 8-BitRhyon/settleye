"""Tests for the Jev gate.

The gate is a discriminator: it answers whether a promise exists and what its
end state is. It never moves money. These tests pin the wire shape, the
parsing, the failure modes, and the one behaviour that saves money: skipping
the generative extraction call when Jev sees no promise.
"""

import asyncio
import json

import httpx

from app.gate.jev import (
    SKIP_THRESHOLD,
    GateDecision,
    JevClient,
    JevError,
    gate_transcript,
    read_decision,
)


def jev_reply(has_promise: float, modality: str = "binding", conf: float = 0.9) -> dict:
    return {
        "model": "jev-1.13.0",
        "answers": {
            "has_promise": {"type": "noul", "noul": has_promise},
            "modality": {
                "type": "choice",
                "choice": modality,
                "confidence": conf,
                "probabilities": {modality: conf},
            },
        },
        "usage": {"input_tokens": 120, "output_tokens": 8},
    }


def client_returning(payload: dict, seen: list[httpx.Request] | None = None) -> JevClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request)
        return httpx.Response(200, json=payload)

    return JevClient(api_key="jev_test", transport=httpx.MockTransport(handler))


def test_gate_reads_probabilities() -> None:
    decision = asyncio.run(
        gate_transcript(client_returning(jev_reply(0.91, "binding", 0.88)), "t")
    )
    assert decision.has_promise == 0.91
    assert decision.modality == "binding"
    assert decision.modality_confidence == 0.88
    assert decision.skip_extraction is False


def test_low_probability_skips_extraction() -> None:
    decision = asyncio.run(
        gate_transcript(client_returning(jev_reply(0.04, "info_only", 0.7)), "t")
    )
    assert decision.skip_extraction is True
    assert decision.has_promise < SKIP_THRESHOLD


def test_request_carries_state_model_and_both_questions() -> None:
    seen: list[httpx.Request] = []
    asyncio.run(gate_transcript(client_returning(jev_reply(0.5), seen), "hello world"))
    body = json.loads(seen[0].content)
    assert body["state"] == "hello world"
    assert body["model"] == "jev-latest"
    assert set(body["questions"]) == {"has_promise", "modality"}
    assert body["questions"]["has_promise"]["type"] == "noul"
    assert body["questions"]["modality"]["type"] == "choice"
    assert seen[0].headers["Authorization"] == "Bearer jev_test"


def test_http_error_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "bad key"})

    client = JevClient(api_key="nope", transport=httpx.MockTransport(handler))
    try:
        asyncio.run(gate_transcript(client, "t"))
    except JevError as exc:
        assert "401" in str(exc) or "bad key" in str(exc)
    else:
        raise AssertionError("expected JevError")


def test_malformed_answer_raises() -> None:
    try:
        read_decision({"has_promise": {"noul": "not a number"}})
    except JevError:
        return
    raise AssertionError("expected JevError")


def test_unknown_modality_raises() -> None:
    try:
        read_decision(
            {
                "has_promise": {"noul": 0.9},
                "modality": {"choice": "refund_promise", "confidence": 0.9},
            }
        )
    except JevError:
        return
    raise AssertionError("expected JevError")


def test_probability_out_of_range_raises() -> None:
    try:
        read_decision(
            {
                "has_promise": {"noul": 1.7},
                "modality": {"choice": "binding", "confidence": 0.9},
            }
        )
    except JevError:
        return
    raise AssertionError("expected JevError")


def test_skip_flag_boundary() -> None:
    assert GateDecision(0.19, "binding", 0.5).skip_extraction is True
    assert GateDecision(0.21, "binding", 0.5).skip_extraction is False
