"""Shopify dev-store ledger adapter.

Read path is order refunds via the GraphQL Admin API. Write path is
refundCreate guarded by the @idempotent directive (required since 2026-04)
plus userErrors inspection: a rejected mutation raises, never pretends.
The exact mutation shape gets live verification against a dev store once
its custom-app token lands; until then the wire format is pinned by tests.
"""

from typing import Any

import httpx

API_VERSION = "2026-10"


class ShopifyError(Exception):
    """Shopify answered with errors, userErrors, or an unparsable payload."""


class ShopifyAdapter:
    """LedgerAdapter over the Shopify GraphQL Admin API."""

    def __init__(
        self,
        store_domain: str,
        access_token: str,
        transport: httpx.BaseTransport | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._url = (
            f"https://{store_domain}/admin/api/{API_VERSION}/graphql.json"
        )
        self._token = access_token
        self._client = httpx.Client(
            transport=transport,
            timeout=httpx.Timeout(timeout_seconds),
        )

    def _call(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        response = self._client.post(
            self._url,
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self._token,
            },
            json={"query": query, "variables": variables},
        )
        try:
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            raise ShopifyError(f"Shopify call failed: {exc}") from exc
        if not isinstance(payload, dict) or payload.get("errors"):
            raise ShopifyError(f"Shopify GraphQL errors: {payload.get('errors')}")
        return payload.get("data", {})

    def refunded_usd(self, order_id: str) -> float | None:
        """Settled refund dollars, 0.0 when the order exists but is unrefunded,
        None when no order matches."""
        name = order_id if order_id.startswith("#") else f"#{order_id}"
        data = self._call(
            """
            query OrderRefunds($name: String!) {
              orders(first: 1, query: $name) {
                edges {
                  node {
                    id
                    refunds {
                      id
                      totalRefundedSet {
                        shopMoney { amount }
                      }
                    }
                  }
                }
              }
            }
            """,
            {"name": f"name:{name}"},
        )
        edges = data.get("orders", {}).get("edges", [])
        if not edges:
            return None
        total = 0.0
        for refund in edges[0].get("node", {}).get("refunds", []):
            try:
                total += float(
                    refund["totalRefundedSet"]["shopMoney"]["amount"]
                )
            except (KeyError, TypeError, ValueError):
                continue
        return round(total, 2)

    def record_refund(self, order_id: str, amount_usd: float) -> dict[str, Any]:
        """Execute a dev-store refund. Idempotent by directive key."""
        name = order_id if order_id.startswith("#") else f"#{order_id}"
        key = f"refund:{order_id.lstrip('#')}:{amount_usd:.2f}"
        data = self._call(
            """
            mutation RefundCreate($input: RefundInput!, $key: String!) @idempotent(key: $key) {
              refundCreate(input: $input) {
                refund { id }
                userErrors { field message }
              }
            }
            """,
            {
                "input": {"orderName": name, "notify": False},
                "key": key,
            },
        )
        node = data.get("refundCreate", {})
        errors = node.get("userErrors", [])
        if errors:
            raise ShopifyError(f"refundCreate rejected: {errors}")
        refund = node.get("refund") or {}
        if not refund.get("id"):
            raise ShopifyError("refundCreate returned no refund id.")
        return {
            "id": refund["id"],
            "order_id": order_id,
            "refunded_usd": round(amount_usd, 2),
            "idempotency_key": key,
        }
