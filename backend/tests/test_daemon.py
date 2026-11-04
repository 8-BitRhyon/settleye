"""Tests for the daemon loop: batch audit over many transcripts.

The daemon is the agentic half of Settleye. It sweeps a batch of support
transcripts on a schedule, reconciles each against the ledger, and reports
money-sorted drift. Money never moves unless auto_remediate is explicit:
the default pass is audit-only, so a cron run can never refund by accident.
"""

import asyncio
import json
from pathlib import Path

import httpx

from app.daemon import (
    BatchReplayClient,
    ReplayClient,
    load_replay,
    main,
    run_batch,
)
from app.extract.client import MetaModelClient
from app.extract.live_check import load_transcript
from app.extract.pipeline import ExtractionError
from app.ledger.mock import MockLedgerAdapter
from app.remediate.service import RemediationService
from app.value import ValueLedger

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"

PHANTOM_45 = json.dumps([
    {
        "action": "refund",
        "amount": 45.00,
        "order_id": "992",
        "target_system": "stripe",
        "asserted_state": "full refund processed",
        "confidence": 0.9,
        "evidence_span": "I have processed a full $45 refund for order #992.",
    }
])

PHANTOM_120 = json.dumps([
    {
        "action": "refund",
        "amount": 120.00,
        "order_id": "1042",
        "target_system": "stripe",
        "asserted_state": "full refund processed",
        "confidence": 0.9,
        "evidence_span": "I have processed a full $120 refund for order #1042.",
    }
])

CLEAN = json.dumps([])

GARBAGE = "this is not valid model output {{{"


