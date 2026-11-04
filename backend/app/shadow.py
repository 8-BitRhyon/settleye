"""Shadow audit: measure Settleye on a transcript folder, merchant numbers.

The API serves one transcript; the daemon sweeps a batch; this harness answers
the buyer's first question. On my tickets, how many promises drift, how many
dollars sit at risk per thousand tickets, and how often does Settleye clear a
ticket that actually held a binding promise?

Definitions, stated once:

- tickets: every transcript attempted for the report, including failed audits.
  A file that cannot be read or audited is a case error; `errors` counts those
  failures, and `successful_tickets = tickets - errors`. The per-1,000
  denominator uses attempted tickets, so a crash can never shrink it and
  inflate the money-per-ticket rate.
- drifts: reconciliation results whose verdict is `drift`.
- drift_dollars_per_1000_tickets: total_at_risk / tickets * 1000.
- binding_cases: labeled cases with at least one `binding` promise.
- false_clears: of those, cases whose report holds no `binding` promise.
  Presence based: one binding promise anywhere in the report clears the case.
  An errored binding case counts as a false clear: no promise was found, and a
  merchant cannot be told that ticket was covered.
- false_clear_rate: false_clears / binding_cases; null without labels, and
  null when there are no labeled binding cases to divide by.

The ledger is read only and remediation is never called, so a shadow run on a
merchant export cannot move money.

Replay mode (`--replay`) measures recorded live output instead of calling the
model: every recorded filename gets one fixed JSON reply, and the real
extraction and reconciliation code paths run unchanged. Replay needs no key,
builds no model client, and makes no network call. A replay proves the
pipeline and the metrics; it does not prove a fresh model run. The report
records the replay path so the two can never be confused.
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.audit import audit_transcript
from app.daemon import build_ledger
from app.extract.client import BASE_URL_DEFAULT, MetaModelClient, model_id
from app.extract.live_check import load_dotenv_file, load_transcript
from app.ledger.base import LedgerAdapter
from app.models import AuditReport

DEFAULT_OUT = (
    Path(__file__).resolve().parents[1] / ".tmp" / "shadow_report.json"
)

LabelCase = dict[str, Any]
Case = dict[str, Any]


def expected_binding_count(label: LabelCase | None) -> int:
    """Labeled promises that ended binding: the ones the ledger join must see."""
    if not label:
        return 0
    return sum(
        1
        for promise in label.get("promises", [])
        if promise.get("terminal_status") == "binding"
    )


def found_binding_count(report: AuditReport) -> int:
    """Extracted promises the model marked binding."""
    return sum(
        1 for promise in report.promises if promise.terminal_status == "binding"
    )


def case_from_report(
    source: str, report: AuditReport, label: LabelCase | None
) -> Case:
    """One audited transcript scored against its label, when it has one."""
    expected = expected_binding_count(label)
    found = found_binding_count(report)
    false_clear: bool | None = None
    if label is not None:
        false_clear = expected > 0 and found == 0
    return {
        "source": source,
        "verdict": report.verdict,
        "drifts": len(report.drifts),
        "total_at_risk_usd": round(report.total_at_risk_usd, 2),
        "expected_binding": expected,
        "found_binding": found,
        "false_clear": false_clear,
        "error": None,
    }


def case_from_error(
    source: str, error: str, label: LabelCase | None
) -> Case:
    """One isolated failure: no ticket, no drift, still scored for silence.

    A labeled binding case that errored found no binding promise, so it is a
    false clear. The error is recorded next to it, never swallowed.
    """
    expected = expected_binding_count(label)
    false_clear: bool | None = None
    if label is not None:
        false_clear = expected > 0
    return {
        "source": source,
        "verdict": "error",
        "drifts": 0,
        "total_at_risk_usd": 0.0,
        "expected_binding": expected,
        "found_binding": 0,
        "false_clear": false_clear,
        "error": error,
    }


def summarize_cases(cases: list[Case], labels_present: bool) -> dict:
    """Fold per-case outcomes into the merchant-facing numbers.

    The ticket denominator is every attempted transcript, not only the ones
    that succeeded: a failed audit still consumed a ticket, and quietly
    shrinking the denominator would inflate the money-per-1,000 rate.
    """
    tickets = len(cases)
    successful = sum(1 for case in cases if case["error"] is None)
    errors = tickets - successful
    drifts = sum(case["drifts"] for case in cases)
    total = round(sum(case["total_at_risk_usd"] for case in cases), 2)
    binding_cases = sum(
        1 for case in cases if case["expected_binding"] > 0
    )
    false_clears = sum(1 for case in cases if case["false_clear"] is True)
    per_1000 = round(total / tickets * 1000, 2) if tickets else 0.0
    rate: float | None = None
    if labels_present and binding_cases:
        rate = round(false_clears / binding_cases, 4)
    return {
        "tickets": tickets,
        "successful_tickets": successful,
        "errors": errors,
        "drifts": drifts,
        "total_at_risk_usd": total,
        "drift_dollars_per_1000_tickets": per_1000,
        "binding_cases": binding_cases,
        "false_clears": false_clears,
        "false_clear_rate": rate,
        "cases": cases,
    }


def load_labels(path: str | Path) -> dict[str, LabelCase]:
    """Manifest keyed by transcript filename, as `fixtures/eval_expected.json`."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def select_paths(directory: str | Path, limit: int | None) -> list[Path]:
    """Sorted transcript files, capped by `limit` before any model call."""
    paths = sorted(Path(directory).glob("*.json"))
    if limit is not None:
        paths = paths[: max(limit, 0)]
    return paths


def write_report(payload: dict, out: str | Path) -> Path:
    """Write the JSON report, creating the parent folder when missing."""
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


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


