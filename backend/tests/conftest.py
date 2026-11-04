"""Shared isolation: no test writes receipts to the repo-local store.

The default store exists so the API and daemon survive restarts in real
use. Tests must never share it: each test points the env override at its
own tmp file, so receipt state cannot leak between tests.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Path]:
    path = tmp_path / "receipts.jsonl"
    monkeypatch.setenv("SETTLEYE_RECEIPTS_PATH", str(path))
    yield path


@pytest.fixture(autouse=True)
def isolated_keyring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Path]:
    """Never let a test read or write the repo-local issuer key or registry."""
    registry = tmp_path / "keyring.json"
    key = tmp_path / "issuer.key"
    monkeypatch.setenv("SETTLEYE_KEYRING_PATH", str(registry))
    monkeypatch.setenv("SETTLEYE_ISSUER_KEY_PATH", str(key))
    yield registry
