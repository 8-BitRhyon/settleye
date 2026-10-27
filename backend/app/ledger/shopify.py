"""Shopify dev-store ledger adapter.

Read path is order refunds via the GraphQL Admin API. Write path is
refundCreate with the @idempotent directive on the field plus userErrors
inspection: a rejected mutation raises, never pretends. Wire shape is
live-verified against the dev store (order GID plus SALE-parented
transaction, manual gateway, field-level directive).
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
        """Execute a dev-store refund. Idempotent by field-level directive key.

        Live-verified shape: RefundInput takes the order GID plus one
        transaction (parent SALE id, order GID, formatted amount, REFUND
        kind, sale gateway). The @idempotent directive sits on the
        refundCreate field, not the mutation operation.
        """
        name = order_id if order_id.startswith("#") else f"#{order_id}"
        key = f"refund:{order_id.lstrip('#')}:{amount_usd:.2f}"
        lookup = self._call(
            """
            query OrderForRefund($name: String!) {
              orders(first: 1, query: $name) {
                edges {
                  node {
                    id
                    transactions(first: 10) {
                      id
                      gateway
                      kind
                      status
                    }
                  }
                }
              }
            }
            """,
            {"name": f"name:{name}"},
        )
        edges = lookup.get("orders", {}).get("edges", [])
        if not edges:
            raise ShopifyError(f"No order matches {name}.")
        node = edges[0].get("node", {})
        order_gid = node.get("id")
        sale = next(
            (
                t
                for t in node.get("transactions", [])
                if t.get("kind") == "SALE" and t.get("id")
            ),
            None,
        )
        if not order_gid or not sale:
            raise ShopifyError(
                f"Order {name} has no refundable SALE transaction."
            )
        data = self._call(
            """
            mutation RefundCreate($input: RefundInput!, $key: String!) {
              refundCreate(input: $input) @idempotent(key: $key) {
                refund { id }
                userErrors { field message }
              }
            }
            """,
            {
                "input": {
                    "orderId": order_gid,
                    "notify": False,
                    "note": f"Settleye refund {name} ${amount_usd:.2f}",
                    "transactions": [
                        {
                            "parentId": sale["id"],
                            "orderId": order_gid,
                            "amount": f"{amount_usd:.2f}",
                            "kind": "REFUND",
                            "gateway": sale.get("gateway") or "manual",
                        }
                    ],
                },
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
