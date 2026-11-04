"""Tests for the shadow audit harness: merchant numbers, isolated failures.

Three layers, deliberately separate:

- Pure metric math over canned `AuditReport`s: a labeled binding case that was
  found, one that was missed, a labeled non-binding case that must never enter
  the false-clear denominator, and an error that must still count as an
  attempted ticket.
- Runner behavior with `audit_transcript` monkeypatched: the JSON report is
  written, one bad transcript becomes a case error instead of a crash, and
  `--limit` caps the files before any model call.
- Replay through the real CLI on the 12-case eval with recorded live output:
  no API key, no model client, no network.

No live model calls in any test.
"""

import asyncio
import json
from pathlib import Path

from app import shadow
from app.models import AuditReport, PromiseEntity, ReconciliationResult

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
EVAL_DIR = FIXTURES / "eval"
EVAL_EXPECTED = FIXTURES / "eval_expected.json"
EVAL_LIVE_OUTPUT = FIXTURES / "eval_live_output.json"


def make_promise(status: str = "binding", amount: float = 45.0):
    return PromiseEntity(
        action="refund",
        amount=amount,
        order_id="992",
        target_system="stripe",
        asserted_state="refund processed",
        confidence=0.9,
        terminal_status=status,
    )


def audit_report(
    statuses: tuple[str, ...] = (), amounts: tuple[float, ...] = ()
) -> AuditReport:
    """Canned report: promises by terminal status, drifts by amount."""
    promises = [make_promise(status) for status in statuses]
    drifts = [
        ReconciliationResult(
            promise=promises[index],
            verdict="drift",
            ledger_summary="canned",
            amount_at_risk_usd=amount,
        )
        for index, amount in enumerate(amounts)
    ]
    total = round(sum(amounts), 2)
    return AuditReport(
        promises=promises,
        results=drifts,
        drifts=drifts,
        total_at_risk_usd=total,
        verdict="drift_found" if drifts else "verified_green",
    )


def label(*statuses: str) -> dict:
    return {"promises": [{"terminal_status": s} for s in statuses]}


def test_metric_math_counts_attempted_tickets_including_errors() -> None:
    labels = {
        "found.json": label("binding"),
        "missed.json": label("binding"),
        "retracted.json": label("retracted"),
    }
    cases = [
        shadow.case_from_report(
            "found.json", audit_report(("binding",), (45.0,)), labels["found.json"]
        ),
        shadow.case_from_report("missed.json", audit_report(), labels["missed.json"]),
        shadow.case_from_report(
            "retracted.json",
            audit_report(("retracted",)),
            labels["retracted.json"],
        ),
        shadow.case_from_error("broken.json", "OSError: unreadable", None),
    ]
    metrics = shadow.summarize_cases(cases, labels_present=True)
    assert metrics["tickets"] == 4
    assert metrics["successful_tickets"] == 3
    assert metrics["errors"] == 1
    assert metrics["drifts"] == 1
    assert metrics["total_at_risk_usd"] == 45.0
    # 45 dollars over all 4 attempted tickets, not just the 3 that audited.
    assert metrics["drift_dollars_per_1000_tickets"] == 11250.0
    assert metrics["binding_cases"] == 2
    assert metrics["false_clears"] == 1
    assert metrics["false_clear_rate"] == 0.5
    assert [case["false_clear"] for case in cases] == [False, True, False, None]
    assert [case["expected_binding"] for case in cases] == [1, 1, 0, 0]
    assert [case["found_binding"] for case in cases] == [1, 0, 0, 0]


def test_non_binding_case_never_enters_false_clear_denominator() -> None:
    cases = [
        shadow.case_from_report(
            "retracted.json", audit_report(), label("retracted")
        )
    ]
    metrics = shadow.summarize_cases(cases, labels_present=True)
    assert metrics["binding_cases"] == 0
    assert metrics["false_clears"] == 0
    assert metrics["false_clear_rate"] is None
    assert cases[0]["false_clear"] is False


def test_without_labels_rate_is_null_but_dollars_still_count() -> None:
    cases = [
        shadow.case_from_report(
            "phantom.json", audit_report(("binding",), (45.0,)), None
        )
    ]
    metrics = shadow.summarize_cases(cases, labels_present=False)
    assert metrics["tickets"] == 1
    assert metrics["drift_dollars_per_1000_tickets"] == 45000.0
    assert metrics["binding_cases"] == 0
    assert metrics["false_clears"] == 0
    assert metrics["false_clear_rate"] is None
    assert cases[0]["false_clear"] is None


def test_error_adds_to_attempted_tickets_and_still_scored_for_silence() -> None:
    cases = [
        shadow.case_from_report(
            "ok.json", audit_report(("binding",), (45.0,)), label("binding")
        ),
        shadow.case_from_error(
            "bad.json", "ExtractionError: no JSON", label("binding")
        ),
    ]
    metrics = shadow.summarize_cases(cases, labels_present=True)
    assert metrics["tickets"] == 2
    assert metrics["successful_tickets"] == 1
    assert metrics["errors"] == 1
    assert metrics["drifts"] == 1
    assert metrics["total_at_risk_usd"] == 45.0
    assert metrics["drift_dollars_per_1000_tickets"] == 22500.0
    assert metrics["binding_cases"] == 2
    assert metrics["false_clears"] == 1
    assert metrics["false_clear_rate"] == 0.5
    assert cases[1]["verdict"] == "error"
    assert cases[1]["false_clear"] is True


