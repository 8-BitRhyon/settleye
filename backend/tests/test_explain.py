"""Tests for per-drift plain-English explanations.

Explanations fire only for drifts, on demand, through POST /explain. The
model gets the promise, the ledger summary, and the amount; nothing else.
Display-only text is still untrusted: empty replies raise, overlong replies
are capped, and the prompt forbids inventing facts beyond its inputs.
"""

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.explain import ExplainError, explain_drift
from app.extract.client import MetaModelClient
from app.models import PromiseEntity
from app.remediate.service import RemediationService
from app.value import ValueLedger

from tests.test_remediate import drift_result, mock_ledger


def text_client(reply: str) -> MetaModelClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": reply}}], "model": "test"},
        )

    return MetaModelClient(api_key="k", transport=httpx.MockTransport(handler))


def promise() -> PromiseEntity:
    return drift_result().promise


async def test_explain_returns_plain_text() -> None:
    text = await explain_drift(
        promise(),
        "Order 992: $0.00 settled of $45.00 promised.",
        45.00,
        text_client("The agent said the $45 refund was done, but the ledger shows $0 settled, so $45 is still owed."),
    )
    assert "45" in text
    assert len(text) <= 500


async def test_explain_empty_reply_raises() -> None:
    with pytest.raises(ExplainError):
        await explain_drift(
            promise(), "Order 992: $0.00 settled.", 45.00, text_client("   ")
        )


async def test_explain_caps_overlong_reply() -> None:
    text = await explain_drift(
        promise(), "Order 992: $0.00 settled.", 45.00, text_client("x" * 2000)
    )
    assert len(text) <= 500


def test_explain_prompt_forbids_new_facts() -> None:
    from app.explain import EXPLAIN_SYSTEM_PROMPT

    lowered = EXPLAIN_SYSTEM_PROMPT.lower()
    assert "only" in lowered and "fact" in lowered


def fresh_app_state() -> TestClient:
    main_module.app.state.ledger = mock_ledger()
    main_module.app.state.remediation = RemediationService()
    main_module.app.state.value = ValueLedger()
    return TestClient(main_module.app)


def test_explain_route_round_trip(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module,
        "build_client",
        lambda: text_client("The $45 refund was promised but never settled."),
    )
    client = fresh_app_state()
    response = client.post(
        "/explain",
        json={
            "promise": promise().model_dump(),
            "ledger_summary": "Order 992: $0.00 settled of $45.00 promised.",
            "amount_usd": 45.00,
        },
    )
    assert response.status_code == 200
    assert "45" in response.json()["explanation"]


def test_explain_route_rejects_empty(monkeypatch) -> None:
    monkeypatch.setattr(
        main_module, "build_client", lambda: text_client("  ")
    )
    client = fresh_app_state()
    response = client.post(
        "/explain",
        json={
            "promise": promise().model_dump(),
            "ledger_summary": "Order 992: $0.00 settled.",
            "amount_usd": 45.00,
        },
    )
    assert response.status_code == 422
