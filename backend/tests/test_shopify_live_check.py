"""The dev-store check fails loudly and never writes."""

from __future__ import annotations

import pytest

from app.ledger import live_check
from app.ledger.shopify import ShopifyError


class FakeAdapter:
    def __init__(self, *args, **kwargs) -> None:
        pass

    def refunded_usd(self, order: str) -> float | None:
        return 6.0


class MissingAdapter(FakeAdapter):
    def refunded_usd(self, order: str) -> float | None:
        return None


class UnauthorizedAdapter(FakeAdapter):
    def refunded_usd(self, order: str) -> float | None:
        raise ShopifyError(
            "Shopify call failed: Client error '401 Unauthorized' for url "
            "'https://example.myshopify.com/admin/api/2026-10/graphql.json'"
        )


@pytest.fixture(autouse=True)
def no_dotenv(monkeypatch):
    monkeypatch.setattr(live_check, "load_dotenv_file", lambda *args, **kwargs: None)


def test_shared_secret_is_refused_before_the_call(monkeypatch, capsys) -> None:
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "example.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ADMIN_TOKEN", "shpss_secret")
    monkeypatch.setattr(live_check, "ShopifyAdapter", pytest.fail)
    assert live_check.main(["1001"]) == 3
    err = capsys.readouterr().err
    assert "API secret key" in err
    assert "No call was made" in err


def test_user_access_token_is_accepted(monkeypatch, capsys) -> None:
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "example.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ADMIN_TOKEN", "shpua_token")
    monkeypatch.setattr(live_check, "ShopifyAdapter", FakeAdapter)
    assert live_check.main(["1001"]) == 0
    assert "$6.00 settled" in capsys.readouterr().out


def test_missing_config_is_a_clean_refusal(monkeypatch, capsys) -> None:
    monkeypatch.delenv("SHOPIFY_STORE_DOMAIN", raising=False)
    monkeypatch.delenv("SHOPIFY_ADMIN_TOKEN", raising=False)
    assert live_check.main(["1001"]) == 2
    assert "required" in capsys.readouterr().err


def test_reads_settled_refund(monkeypatch, capsys) -> None:
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "example.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ADMIN_TOKEN", "shp_test")
    monkeypatch.setattr(live_check, "ShopifyAdapter", FakeAdapter)
    assert live_check.main(["1001"]) == 0
    assert "$6.00 settled" in capsys.readouterr().out


def test_missing_order_is_not_a_crash(monkeypatch, capsys) -> None:
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "example.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ADMIN_TOKEN", "shp_test")
    monkeypatch.setattr(live_check, "ShopifyAdapter", MissingAdapter)
    assert live_check.main(["1001"]) == 1
    assert "was not found" in capsys.readouterr().out


def test_401_tells_you_how_to_fix_it(monkeypatch, capsys) -> None:
    monkeypatch.setenv("SHOPIFY_STORE_DOMAIN", "example.myshopify.com")
    monkeypatch.setenv("SHOPIFY_ADMIN_TOKEN", "shp_test")
    monkeypatch.setattr(live_check, "ShopifyAdapter", UnauthorizedAdapter)
    assert live_check.main(["1001"]) == 3
    err = capsys.readouterr().err
    assert "401" in err
    assert "Regenerate" in err
    assert "No refund was attempted" in err
