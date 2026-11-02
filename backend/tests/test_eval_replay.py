"""Replay test over recorded live model output.

The routing-mock tests prove the reconcile contract. This test proves the
published accuracy number against output a real model actually produced, so
the eval score cannot be self-fulfilling. If the recorded file and the
manifest disagree, this fails loudly.

Recorded 2026-11-01 with meta-models/muse-spark-open-1026 via Baseten
(fixtures/eval_live_output.json holds each case's entities plus elapsed time).
"""

import json
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
EXPECTED = json.loads((FIXTURES / "eval_expected.json").read_text())
RECORDED = json.loads((FIXTURES / "eval_live_output.json").read_text())


def _norm_order(value: str | None) -> str | None:
    if value is None:
        return None
    return str(value).strip().lstrip("#")


def test_recorded_output_covers_every_expected_case() -> None:
    assert set(RECORDED) == set(EXPECTED), "recorded set and manifest must match"
    assert len(RECORDED) == 12
    for name, entry in RECORDED.items():
        assert entry["model"], f"{name} missing model id"
        assert entry["model"].startswith("meta-models/muse-spark-open")


def test_entity_accuracy_matches_published_number() -> None:
    exact = 0
    for name, want in EXPECTED.items():
        got = [
            (p["action"], _norm_order(p["order_id"]), p["amount"], p["terminal_status"])
            for p in RECORDED[name]["entities"]
        ]
        expected = [
            (
                p["action"],
                _norm_order(p["order_id"]),
                p["amount"],
                p["terminal_status"],
            )
            for p in want["promises"]
        ]
        if got == expected:
            exact += 1
    # Published claim: 12 of 12 verdicts, 11 of 12 exact entity matches.
    assert exact == 11, f"expected 11 exact entity matches, recorded {exact}"


def test_no_binding_promise_appears_where_manifest_says_none() -> None:
    for name, want in EXPECTED.items():
        expected_binding = [p for p in want["promises"] if p["terminal_status"] == "binding"]
        recorded_binding = [
            p for p in RECORDED[name]["entities"] if p["terminal_status"] == "binding"
        ]
        assert len(recorded_binding) == len(expected_binding), (
            f"{name}: binding count drifted, {len(recorded_binding)} recorded "
            f"vs {len(expected_binding)} expected"
        )


def test_non_binding_cases_recorded_without_binding() -> None:
    for name in (
        "t05_retracted.json",
        "t06_conditional.json",
        "t07_info_only.json",
    ):
        statuses = [p["terminal_status"] for p in RECORDED[name]["entities"]]
        assert "binding" not in statuses, f"{name}: {statuses}"
