"""Daemon loop: batch audit over many transcripts, Modal-ready.

The API serves the human inbox; this module is the autonomous half. A cron
(or a Modal scheduled function, once credits land) calls run_batch with the
day's transcripts: each is extracted, reconciled, and folded into one
money-sorted exception report. The default pass is audit-only, so a
scheduled run can never move money. Pass auto_remediate=True only for
offline/demo ledgers where settling drift unattended is intended.

Modal shape when credits land (no code change here, just a wrapper):

    import modal
    app = modal.App("settleye")
    @app.function(schedule=modal.Cron("0 * * * *"))
    def sweep():
        asyncio.run(run_batch(load_transcripts(), build_client(), ...))

This module imports no FastAPI state, so the wrapper stays trivial.
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

from app.audit import audit_transcript
from app.extract.client import (
    BASE_URL_DEFAULT,
    MetaModelClient,
    model_id,
)
from app.extract.live_check import load_dotenv_file, load_transcript
from app.extract.pipeline import ExtractionError
from app.ledger.base import LedgerAdapter
from app.ledger.mock import MockLedgerAdapter
from app.models import BatchItemReport, BatchReport, RepeatOrder
from app.remediate.service import RemediationError, RemediationService
from app.value import ValueLedger


def find_repeat_orders(
    items: list[BatchItemReport], drifts: list
) -> list[RepeatOrder]:
    """Group drift by normalized order across sources. Two-plus wins.

    Pure code over reconciled results, zero model calls: the daemon's
    memory of which orders keep getting promised refunds.
    """
    by_order: dict[str, dict] = {}
    for item in items:
        if item.report is None:
            continue
        for drift in item.report.drifts:
            key = (drift.promise.order_id or "").strip().lstrip("#")
            if not key:
                continue
            bucket = by_order.setdefault(key, {"sources": [], "total": 0.0})
            bucket["sources"].append(item.source)
            bucket["total"] += drift.amount_at_risk_usd
    repeats = []
    for order_id in sorted(by_order):
        bucket = by_order[order_id]
        sources = sorted(set(bucket["sources"]))
        if len(sources) >= 2:
            repeats.append(
                RepeatOrder(
                    order_id=order_id,
                    sources=sources,
                    occurrences=len(sources),
                    total_at_risk_usd=round(bucket["total"], 2),
                )
            )
    return repeats


async def run_batch(
    transcripts: dict[str, str],
    client: MetaModelClient,
    ledger: LedgerAdapter,
    remediation: RemediationService,
    value: ValueLedger,
    auto_remediate: bool = False,
) -> BatchReport:
    """Audit every transcript, isolate failures, sort drift money-first."""
    items: list[BatchItemReport] = []
    drifts = []
    remediated = 0
    remediation_errors: list[str] = []
    for source in sorted(transcripts):
        try:
            report = await audit_transcript(
                transcripts[source], client, ledger
            )
        except ExtractionError as exc:
            items.append(BatchItemReport(source=source, error=str(exc)))
            continue
        items.append(BatchItemReport(source=source, report=report))
        drifts.extend(report.drifts)
        if auto_remediate:
            for drift in report.drifts:
                try:
                    remediation.remediate(drift, ledger, value)
                    remediated += 1
                except RemediationError as exc:
                    remediation_errors.append(f"{source}: {exc}")
    drifts.sort(key=lambda d: d.amount_at_risk_usd, reverse=True)
    total = round(sum(d.amount_at_risk_usd for d in drifts), 2)
    repeat_orders = find_repeat_orders(items, drifts)
    has_hard_error = bool(items) and all(
        item.error and item.report is None for item in items
    )
    if drifts:
        verdict = "drift_found"
    elif has_hard_error:
        verdict = "batch_error"
    else:
        verdict = "verified_green"
    return BatchReport(
        items=items,
        drifts=drifts,
        repeat_orders=repeat_orders,
        total_at_risk_usd=total,
        remediated=remediated,
        remediation_errors=remediation_errors,
        verdict=verdict,
    )


def format_batch(report: BatchReport, elapsed_seconds: float) -> str:
    """Camera-readable sweep summary: money first, errors clearly marked."""
    lines = [
        f"sources: {len(report.items)}",
        f"elapsed: {elapsed_seconds:.2f}s",
        f"verdict: {report.verdict}",
        f"total_at_risk: ${report.total_at_risk_usd:.2f}",
        f"remediated: {report.remediated}",
    ]
    for drift in report.drifts:
        promise = drift.promise
        lines.append(
            f"- ${drift.amount_at_risk_usd:.2f} {promise.action} "
            f"order #{promise.order_id or '?'} [{promise.target_system}]"
        )
    for repeat in report.repeat_orders:
        lines.append(
            f"! repeat: order #{repeat.order_id} promised in "
            f"{repeat.occurrences} transcripts "
            f"(${repeat.total_at_risk_usd:.2f} at risk)"
        )
    for item in report.items:
        if item.error:
            lines.append(f"! {item.source}: ERROR {item.error[:120]}")
    for err in report.remediation_errors:
        lines.append(f"! remediate: {err[:120]}")
    return "\n".join(lines)


def build_ledger(kind: str) -> LedgerAdapter:
    """Offline mock by default; live Shopify only when explicitly asked."""
    if kind == "shopify":
        from app.ledger.shopify import ShopifyAdapter

        store = os.environ.get("SHOPIFY_STORE_DOMAIN", "")
        token = os.environ.get("SHOPIFY_ADMIN_TOKEN", "")
        if not store or not token:
            raise SystemExit(
                "SHOPIFY_STORE_DOMAIN and SHOPIFY_ADMIN_TOKEN are required "
                "for --ledger shopify. No call was made."
            )
        return ShopifyAdapter(store_domain=store, access_token=token)
    fixture = (
        Path(__file__).resolve().parents[2] / "fixtures" / "mock_ledger.json"
    )
    return MockLedgerAdapter(json.loads(fixture.read_text()))


async def _run(args: argparse.Namespace) -> int:
    api_key = args.api_key or os.environ.get("BASETEN_API_KEY")
    if not api_key:
        print(
            "BASETEN_API_KEY is not set. Export it or pass --api-key. "
            "No call was made.",
            file=sys.stderr,
        )
        return 2
    if args.auto_remediate and args.ledger != "mock":
        print(
            "Refusing: --auto-remediate runs only against --ledger mock. "
            "Live money moves through the human inbox, never the daemon.",
            file=sys.stderr,
        )
        return 2
    directory = Path(args.dir)
    paths = sorted(directory.glob("*.json"))
    if not paths:
        print(f"No transcript JSON files in {directory}.", file=sys.stderr)
        return 2
    transcripts = {path.name: load_transcript(str(path)) for path in paths}
    client = MetaModelClient(
        api_key=api_key, base_url=args.base_url, model=args.model or model_id()
    )
    if not await client.health_check():
        print(
            f"Model endpoint unreachable at {args.base_url}.",
            file=sys.stderr,
        )
        return 3
    ledger = build_ledger(args.ledger)
    started = time.monotonic()
    report = await run_batch(
        transcripts,
        client,
        ledger,
        RemediationService(),
        ValueLedger(),
        auto_remediate=args.auto_remediate,
    )
    print(format_batch(report, time.monotonic() - started))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Batch-audit transcripts and report money-sorted drift."
    )
    parser.add_argument("--dir", required=True, help="Transcript JSON folder.")
    parser.add_argument("--ledger", default="mock", choices=["mock", "shopify"])
    parser.add_argument(
        "--auto-remediate",
        action="store_true",
        help="Settle drift unattended (mock ledger only).",
    )
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--base-url", default=BASE_URL_DEFAULT)
    parser.add_argument("--model", default=None)
    parser.add_argument("--env-file", default=None)
    args = parser.parse_args(argv)
    load_dotenv_file(args.env_file)
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
