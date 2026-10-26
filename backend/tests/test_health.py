"""Smoke test: the API boots and answers health checks."""

from fastapi.testclient import TestClient

from app.main import app


def test_healthz_ok() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_promise_entity_schema() -> None:
    from app.models import PromiseEntity

    entity = PromiseEntity(
        action="refund",
        amount=45.00,
        order_id="992",
        target_system="stripe",
        asserted_state="full refund processed",
        confidence=0.9,
        evidence_span="I have processed a full $45 refund for order #992.",
    )
    assert entity.action == "refund"
    assert entity.amount == 45.00
