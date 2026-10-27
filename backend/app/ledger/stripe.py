"""Stripe test-mode ledger adapter.

Money movement truth comes from the refunds list per charge; orders map
to charges through the `order_id` metadata stamp our own checkout writes.
Test keys (`sk_test_`) never touch card networks. Amounts cross the wire
in integer minor units (cents) and convert to dollars at the boundary.
"""

from typing import Any

import httpx


class StripeError(Exception):
    """Stripe answered with an error or an unparsable payload."""


class StripeAdapter:
    """LedgerAdapter over Stripe test-mode REST."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.stripe.com",
        transport: httpx.BaseTransport | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        if not api_key.startswith("sk_test_"):
            raise ValueError("Refusing non-test Stripe key. Live keys never enter this path.")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            transport=transport,
            timeout=httpx.Timeout(timeout_seconds),
        )

    def _headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        response = self._client.get(
            f"{self._base_url}{path}", headers=self._headers(), params=params
        )
        return self._checked(response)

    def _post(self, path: str, data: dict[str, str], idempotency_key: str) -> dict[str, Any]:
        response = self._client.post(
            f"{self._base_url}{path}",
            headers=self._headers(idempotency_key),
            data=data,
        )
        return self._checked(response)

    @staticmethod
    def _checked(response: httpx.Response) -> dict[str, Any]:
        try:
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            raise StripeError(f"Stripe call failed: {exc}") from exc
        if not isinstance(payload, dict):
            raise StripeError("Stripe answered with a non-object payload.")
        return payload

    def find_charge_id(self, order_id: str) -> str | None:
        """Charge stamped with our order id, or None when unknown."""
        payload = self._get(
            "/v1/charges/search", {"query": f"metadata['order_id']:'{order_id}'"}
        )
        rows = payload.get("data", [])
        if not rows or not isinstance(rows[0], dict):
            return None
        charge_id = rows[0].get("id")
        return str(charge_id) if charge_id else None

    def refunded_usd(self, order_id: str) -> float | None:
        """Settled refund dollars, 0.0 when the charge exists but is unrefunded,
        None when no charge maps to the order."""
        charge_id = self.find_charge_id(order_id)
        if charge_id is None:
            return None
        payload = self._get("/v1/refunds", {"charge": charge_id, "limit": "100"})
        total_cents = 0
        for refund in payload.get("data", []):
            if isinstance(refund, dict) and isinstance(refund.get("amount"), int):
                total_cents += refund["amount"]
        return round(total_cents / 100.0, 2)

    def record_refund(self, order_id: str, amount_usd: float) -> dict[str, Any]:
        """Execute a test-mode refund. The idempotency key makes retries safe."""
        charge_id = self.find_charge_id(order_id)
        if charge_id is None:
            raise KeyError(f"unknown order: {order_id}")
        cents = int(round(amount_usd * 100))
        key = f"refund:{order_id}:{amount_usd:.2f}"
        payload = self._post(
            "/v1/refunds",
            {"charge": charge_id, "amount": str(cents)},
            idempotency_key=key,
        )
        created_cents = payload.get("amount", 0)
        created = created_cents / 100.0 if isinstance(created_cents, int) else 0.0
        return {
            "id": payload.get("id"),
            "order_id": order_id,
            "refunded_usd": round(created, 2),
            "idempotency_key": key,
        }
