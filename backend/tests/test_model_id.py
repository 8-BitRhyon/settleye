"""The model ID is load-bearing and event-directed.

The event guide instructs `meta-models/muse-spark-open-1026` (a pinned
event deployment), overriding the public catalog ID. The default follows
the event; MODEL_ID selects anything else with zero code changes.
"""

from app.extract.client import MODEL_ID, model_id

EVENT_MODEL_ID = "meta-models/muse-spark-open-1026"


def test_default_is_event_instructed_id() -> None:
    assert MODEL_ID == EVENT_MODEL_ID


def test_env_override_selects_canonical_id(monkeypatch) -> None:
    monkeypatch.setenv("MODEL_ID", "meta-models/muse-spark-open")
    assert model_id() == "meta-models/muse-spark-open"


def test_unset_env_falls_back_to_event_default(monkeypatch) -> None:
    monkeypatch.delenv("MODEL_ID", raising=False)
    assert model_id() == MODEL_ID
