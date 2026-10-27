"""Promise-vs-ledger diff: the core verdict engine.

Only refunds are reconcilable today. Any other action, missing order, or
unknown ledger row reports `unverifiable`: the engine never fabricates a
verdict it cannot prove from ledger state.
"""

from app.commitment import is_binding
from app.ledger.base import LedgerAdapter
from app.models import PromiseEntity, ReconciliationResult

_HALF_CENT_USD = 0.005


def reconcile(promise: PromiseEntity, ledger: LedgerAdapter) -> ReconciliationResult:
    """Diff one extracted promise against settled ledger state."""
    if not is_binding(promise):
        return ReconciliationResult(
            promise=promise,
            verdict="not_binding",
            ledger_summary=(
                f"Commitment ended as {promise.terminal_status}; "
                "nothing is owed unless stated again."
            ),
        )
    # Models quote order numbers as spoken ("#992"); ledgers key them bare.
    # Normalize once here so every adapter sees the same identifier.
    order_id = (promise.order_id or "").strip().lstrip("#")
    if promise.action != "refund" or promise.amount is None or not order_id:
        return ReconciliationResult(
            promise=promise,
            verdict="unverifiable",
            ledger_summary="Only refunds with an amount and order can be reconciled.",
        )
    settled = ledger.refunded_usd(order_id)
    if settled is None:
        return ReconciliationResult(
            promise=promise,
            verdict="unverifiable",
            ledger_summary=f"Order {promise.order_id} is unknown to the ledger.",
        )
    shortfall = round(promise.amount - settled, 2)
    if abs(shortfall) < _HALF_CENT_USD:
        return ReconciliationResult(
            promise=promise,
            verdict="verified",
            ledger_summary=(
                f"Order {promise.order_id}: ${settled:.2f} settled of "
                f"${promise.amount:.2f} promised."
            ),
            amount_at_risk_usd=0.0,
        )
    return ReconciliationResult(
        promise=promise,
        verdict="drift",
        ledger_summary=(
            f"Order {promise.order_id}: ${settled:.2f} settled of "
            f"${promise.amount:.2f} promised."
        ),
        amount_at_risk_usd=max(shortfall, 0.0),
    )
