"""Tests for the live-model proof script (everything except the network).

The live call itself needs real Baseten credits and cannot run in CI.
What is tested here: argument handling, missing-key behavior, transcript
loading, and report formatting. The script must fail loudly, never silently.
"""

from app.extract.live_check import format_report, load_transcript, resolve_api_key


def test_missing_key_resolves_none(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("BASETEN_API_KEY", raising=False)
    assert resolve_api_key(explicit=None) is None


def test_explicit_key_wins_over_env(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BASETEN_API_KEY", "env-key")
    assert resolve_api_key(explicit="flag-key") == "flag-key"


def test_env_key_used_when_no_flag(monkeypatch) -> None:
    monkeypatch.setenv("BASETEN_API_KEY", "env-key")
    assert resolve_api_key(explicit=None) == "env-key"


def test_load_phantom_fixture() -> None:
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[2]
        / "fixtures"
        / "transcript_phantom_refund.json"
    )
    text = load_transcript(str(path))
    assert "#992" in text
    assert "$45" in text


def test_format_report_shows_model_and_entities() -> None:
    from app.models import PromiseEntity

    report = format_report(
        model_id="meta-models/muse-spark-open",
        elapsed_seconds=1.23,
        entities=[
            PromiseEntity(
                action="refund",
                amount=45.00,
                order_id="992",
                target_system="stripe",
                asserted_state="full refund processed",
                confidence=0.9,
                evidence_span="processed",
            )
        ],
    )
    assert "meta-models/muse-spark-open" in report
    assert "992" in report
    assert "1.23s" in report
