"""One-click remediation: execute the corrective payload exactly once.

Stripe and Shopify are separate refund rails that can double-refund the
same order. Every remediation carries an idempotency key derived from the
promise itself; a retried key returns the original receipt and never
touches the ledger again.
"""

from app.ledger.base import LedgerAdapter
from app.models import ReconciliationResult, RemediationReceipt
from app.value import Recovery, ValueLedger


class RemediationError(Exception):
    """The requested fix is not a drift or cannot be executed safely."""


def idempotency_key(promise_action: str, order_id: str | None, amount_usd: float) -> str:
    return f"{promise_action}:{order_id or 'unknown'}:{amount_usd:.2f}"


class RemediationService:
    """Executes drift fixes with in-memory idempotency tracking."""

    def __init__(self) -> None:
        self._executed: dict[str, RemediationReceipt] = {}

    def find(self, key: str) -> RemediationReceipt | None:
        """Return the original receipt for a seen key, if any."""
        receipt = self._executed.get(key)
        if receipt is None:
            return None
        return receipt.model_copy(update={"status": "already_executed"})

    def remediate(
        self,
        result: ReconciliationResult,
        ledger: LedgerAdapter,
        value: ValueLedger,
    ) -> RemediationReceipt:
        if result.verdict != "drift":
            raise RemediationError(
                f"Nothing to remediate: verdict is {result.verdict}."
            )
        promise = result.promise
        key = idempotency_key(
            promise.action, promise.order_id, result.amount_at_risk_usd
        )
        if key in self._executed:
            found = self.find(key)
            assert found is not None
            return found
        ledger.record_refund(
            order_id=promise.order_id or "unknown",
            amount_usd=result.amount_at_risk_usd,
        )
        value.recoveries.append(
            Recovery(
                id=key,
                amount_usd=result.amount_at_risk_usd,
                kind="refund_recovered",
            )
        )
        receipt = RemediationReceipt(
            idempotency_key=key,
            promise=promise,
            amount_usd=result.amount_at_risk_usd,
            status="executed",
        )
        self._executed[key] = receipt
        return receipt