def test_default_out_is_repo_relative_backend_tmp() -> None:
    backend = Path(__file__).resolve().parents[1]
    assert shadow.DEFAULT_OUT == backend / ".tmp" / "shadow_report.json"


def write_transcript(folder: Path, name: str, text: str) -> Path:
    path = folder / name
    path.write_text(
        json.dumps({"turns": [{"role": "customer", "text": text}]}),
        encoding="utf-8",
    )
    return path


def test_runner_writes_report_and_continues_after_errors(
    tmp_path: Path, monkeypatch
) -> None:
    folder = tmp_path / "transcripts"
    folder.mkdir()
    write_transcript(folder, "a.json", "order #992 refund please")
    write_transcript(folder, "b.json", "BOOM this one explodes")
    write_transcript(folder, "c.json", "order #992 refund again")
    (folder / "d_broken.json").write_text("[]", encoding="utf-8")

    async def fake_audit(transcript: str, client, ledger) -> AuditReport:
        if "BOOM" in transcript:
            raise RuntimeError("model exploded")
        return audit_report(("binding",), (45.0,))

    monkeypatch.setattr(shadow, "audit_transcript", fake_audit)
    out = tmp_path / "reports" / "shadow.json"
    labels = {"b.json": label("binding")}
    report = asyncio.run(
        shadow.run_shadow(folder, None, None, labels=labels, out=out)
    )

    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload == report
    assert payload["tickets"] == 4
    assert payload["successful_tickets"] == 2
    assert payload["errors"] == 2
    assert payload["drifts"] == 2
    assert payload["total_at_risk_usd"] == 90.0
    assert payload["drift_dollars_per_1000_tickets"] == 22500.0
    assert payload["binding_cases"] == 1
    assert payload["false_clears"] == 1
    assert payload["false_clear_rate"] == 1.0
    failed = {
        case["source"]: case["error"]
        for case in payload["cases"]
        if case["error"]
    }
    assert set(failed) == {"b.json", "d_broken.json"}
    assert "RuntimeError" in failed["b.json"]
    assert "AttributeError" in failed["d_broken.json"]


def test_runner_respects_limit_before_any_call(
    tmp_path: Path, monkeypatch
) -> None:
    folder = tmp_path / "transcripts"
    folder.mkdir()
    write_transcript(folder, "a.json", "first ticket")
    write_transcript(folder, "b.json", "second ticket")
    write_transcript(folder, "c.json", "third ticket")
    seen: list[str] = []

    async def fake_audit(transcript: str, client, ledger) -> AuditReport:
        seen.append(transcript)
        return audit_report()

    monkeypatch.setattr(shadow, "audit_transcript", fake_audit)
    out = tmp_path / "shadow.json"
    report = asyncio.run(
        shadow.run_shadow(folder, None, None, limit=1, out=out)
    )

    assert len(seen) == 1
    assert "first ticket" in seen[0]
    assert report["limit"] == 1
    assert report["tickets"] == 1
    assert [case["source"] for case in report["cases"]] == ["a.json"]
    assert json.loads(out.read_text(encoding="utf-8"))["tickets"] == 1


def test_select_paths_is_sorted_and_capped(tmp_path: Path) -> None:
    folder = tmp_path / "transcripts"
    folder.mkdir()
    for name in ("c.json", "a.json", "b.json", "notes.txt"):
        (folder / name).write_text("{}", encoding="utf-8")
    assert [p.name for p in shadow.select_paths(folder, None)] == [
        "a.json",
        "b.json",
        "c.json",
    ]
    assert [p.name for p in shadow.select_paths(folder, 2)] == [
        "a.json",
        "b.json",
    ]


def test_replay_missing_filename_is_a_case_error(tmp_path: Path) -> None:
    folder = tmp_path / "transcripts"
    folder.mkdir()
    write_transcript(folder, "a.json", "a ticket")
    report = asyncio.run(
        shadow.run_shadow(folder, None, None, replay={"other.json": "[]"})
    )
    assert report["tickets"] == 1
    assert report["successful_tickets"] == 0
    assert report["errors"] == 1
    assert report["cases"][0]["error"] is not None
    assert "no recorded output" in report["cases"][0]["error"]
    assert report["drift_dollars_per_1000_tickets"] == 0.0


def test_replay_mode_audits_twelve_eval_cases_without_api_key(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv("BASETEN_API_KEY", raising=False)
    monkeypatch.setattr(shadow, "load_dotenv_file", lambda *args, **kwargs: None)

    def no_live_client(*args, **kwargs):
        raise AssertionError("replay mode must not construct MetaModelClient")

    monkeypatch.setattr(shadow, "MetaModelClient", no_live_client)
    out = tmp_path / "shadow_replay.json"
    code = shadow.main(
        [
            "--dir",
            str(EVAL_DIR),
            "--ledger",
            "mock",
            "--labels",
            str(EVAL_EXPECTED),
            "--replay",
            str(EVAL_LIVE_OUTPUT),
            "--out",
            str(out),
        ]
    )
    assert code == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["replay"] == str(EVAL_LIVE_OUTPUT)
    assert payload["tickets"] == 12
    assert payload["successful_tickets"] == 12
    assert payload["errors"] == 0
    assert len(payload["cases"]) == 12
    assert {case["error"] for case in payload["cases"]} == {None}
    assert payload["drifts"] == 5
    assert payload["total_at_risk_usd"] == 285.5
    assert payload["drift_dollars_per_1000_tickets"] == 23791.67
    assert payload["binding_cases"] == 8
    assert payload["false_clears"] == 0
    assert payload["false_clear_rate"] == 0.0
