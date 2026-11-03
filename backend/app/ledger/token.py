"""Mint a short-lived Shopify client-credentials token for the dev store.

Usage:
    cd backend
    uv run python -m app.ledger.token --write

The Dev Dashboard app's client ID and secret exchange for an `shpua_` access
token at `/admin/oauth/access_token`. The token expires, so rerun this when the
live check returns 401. The token is written to `.env`; it is never printed.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import httpx

from app.extract.live_check import load_dotenv_file, repo_env_path


def write_token(env_path: Path, token: str) -> bool:
    lines = env_path.read_text(encoding="utf-8").splitlines()
    updated = []
    replaced = False
    for line in lines:
        if line.startswith("SHOPIFY_ADMIN_TOKEN="):
            updated.append(f"SHOPIFY_ADMIN_TOKEN={token}")
            replaced = True
        else:
            updated.append(line)
    if not replaced:
        updated.append(f"SHOPIFY_ADMIN_TOKEN={token}")
    env_path.write_text("\n".join(updated) + "\n", encoding="utf-8")
    return replaced


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Mint a Shopify client-credentials access token."
    )
    parser.add_argument("--store", default=None)
    parser.add_argument("--client-id", default=None)
    parser.add_argument("--client-secret", default=None)
    parser.add_argument("--env-file", default=None)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the new token to the env file. The token is never printed.",
    )
    args = parser.parse_args(argv)

    load_dotenv_file(args.env_file)
    store = args.store or os.environ.get("SHOPIFY_STORE_DOMAIN", "")
    client_id = args.client_id or os.environ.get("SHOPIFY_CLIENT_ID", "")
    client_secret = args.client_secret or os.environ.get(
        "SHOPIFY_CLIENT_SECRET", ""
    )
    if not store or not client_id or not client_secret:
        print(
            "SHOPIFY_STORE_DOMAIN, SHOPIFY_CLIENT_ID, and "
            "SHOPIFY_CLIENT_SECRET are required. No call was made.",
            file=sys.stderr,
        )
        return 2

    try:
        response = httpx.post(
            f"https://{store}/admin/oauth/access_token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=30,
        )
    except Exception as exc:
        print(f"Token exchange failed: {exc}", file=sys.stderr)
        return 3

    if response.status_code != 200:
        print(
            f"Token exchange failed: HTTP {response.status_code}: "
            f"{response.text[:300]}",
            file=sys.stderr,
        )
        return 3
    payload = response.json()
    token = payload.get("access_token")
    if not token:
        print("Token exchange returned no access_token.", file=sys.stderr)
        return 3

    print(
        f"token prefix {token[:6]}  length {len(token)}  "
        f"scope {payload.get('scope')}  expires_in {payload.get('expires_in')}"
    )
    if args.write:
        env_path = Path(args.env_file) if args.env_file else repo_env_path()
        replaced = write_token(env_path, token)
        print(f"updated {env_path} (token not printed; replaced={replaced})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
