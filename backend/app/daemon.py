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
from typing import Any

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


class ReplayClient:
    """Offline stand-in for MetaModelClient: one recorded reply, no network.

    The reply came from a prior live run, so the extraction pipeline still
    parses and validates real model output; only the transport is removed.
    Keyed by transcript filename at the call site, so no prompt sniffing and
    no ambiguity about which recording belongs to which file.
    """

    def __init__(self, reply: str, source: str = "") -> None:
        self.reply = reply
        self.source = source
        self.calls = 0

    async def chat(
        self, messages: list[dict[str, str]], temperature: float = 0.2
    ) -> str:
        self.calls += 1
        return self.reply


class BatchReplayClient:
    """Offline stand-in for MetaModelClient across a batch of transcripts.

    Maps transcript filenames to recorded replies.
    """

    def __init__(self, replies: dict[str, str]) -> None:
        self.replies = dict(replies)

    def for_source(self, source: str) -> ReplayClient:
        reply = self.replies.get(source)
        if reply is None:
            raise ExtractionError(
                f"no recorded output for {source} in replay file"
            )
        return ReplayClient(reply, source=source)

    async def chat(
        self, messages: list[dict[str, str]], temperature: float = 0.2
    ) -> str:
        if len(self.replies) == 1:
            return next(iter(self.replies.values()))
        raise RuntimeError(
            "BatchReplayClient requires for_source(source) when multiple replies are loaded"
        )


def load_replay(path: str | Path) -> tuple[dict[str, str], str]:
    """Recorded live output as (filename -> JSON reply, model label).

    Shape matches fixtures/eval_live_output.json:
    {filename: {"entities": [...], "model": ..., "elapsed_s": ...}}.
    """
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("replay file must be a JSON object keyed by filename")
    replies: dict[str, str] = {}
    models: set[str] = set()
    for source, entry in payload.items():
        if not isinstance(entry, dict) or not isinstance(
            entry.get("entities"), list
        ):
            raise ValueError(f"replay entry {source!r} needs an entities list")
        replies[source] = json.dumps(entry["entities"])
        if entry.get("model"):
            models.add(str(entry["model"]))
    model = models.pop() if len(models) == 1 else "replay"
    return replies, model


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
    client: Any,
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
            case_client = (
                client.for_source(source)
                if hasattr(client, "for_source")
                else client
            )
            report = await audit_transcript(
                transcripts[source], case_client, ledger
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
    replay: dict[str, str] | None = None
    if getattr(args, "replay", None):
        try:
            replay, _ = load_replay(args.replay)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"Cannot read replay {args.replay}: {exc}", file=sys.stderr)
            return 2

    api_key = None
    if replay is None:
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

    if not args.dir:
        default_dir = Path(__file__).resolve().parents[2] / "fixtures" / "eval"
        if default_dir.is_dir():
            directory = default_dir
        else:
            print(
                "Error: --dir is required. Specify path to transcript JSON folder.",
                file=sys.stderr,
            )
            return 2
    else:
        directory = Path(args.dir)

    if not directory.is_dir():
        print(f"Not a directory: {directory}", file=sys.stderr)
        return 2
    paths = sorted(directory.glob("*.json"))
    if not paths:
        print(f"No transcript JSON files in {directory}.", file=sys.stderr)
        return 2
    transcripts = {path.name: load_transcript(str(path)) for path in paths}

    if replay is not None:
        client = BatchReplayClient(replay)
    else:
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
    parser.add_argument(
        "--dir",
        default=None,
        help="Transcript JSON folder (defaults to fixtures/eval if present).",
    )
    parser.add_argument("--ledger", default="mock", choices=["mock", "shopify"])
    parser.add_argument(
        "--auto-remediate",
        action="store_true",
        help="Settle drift unattended (mock ledger only).",
    )
    parser.add_argument(
        "--replay",
        default=None,
        help="Path to pre-recorded model output JSON for offline replay.",
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
