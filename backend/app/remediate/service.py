"""One-click remediation: execute the corrective payload exactly once.

Stripe and Shopify are separate refund rails that can double-refund the
same order. Every remediation carries an idempotency key derived from the
promise identity (action, order, rail, promised amount), never from the
residual shortfall: a partial refund changes the shortfall, and the key must
not change with it.

Receipts are appended to a JSONL store and fsynced before the call returns.
A restart reloads the store, so a remembered promise returns the original
receipt and never touches the ledger again. A corrupt store fails closed:
refusing to remediate is always cheaper than a second refund.
"""

import json
import logging
import os
import threading
from pathlib import Path

from app.ledger.base import LedgerAdapter
from app.models import PromiseEntity, ReconciliationResult, RemediationReceipt
from app.signing import ReceiptContext, ReceiptSigner
from app.value import Recovery, ValueLedger

RECEIPTS_PATH_ENV = "SETTLEYE_RECEIPTS_PATH"
_DEFAULT_RECEIPTS_PATH = (
    Path(__file__).resolve().parents[2] / ".tmp" / "receipts.jsonl"
)

_LOGGER = logging.getLogger(__name__)


class RemediationError(Exception):
    """The requested fix is not a drift or cannot be executed safely."""


def _bare_order_id(order_id: str | None) -> str:
    """Ledger key without the spoken hash or surrounding space."""
    return (order_id or "").strip().lstrip("#") or "unknown"


def idempotency_key(
    promise_action: str,
    order_id: str | None,
    amount_usd: float,
    target_system: str = "unknown",
) -> str:
    """Stable key: action, order, refund rail, and promised amount.

    The order id is normalized exactly like the ledger boundary, so `#992`
    and `992` can never mint two keys for the same promised refund.
    """
    return (
        f"{promise_action}:{_bare_order_id(order_id)}:"
        f"{target_system}:{amount_usd:.2f}"
    )


def promise_key(promise: PromiseEntity, fallback_amount_usd: float) -> str:
    """Key a promise by identity, never by the residual shortfall.

    The promised amount is the anchor: it is what the customer was told and
    it does not move when a partial refund settles. Fall back to the live
    at-risk amount only when the transcript never stated a number.
    """
    amount_usd = (
        promise.amount if promise.amount is not None else fallback_amount_usd
    )
    return idempotency_key(
        promise.action, promise.order_id, amount_usd, promise.target_system
    )


def default_receipts_path() -> Path:
    """Env override for deploys, else a gitignored repo-local store."""
    return Path(os.environ.get(RECEIPTS_PATH_ENV) or _DEFAULT_RECEIPTS_PATH)


class RemediationService:
    """Executes drift fixes; idempotency receipts survive process restarts."""

    def __init__(
        self,
        receipts_path: str | Path | None = None,
        signer: ReceiptSigner | None = None,
    ) -> None:
        self._path = (
            Path(receipts_path)
            if receipts_path is not None
            else default_receipts_path()
        )
        self._signer = signer
        self._executed: dict[str, RemediationReceipt] = {}
        # FastAPI runs sync endpoints in a thread pool. The check, ledger
        # write, and append must be one critical section, or two identical
        # clicks can both pass `find` and refund twice.
        # Reentrant: the route holds it across find, reconcile and remediate.
        self._lock = threading.RLock()
        self._load()

    @property
    def lock(self) -> threading.RLock:
        return self._lock

    @property
    def receipts_path(self) -> Path:
        return self._path

    def _load(self) -> None:
        """Replay the append-only store. Corrupt state fails closed."""
        if not self._path.exists():
            return
        try:
            text = self._path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RemediationError(
                f"Receipt store {self._path} is unreadable: {exc}. "
                "Refusing to remediate."
            ) from exc
        for number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                receipt = RemediationReceipt.model_validate(json.loads(line))
            except ValueError as exc:
                raise RemediationError(
                    f"Receipt store {self._path} line {number} is corrupt: "
                    f"{exc}. Refusing to remediate."
                ) from exc
            # First line wins: it records the money that actually moved.
            self._executed.setdefault(receipt.idempotency_key, receipt)

    def _append(self, receipt: RemediationReceipt) -> None:
        """Append one receipt and fsync it before the caller returns."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(receipt.model_dump_json() + "\n")
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise RemediationError(
                f"Could not persist receipt {receipt.idempotency_key} to "
                f"{self._path}: {exc}. The ledger may have moved; "
                "reconcile by hand before retrying."
            ) from exc
        self._executed[receipt.idempotency_key] = receipt

    def find(self, key: str) -> RemediationReceipt | None:
        """Return the original receipt for a seen key, if any.

        Stores written before order normalization may hold `#992`. Check the
        normalized key first, then the one legacy hash-prefixed variant, so an
        upgrade cannot forget a refund that already moved money.
        """
        candidates = [key]
        parts = key.split(":")
        if len(parts) == 4 and not parts[1].startswith("#"):
            candidates.append(f"{parts[0]}:#{parts[1]}:{parts[2]}:{parts[3]}")
            # Pre-rail key shape from the first signed sample and early
            # stores: refund:992:45.00.
            candidates.append(f"{parts[0]}:{parts[1]}:{parts[3]}")
        if len(parts) == 3 and not parts[1].startswith("#"):
            candidates.append(f"{parts[0]}:#{parts[1]}:{parts[2]}")
        for candidate in candidates:
            receipt = self._executed.get(candidate)
            if receipt is not None:
                return receipt.model_copy(update={"status": "already_executed"})
        return None

    def remediate(
        self,
        result: ReconciliationResult,
        ledger: LedgerAdapter,
        value: ValueLedger,
        context: ReceiptContext | None = None,
    ) -> RemediationReceipt:
        if result.verdict != "drift":
            raise RemediationError(
                f"Nothing to remediate: verdict is {result.verdict}."
            )
        promise = result.promise
        key = promise_key(promise, result.amount_at_risk_usd)
        with self._lock:
            found = self.find(key)
            if found is not None:
                return found
            # Reconcile strips the spoken "#" before reading the ledger;
            # writes must cross the same boundary with the same bare key.
            ledger_order_id = _bare_order_id(promise.order_id)
            # A hard ceiling on the original charge stops a forged promise
            # from refunding past the money that was actually captured.
            charge_limit = getattr(ledger, "charge_amount_usd", None)
            if callable(charge_limit):
                charge_amount = charge_limit(ledger_order_id)
                settled = ledger.refunded_usd(ledger_order_id) or 0.0
                if (
                    charge_amount is not None
                    and settled + result.amount_at_risk_usd
                    > charge_amount + 0.005
                ):
                    raise RemediationError(
                        f"Refund would exceed the original charge: "
                        f"${settled:.2f} settled + "
                        f"${result.amount_at_risk_usd:.2f} requested of "
                        f"${charge_amount:.2f}."
                    )
            ledger.record_refund(
                order_id=ledger_order_id,
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
            # Sign only after the money moved and only for a new key. A
            # signing failure is logged, not raised: refusing the receipt now
            # would hide a refund that already happened and invite a second
            # one.
            if self._signer is not None and context is not None:
                try:
                    envelope = self._signer.sign(
                        promise,
                        result.amount_at_risk_usd,
                        "executed",
                        context,
                    )
                except Exception as exc:  # noqa: BLE001 - money already moved
                    envelope = None
                    _LOGGER.warning(
                        "Receipt signing failed for %s: %s", key, exc
                    )
                if envelope is not None:
                    receipt = receipt.model_copy(update={"receipt": envelope})
            self._append(receipt)
            return receipt
