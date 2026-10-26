"""In-memory ledger for offline development, CI, and the demo fallback."""

from typing import Any


class MockLedgerAdapter:
    """Ledger state backed by a plain dict shaped like the mock fixture."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._charges: dict[str, dict[str, Any]] = {
            str(charge["order_id"]): dict(charge)
            for charge in data.get("charges", [])
        }

    def refunded_usd(self, order_id: str) -> float | None:
        charge = self._charges.get(order_id)
        if charge is None:
            return None
        return float(charge.get("refunded_usd", 0.0))

    def record_refund(self, order_id: str, amount_usd: float) -> dict[str, Any]:
        charge = self._charges.get(order_id)
        if charge is None:
            raise KeyError(f"unknown order: {order_id}")
        charge["refunded_usd"] = round(float(charge.get("refunded_usd", 0.0)) + amount_usd, 2)
        return {"order_id": order_id, "refunded_usd": charge["refunded_usd"]}
