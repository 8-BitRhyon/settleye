"""The token refresh mints, reports only the prefix, and writes the token."""

from __future__ import annotations

import json

import pytest

from app.ledger import token as token_module


@pytest.fixture(autouse=True)
def no_dotenv(monkeypatch):
    monkeypatch.setattr(token_module, "load_dotenv_file", lambda *args, **kwargs: None)


class FakeResponse:
    def __init__(self, status_code: int, payload: dict) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self) -> dict:
        return self._payload


def clear_shopify_env(monkeypatch) -> None:
    for key in (
        "SHOPIFY_STORE_DOMAIN",
        "SHOPIFY_CLIENT_ID",
        "SHOPIFY_CLIENT_SECRET",
        "SHOPIFY_ADMIN_TOKEN",
    ):
        monkeypatch.delenv(key, raising=False)


def test_missing_config_is_a_clean_refusal(monkeypatch, capsys) -> None:
    clear_shopify_env(monkeypatch)
    assert token_module.main([]) == 2
    assert "required" in capsys.readouterr().err


def test_mints_and_writes_without_printing_the_token(
    monkeypatch, tmp_path, capsys
) -> None:
    clear_shopify_env(monkeypatch)
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "example.myshopify.com")
    monkeypatch.setenv("SHOPIFY_CLIENT_ID", "client")
    monkeypatch.setenv("SHOPIFY_CLIENT_SECRET", "secret")
    env_path = tmp_path / ".env"
    env_path.write_text("SHOPIFY_ADMIN_TOKEN=old\n", encoding="utf-8")
    fake = FakeResponse(
        200,
        {
            "access_token": "shpua_abc123",
            "scope": "write_orders,read_returns",
            "expires_in": 3600,
        },
    )
    monkeypatch.setattr(token_module.httpx, "post", lambda *args, **kwargs: fake)

    assert token_module.main(["--env-file", str(env_path), "--write"]) == 0
    captured = capsys.readouterr()
    assert "shpua_" in captured.out
    assert "shpua_abc123" not in captured.out
    assert "shpua_abc123" not in captured.err
    assert "SHOPIFY_ADMIN_TOKEN=shpua_abc123" in env_path.read_text()


def test_exchange_failure_is_loud(monkeypatch, capsys) -> None:
    clear_shopify_env(monkeypatch)
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "example.myshopify.com")
    monkeypatch.setenv("SHOPIFY_CLIENT_ID", "client")
    monkeypatch.setenv("SHOPIFY_CLIENT_SECRET", "secret")
    fake = FakeResponse(401, {"error": "invalid_client"})
    monkeypatch.setattr(token_module.httpx, "post", lambda *args, **kwargs: fake)

    assert token_module.main([]) == 3
    assert "HTTP 401" in capsys.readouterr().err
