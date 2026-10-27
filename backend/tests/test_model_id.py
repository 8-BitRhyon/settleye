"""The model ID is load-bearing and contested.

Research (2026-10-26) found `meta-models/muse-spark-open-1026` on no
provider; the hackathon FAQ instructs exactly that suffixed ID. The code
therefore defaults to the verified canonical ID but honors a MODEL_ID
override, so either endpoint works with zero code changes.
"""

from app.extract.client import MODEL_ID, model_id


def test_default_is_verified_canonical_id() -> None:
    assert MODEL_ID == "meta-models/muse-spark-open"


def test_env_override_selects_hackathon_id(monkeypatch) -> None:
    monkeypatch.setenv("MODEL_ID", "meta-models/muse-spark-open-1026")
    assert model_id() == "meta-models/muse-spark-open-1026"


def test_unset_env_falls_back_to_canonical(monkeypatch) -> None:
    monkeypatch.delenv("MODEL_ID", raising=False)
    assert model_id() == MODEL_ID