def routing_client() -> MetaModelClient:
    """One mock client whose reply depends on the transcript in the request.

    The pipeline always sends the transcript in the chat messages, so the
    handler routes deterministically no matter how many repair retries fire.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        body = request.content.decode()
        if "ORDER1042" in body:
            reply = PHANTOM_120
        elif "ORDER992" in body:
            reply = PHANTOM_45
        elif "BAD" in body:
            reply = GARBAGE
        else:
            reply = CLEAN
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": reply}}], "model": "test"},
        )

    return MetaModelClient(api_key="k", transport=httpx.MockTransport(handler))


def mock_ledger() -> MockLedgerAdapter:
    data = json.loads((FIXTURES / "mock_ledger.json").read_text())
    return MockLedgerAdapter(data)


def fresh() -> tuple[MockLedgerAdapter, RemediationService, ValueLedger]:
    return mock_ledger(), RemediationService(), ValueLedger()


def test_batch_sorts_drift_money_first() -> None:
    ledger, service, value = fresh()
    report = asyncio.run(
        run_batch(
            {
                "small.json": "transcript ORDER992 here",
                "big.json": "transcript ORDER1042 here",
                "clean.json": "nothing promised here",
            },
            routing_client(),
            ledger,
            service,
            value,
        )
    )
    assert report.verdict == "drift_found"
    assert report.total_at_risk_usd == 165.00
    assert [d.promise.order_id for d in report.drifts] == ["1042", "992"]
    assert [d.amount_at_risk_usd for d in report.drifts] == [120.00, 45.00]


def test_clean_batch_stays_green() -> None:
    ledger, service, value = fresh()
    report = asyncio.run(
        run_batch(
            {"clean.json": "nothing promised here"},
            routing_client(),
            ledger,
            service,
            value,
        )
    )
    assert report.verdict == "verified_green"
    assert report.total_at_risk_usd == 0.0
    assert report.drifts == []


def test_one_bad_transcript_does_not_kill_batch() -> None:
    ledger, service, value = fresh()
    report = asyncio.run(
        run_batch(
            {
                "good.json": "transcript ORDER992 here",
                "bad.json": "BAD transcript here",
            },
            routing_client(),
            ledger,
            service,
            value,
        )
    )
    assert report.verdict == "drift_found"
    assert len(report.items) == 2
    errors = [item for item in report.items if item.error]
    assert len(errors) == 1
    assert errors[0].source == "bad.json"
    assert "good.json" in [item.source for item in report.items if item.report]


def test_default_pass_never_touches_ledger() -> None:
    ledger, service, value = fresh()
    before = ledger.refunded_usd("992")
    report = asyncio.run(
        run_batch(
            {"phantom.json": "transcript ORDER992 here"},
            routing_client(),
            ledger,
            service,
            value,
        )
    )
    assert report.verdict == "drift_found"
    assert report.remediated == 0
    assert ledger.refunded_usd("992") == before


def test_auto_remediate_settles_and_rerun_is_safe() -> None:
    ledger, service, value = fresh()
    client = routing_client()
    first = asyncio.run(
        run_batch(
            {"phantom.json": "transcript ORDER992 here"},
            client,
            ledger,
            service,
            value,
            auto_remediate=True,
        )
    )
    assert first.remediated == 1
    assert ledger.refunded_usd("992") == 45.00
    second = asyncio.run(
        run_batch(
            {"phantom.json": "transcript ORDER992 here"},
            client,
            ledger,
            service,
            value,
            auto_remediate=True,
        )
    )
    assert second.remediated == 0
    assert second.verdict == "verified_green"
    assert ledger.refunded_usd("992") == 45.00


def test_empty_batch_is_green() -> None:
    ledger, service, value = fresh()
    report = asyncio.run(
        run_batch({}, routing_client(), ledger, service, value)
    )
    assert report.verdict == "verified_green"
    assert report.items == []


def test_repeat_order_flagged_across_sources() -> None:
    ledger, service, value = fresh()
    report = asyncio.run(
        run_batch(
            {
                "a.json": "transcript ORDER992 here",
                "b.json": "transcript ORDER992 here",
                "c.json": "transcript ORDER1042 here",
            },
            routing_client(),
            ledger,
            service,
            value,
        )
    )
    assert len(report.repeat_orders) == 1
    repeat = report.repeat_orders[0]
    assert repeat.order_id == "992"
    assert sorted(repeat.sources) == ["a.json", "b.json"]
    assert repeat.occurrences == 2
    assert repeat.total_at_risk_usd == 90.00


def test_single_source_is_not_a_repeat() -> None:
    ledger, service, value = fresh()
    report = asyncio.run(
        run_batch(
            {"only.json": "transcript ORDER992 here"},
            routing_client(),
            ledger,
            service,
            value,
        )
    )
    assert report.repeat_orders == []


def test_batch_replay_client_lookup_and_missing() -> None:
    client = BatchReplayClient({"a.json": PHANTOM_45})
    replay = client.for_source("a.json")
    assert isinstance(replay, ReplayClient)
    assert replay.source == "a.json"

    try:
        client.for_source("missing.json")
        assert False, "expected ExtractionError"
    except ExtractionError as exc:
        assert "no recorded output" in str(exc)

    res = asyncio.run(client.chat([{"role": "user", "content": "hi"}]))
    assert res == PHANTOM_45


def test_run_batch_with_batch_replay_client() -> None:
    ledger, service, value = fresh()
    replay_file = FIXTURES / "eval_live_output.json"
    replies, _ = load_replay(replay_file)
    client = BatchReplayClient(replies)

    eval_dir = FIXTURES / "eval"
    paths = sorted(eval_dir.glob("*.json"))
    transcripts = {p.name: load_transcript(str(p)) for p in paths}

    report = asyncio.run(run_batch(transcripts, client, ledger, service, value))
    assert report.verdict == "drift_found"
    assert len(report.items) == 12
    assert report.total_at_risk_usd == 285.50
    assert len(report.drifts) == 5
    assert len(report.repeat_orders) == 1
    assert report.repeat_orders[0].order_id == "992"


def test_daemon_cli_replay_offline(monkeypatch, capsys) -> None:
    monkeypatch.delenv("BASETEN_API_KEY", raising=False)
    exit_code = main([
        "--dir",
        str(FIXTURES / "eval"),
        "--ledger",
        "mock",
        "--replay",
        str(FIXTURES / "eval_live_output.json"),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "sources: 12" in captured.out
    assert "verdict: drift_found" in captured.out
    assert "total_at_risk: $285.50" in captured.out
    assert "order #992" in captured.out


def test_daemon_cli_replay_missing_file(monkeypatch, capsys) -> None:
    monkeypatch.delenv("BASETEN_API_KEY", raising=False)
    exit_code = main([
        "--dir",
        str(FIXTURES / "eval"),
        "--ledger",
        "mock",
        "--replay",
        "non_existent_file.json",
    ])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "Cannot read replay" in captured.err


def test_daemon_cli_dir_defaults_to_eval_if_present(monkeypatch, capsys) -> None:
    monkeypatch.delenv("BASETEN_API_KEY", raising=False)
    exit_code = main([
        "--ledger",
        "mock",
        "--replay",
        str(FIXTURES / "eval_live_output.json"),
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "sources: 12" in captured.out


def test_daemon_cli_without_replay_or_api_key_fails(monkeypatch, capsys) -> None:
    monkeypatch.delenv("BASETEN_API_KEY", raising=False)
    monkeypatch.setattr("app.daemon.load_dotenv_file", lambda _: None)
    exit_code = main([
        "--dir",
        str(FIXTURES / "eval"),
        "--ledger",
        "mock",
    ])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "BASETEN_API_KEY is not set" in captured.err
