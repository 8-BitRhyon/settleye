"""Tests for the Stripe test-mode ledger adapter.

Stripe speaks form-encoded REST with Bearer test keys. All HTTP is
replayed through httpx.MockTransport with Stripe-shaped payloads: no
network, no keys, no real money, deterministic.
"""

import httpx

from app.ledger.stripe import StripeAdapter

CHARGE_SEARCH_HIT = {
    "data": [{"id": "ch_test_992", "amount": 4500, "metadata": {"order_id": "992"}}]
}
CHARGE_SEARCH_MISS = {"data": []}
REFUNDS_SETTLED = {
    "data": [{"id": "re_test_1", "amount": 4500, "charge": "ch_test_992"}]
}
REFUNDS_EMPTY = {"data": []}


def make_adapter(
    search: dict, refunds: dict, seen: list[httpx.Request]
) -> StripeAdapter:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        path = request.url.path
        if path == "/v1/charges/search":
            return httpx.Response(200, json=search)
        if path == "/v1/refunds" and request.method == "GET":
            return httpx.Response(200, json=refunds)
        if path == "/v1/refunds" and request.method == "POST":
            return httpx.Response(
                200, json={"id": "re_test_new", "amount": 4500}
            )
        raise AssertionError(f"unexpected {request.method} {path}")

    return StripeAdapter(
        api_key="sk_test_fake", transport=httpx.MockTransport(handler)
    )


def test_settled_refund_reads_dollars() -> None:
    seen: list[httpx.Request] = []
    adapter = make_adapter(CHARGE_SEARCH_HIT, REFUNDS_SETTLED, seen)
    assert adapter.refunded_usd("992") == 45.00


def test_phantom_refund_reads_zero() -> None:
    seen: list[httpx.Request] = []
    adapter = make_adapter(CHARGE_SEARCH_HIT, REFUNDS_EMPTY, seen)
    assert adapter.refunded_usd("992") == 0.0


def test_unknown_order_is_none_not_zero() -> None:
    seen: list[httpx.Request] = []
    adapter = make_adapter(CHARGE_SEARCH_MISS, REFUNDS_EMPTY, seen)
    assert adapter.refunded_usd("0000") is None


def test_create_sends_form_body_and_idempotency_key() -> None:
    seen: list[httpx.Request] = []
    adapter = make_adapter(CHARGE_SEARCH_HIT, REFUNDS_EMPTY, seen)
    receipt = adapter.record_refund(order_id="992", amount_usd=45.00)
    posts = [r for r in seen if r.method == "POST"]
    assert len(posts) == 1
    body = posts[0].content.decode()
    assert "charge=ch_test_992" in body
    assert "amount=4500" in body
    assert posts[0].headers.get("Idempotency-Key", "").startswith("refund:992:")
    assert receipt["refunded_usd"] == 45.00


def test_auth_uses_bearer_test_key() -> None:
    seen: list[httpx.Request] = []
    adapter = make_adapter(CHARGE_SEARCH_HIT, REFUNDS_SETTLED, seen)
    adapter.refunded_usd("992")
    assert seen[0].headers["Authorization"] == "Bearer sk_test_fake"
