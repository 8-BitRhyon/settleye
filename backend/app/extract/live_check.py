"""One-command live proof that the Meta model extracts promises.

Usage once Baseten credits land:
    export BASETEN_API_KEY=...
    cd backend
    uv run python -m app.extract.live_check ../fixtures/transcript_phantom_refund.json

Exit 0 prints the model ID, wall time, and validated entities. Anything
else fails loudly: missing key (2), unreachable model (3), unrepairable
output (4). This output doubles as judging evidence that the Meta model,
not regex, does the extraction.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from app.extract.client import BASE_URL_DEFAULT, MetaModelClient, model_id
from app.extract.pipeline import ExtractionError, extract_promises
from app.models import PromiseEntity


def resolve_api_key(explicit: str | None) -> str | None:
    """CLI flag wins, then environment. None means fail loudly, not silently."""
    if explicit:
        return explicit
    return os.environ.get("BASETEN_API_KEY")


def repo_env_path() -> Path:
    """Repo-root `.env`, resolved from this file so CWD never matters."""
    return Path(__file__).resolve().parents[3] / ".env"


def load_dotenv_file(path: Path | str | None = None) -> None:
    """Minimal `.env` loader: KEY=VALUE lines, `#` comments, `export`
    prefixes, and single/double quotes handled. Real environment variables
    always win. Missing files are silent. No dependency."""
    target = Path(path) if path is not None else repo_env_path()
    try:
        text = target.read_text(encoding="utf-8")
    except OSError:
        return
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def load_transcript(path: str) -> str:
    """Load a fixture file (JSON with turns) or raw text into one string."""
    text = Path(path).read_text(encoding="utf-8")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text
    turns = payload.get("turns", [])
    return "\n".join(
        f"{turn.get('role', '?')}: {turn.get('text', '')}" for turn in turns
    )


def format_report(
    model_id: str, elapsed_seconds: float, entities: list[PromiseEntity]
) -> str:
    """Human- and camera-readable proof of a live model extraction."""
    lines = [
        f"model: {model_id}",
        f"elapsed: {elapsed_seconds:.2f}s",
        f"promises: {len(entities)}",
    ]
    for entity in entities:
        lines.append(
            f"- {entity.action} "
            f"${entity.amount if entity.amount is not None else '?'} "
            f"order #{entity.order_id or '?'} "
            f"[{entity.target_system}] conf={entity.confidence:.2f}"
        )
        if entity.evidence_span:
            lines.append(f'  evidence: "{entity.evidence_span}"')
    return "\n".join(lines)


async def _run(args: argparse.Namespace) -> int:
    api_key = resolve_api_key(args.api_key)
    if not api_key:
        print(
            "BASETEN_API_KEY is not set. Export it or pass --api-key. "
            "No call was made.",
            file=sys.stderr,
        )
        return 2
    client = MetaModelClient(
        api_key=api_key, base_url=args.base_url, model=args.model or model_id()
    )
    if not await client.health_check():
        print(
            f"Model endpoint unreachable at {args.base_url}. "
            "Check the key, the URL, and cold-start waiting.",
            file=sys.stderr,
        )
        return 3
    transcript = load_transcript(args.transcript)
    started = time.monotonic()
    try:
        entities = await extract_promises(transcript, client)
    except ExtractionError as exc:
        print(f"Model output never validated: {exc}", file=sys.stderr)
        return 4
    elapsed = time.monotonic() - started
    print(format_report(args.model or model_id(), elapsed, entities))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Live proof of Meta-model promise extraction."
    )
    parser.add_argument("transcript", help="Fixture JSON or raw text file.")
    parser.add_argument("--api-key", default=None, help="Baseten key (or env).")
    parser.add_argument("--base-url", default=BASE_URL_DEFAULT)
    parser.add_argument("--model", default=None)
    parser.add_argument(
        "--env-file",
        default=None,
        help="Path to .env (defaults to repo-root .env).",
    )
    args = parser.parse_args(argv)
    load_dotenv_file(args.env_file)
    import asyncio

    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
