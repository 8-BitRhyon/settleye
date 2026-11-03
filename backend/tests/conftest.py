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
