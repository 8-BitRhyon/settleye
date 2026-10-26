"""Ledger abstraction: one interface, every money rail behind it.

Stripe test mode, Shopify dev stores, and the mock fixture all implement
this protocol. The diff engine never touches a provider SDK directly, so a
new rail is a new adapter, never engine surgery.
"""

from typing import Any, Protocol


class LedgerAdapter(Protocol):
    """Read (and test-only write) access to refund settlement state."""

    def refunded_usd(self, order_id: str) -> float | None:
        """Dollars settled as refunds for the order, or None if unknown."""
        ...

    def record_refund(self, order_id: str, amount_usd: float) -> dict[str, Any]:
        """Stage a refund write (mock) or execute one (live adapters)."""
        ...
