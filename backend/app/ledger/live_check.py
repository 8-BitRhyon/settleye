"""One-command read-only check of the Shopify dev-store ledger.

Usage:
    cd backend
    uv run python -m app.ledger.live_check 1001

This queries order refunds only. It never calls refundCreate. A 401 means the
dev-store custom-app token is missing or revoked, not that the order is wrong.
"""

from __future__ import annotations

import argparse
import os
import sys

from app.extract.live_check import load_dotenv_file
from app.ledger.shopify import ShopifyAdapter, ShopifyError


def token_hint(token: str) -> str | None:
    """Name the common wrong Shopify credential before sending it anywhere."""
    if token.startswith("shpss_"):
        return (
            "This is the app's API secret key (shpss_), not an Admin API "
            "access token. Copy the Admin API access token (shpat_) from the "
            "app's API credentials."
        )
    if token.startswith("shpua_"):
        return (
            "This looks like a user or OAuth token (shpua_), not a custom-app "
            "Admin API access token. Copy the shpat_ token from the app's API "
            "credentials."
        )
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only Shopify dev-store refund check."
    )
    parser.add_argument(
        "order", nargs="?", default="1001", help="Order name or number."
    )
    parser.add_argument("--env-file", default=None)
    args = parser.parse_args(argv)

    load_dotenv_file(args.env_file)
    store = os.environ.get("SHOPIFY_STORE_DOMAIN", "")
    token = os.environ.get("SHOPIFY_ADMIN_TOKEN", "")
    if not store or not token:
        print(
            "SHOPIFY_STORE_DOMAIN and SHOPIFY_ADMIN_TOKEN are required. "
            "No call was made.",
            file=sys.stderr,
        )
        return 2

    hint = token_hint(token)
    if hint is not None:
        print(hint, file=sys.stderr)
        print("No call was made.", file=sys.stderr)
        return 3

    adapter = ShopifyAdapter(store_domain=store, access_token=token)
    try:
        refunded = adapter.refunded_usd(args.order)
    except ShopifyError as exc:
        print(f"Shopify check failed: {exc}", file=sys.stderr)
        if "401" in str(exc) or "Unauthorized" in str(exc):
            print(
                "The dev-store token was rejected. Regenerate the custom-app "
                "Admin API token with read_orders and write_orders, update "
                "SHOPIFY_ADMIN_TOKEN, and rerun. No refund was attempted.",
                file=sys.stderr,
            )
        return 3

    order = args.order.lstrip("#")
    if refunded is None:
        print(f"Order #{order} was not found in {store}. No refund was attempted.")
        return 1
    print(f"Order #{order}: ${refunded:.2f} settled in {store}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
