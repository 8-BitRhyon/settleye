"""Tests for the Shopify dev-store ledger adapter.

Shopify speaks GraphQL with a custom-app access token. All HTTP is
replayed through httpx.MockTransport with Shopify-shaped payloads: no
network, no token, deterministic. The refundCreate wire shape gets live
verification against a dev store once its token lands.
"""

import httpx

from app.ledger.shopify import ShopifyAdapter, ShopifyError

ORDER_WITH_REFUNDS = {
    "data": {
        "orders": {
            "edges": [
                {
                    "node": {
                        "id": "gid://shopify/Order/1",
                        "name": "#992",
                        "refunds": [
                            {
                                "id": "gid://shopify/Refund/1",
                                "totalRefundedSet": {
                                    "shopMoney": {"amount": "20.00"}
                                },
                            },
                            {
                                "id": "gid://shopify/Refund/2",
                                "totalRefundedSet": {
                                    "shopMoney": {"amount": "25.00"}
                                },
                            },
                        ],
                    }
                }
            ]
        }
    }
}

ORDER_CLEAN = {
    "data": {
        "orders": {
            "edges": [
                {
                    "node": {
                        "id": "gid://shopify/Order/2",
                        "name": "#1042",
                        "refunds": [],
                        "transactions": [
                            {
                                "id": "gid://shopify/OrderTransaction/20",
                                "gateway": "manual",
                                "kind": "SALE",
                                "status": "SUCCESS",
                            }
                        ],
                    }
                }
            ]
        }
    }
}

ORDER_MISS = {"data": {"orders": {"edges": []}}}

REFUND_CREATED = {
    "data": {
        "refundCreate": {
            "refund": {"id": "gid://shopify/Refund/9"},
            "userErrors": [],
        }
    }
}

REFUND_REJECTED = {
    "data": {
        "refundCreate": {
            "refund": None,
            "userErrors": [{"field": ["input"], "message": "Order is archived"}],
        }
    }
}


def make_adapter(
    order_payload: dict, seen: list[httpx.Request], mutate: dict | None = None
) -> ShopifyAdapter:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        body = request.content.decode()
        if "refundCreate" in body:
            return httpx.Response(200, json=mutate or REFUND_CREATED)
        return httpx.Response(200, json=order_payload)

    return ShopifyAdapter(
        store_domain="demo.myshopify.com",
        access_token="shp_fake",
        transport=httpx.MockTransport(handler),
    )


def test_settled_refunds_sum() -> None:
    seen: list[httpx.Request] = []
    adapter = make_adapter(ORDER_WITH_REFUNDS, seen)
    assert adapter.refunded_usd("992") == 45.00


def test_clean_order_reads_zero() -> None:
    seen: list[httpx.Request] = []
    adapter = make_adapter(ORDER_CLEAN, seen)
    assert adapter.refunded_usd("1042") == 0.0


def test_unknown_order_is_none() -> None:
    seen: list[httpx.Request] = []
    adapter = make_adapter(ORDER_MISS, seen)
    assert adapter.refunded_usd("0000") is None


def test_auth_uses_admin_token_header() -> None:
    seen: list[httpx.Request] = []
    adapter = make_adapter(ORDER_CLEAN, seen)
    adapter.refunded_usd("1042")
    assert seen[0].headers["X-Shopify-Access-Token"] == "shp_fake"
    assert "992" in seen[0].content.decode() or "1042" in seen[0].content.decode()


def test_create_carries_idempotency_and_returns_id() -> None:
    seen: list[httpx.Request] = []
    adapter = make_adapter(ORDER_CLEAN, seen)
    receipt = adapter.record_refund(order_id="992", amount_usd=45.00)
    body = seen[-1].content.decode()
    assert "@idempotent" in body
    assert "refundCreate(input: $input) @idempotent" in body
    assert "gid://shopify/Order/2" in body
    assert "gid://shopify/OrderTransaction/20" in body
    assert receipt["refunded_usd"] == 45.00
    assert "Refund/9" in receipt["id"]


def test_create_raises_on_unknown_order() -> None:
    seen: list[httpx.Request] = []
    adapter = make_adapter(ORDER_MISS, seen)
    try:
        adapter.record_refund(order_id="0000", amount_usd=5.00)
    except ShopifyError as exc:
        assert "No order matches" in str(exc)
    else:
        raise AssertionError("expected ShopifyError")


def test_user_errors_raise() -> None:
    seen: list[httpx.Request] = []
    adapter = make_adapter(ORDER_CLEAN, seen, mutate=REFUND_REJECTED)
    try:
        adapter.record_refund(order_id="992", amount_usd=45.00)
    except ShopifyError as exc:
        assert "archived" in str(exc)
    else:
        raise AssertionError("expected ShopifyError")


def test_graphql_errors_raise() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"errors": [{"message": "boom"}]})

    adapter = ShopifyAdapter(
        store_domain="demo.myshopify.com",
        access_token="shp_fake",
        transport=httpx.MockTransport(handler),
    )
    try:
        adapter.refunded_usd("992")
    except ShopifyError:
        return
    raise AssertionError("expected ShopifyError")