def load_replay(path: str | Path) -> tuple[dict[str, str], str]:
    """Recorded live output as (filename -> JSON reply, model label).

    Shape matches `fixtures/eval_live_output.json`:
    `{filename: {"entities": [...], "model": ..., "elapsed_s": ...}}`.
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


async def run_shadow(
    directory: str | Path,
    client: MetaModelClient | None,
    ledger: LedgerAdapter,
    labels: dict[str, LabelCase] | None = None,
    limit: int | None = None,
    out: str | Path | None = None,
    model: str = "",
    ledger_kind: str = "mock",
    replay: dict[str, str] | None = None,
    replay_source: str | None = None,
) -> dict:
    """Audit each transcript in `directory`, one failure at a time.

    Any exception from loading or auditing a file is isolated to that case:
    a bad transcript must not stop a merchant pilot. With `replay`, each file
    gets its recorded reply and `client` is unused. The report is written
    when `out` is set, and always returned.
    """
    folder = Path(directory)
    cases: list[Case] = []
    for path in select_paths(folder, limit):
        label = labels.get(path.name) if labels is not None else None
        try:
            transcript = load_transcript(str(path))
            case_client = client
            if replay is not None:
                reply = replay.get(path.name)
                if reply is None:
                    raise LookupError(
                        f"no recorded output for {path.name} in replay file"
                    )
                case_client = ReplayClient(reply, source=path.name)
            report = await audit_transcript(transcript, case_client, ledger)
        except Exception as exc:  # one bad case, never the whole sweep
            cases.append(
                case_from_error(
                    path.name, f"{type(exc).__name__}: {exc}", label
                )
            )
            continue
        cases.append(case_from_report(path.name, report, label))
    payload = summarize_cases(cases, labels_present=labels is not None)
    payload.update(
        {
            "directory": str(folder),
            "ledger": ledger_kind,
            "model": model,
            "limit": limit,
            "labels": labels is not None,
            "replay": replay_source,
            "generated_at": datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z"),
        }
    )
    if out is not None:
        write_report(payload, out)
    return payload


def format_shadow(report: dict) -> str:
    """Camera- and merchant-readable summary: money and misses first."""
    rate = report["false_clear_rate"]
    rate_text = f"{rate:.1%}" if rate is not None else "n/a"
    mode = "replay" if report.get("replay") else "live"
    lines = [f"mode: {mode}"]
    if report.get("replay"):
        lines.append(f"replay: {report['replay']}")
    lines += [
        f"model: {report.get('model') or 'unknown'}",
        f"ledger: {report.get('ledger', '?')}",
        f"tickets: {report['tickets']} attempted "
        f"({report['successful_tickets']} audited, "
        f"{report['errors']} errors)",
        f"drifts: {report['drifts']}",
        f"total_at_risk: ${report['total_at_risk_usd']:.2f}",
        "drift_dollars_per_1000_tickets: "
        f"${report['drift_dollars_per_1000_tickets']:.2f}",
        "false_clear_rate: "
        f"{rate_text} ({report['false_clears']}/{report['binding_cases']})",
        "note: tickets counts attempted transcripts; "
        "errors counts failed audits",
    ]
    for case in report["cases"]:
        if case["false_clear"]:
            lines.append(
                f"! false clear: {case['source']} "
                f"(expected {case['expected_binding']} binding)"
            )
        if case["error"]:
            lines.append(f"! {case['source']}: ERROR {case['error'][:120]}")
    return "\n".join(lines)


async def _run(args: argparse.Namespace) -> int:
    replay: dict[str, str] | None = None
    recorded_model = ""
    if args.replay:
        try:
            replay, recorded_model = load_replay(args.replay)
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
    directory = Path(args.dir)
    if not directory.is_dir():
        print(f"Not a directory: {directory}", file=sys.stderr)
        return 2
    if not select_paths(directory, None):
        print(f"No transcript JSON files in {directory}.", file=sys.stderr)
        return 2
    if args.limit is not None and args.limit < 1:
        print("--limit must be at least 1.", file=sys.stderr)
        return 2
    try:
        labels = load_labels(args.labels) if args.labels else None
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read labels {args.labels}: {exc}", file=sys.stderr)
        return 2
    model = args.model or recorded_model or model_id()
    client: MetaModelClient | None = None
    if replay is None:
        client = MetaModelClient(
            api_key=api_key, base_url=args.base_url, model=model
        )
        if not await client.health_check():
            print(
                f"Model endpoint unreachable at {args.base_url}. "
                "Check the key, the URL, and cold-start waiting.",
                file=sys.stderr,
            )
            return 3
    ledger = build_ledger(args.ledger)
    started = time.monotonic()
    report = await run_shadow(
        directory,
        client,
        ledger,
        labels=labels,
        limit=args.limit,
        out=args.out,
        model=model,
        ledger_kind=args.ledger,
        replay=replay,
        replay_source=args.replay,
    )
    elapsed = time.monotonic() - started
    print(format_shadow(report))
    print(f"report: {Path(args.out).resolve()}")
    print(f"elapsed: {elapsed:.2f}s")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Shadow-audit a transcript folder and report merchant-facing "
            "metrics. Read-only: never remediates."
        )
    )
    parser.add_argument("--dir", required=True, help="Transcript JSON folder.")
    parser.add_argument("--ledger", default="mock", choices=["mock", "shopify"])
    parser.add_argument(
        "--labels",
        default=None,
        help="Expected manifest, e.g. ../fixtures/eval_expected.json.",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Maximum files to audit."
    )
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument(
        "--replay",
        default=None,
        help=(
            "Recorded live output JSON (fixtures/eval_live_output.json "
            "shape). No key, no client, no network."
        ),
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
