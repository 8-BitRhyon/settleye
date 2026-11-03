"""One-command live check of the Jev gate against the eval set.

Usage once TYPESAFE_API_KEY is in .env:
    cd backend
    uv run python -m app.gate.live_check

Exit 0 prints a per-case table: the promise probability, the modality Jev
chose, and whether it matches the manifest. Anything else fails loudly.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from app.extract.live_check import load_dotenv_file
from app.gate.jev import BASE_URL_DEFAULT, MODEL_DEFAULT, JevClient, JevError, gate_transcript

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures"


def load_cases() -> dict[str, str]:
    """Fixture transcripts keyed by filename, in the same shape the eval uses."""
    cases: dict[str, str] = {}
    for path in sorted((FIXTURES / "eval").glob("*.json")):
        payload = json.loads(path.read_text())
        cases[path.name] = "\n".join(
            f"{turn.get('role', '?')}: {turn.get('text', '')}"
            for turn in payload.get("turns", [])
        )
    return cases


async def _run(api_key: str, base_url: str, model: str) -> int:
    cases = load_cases()
    expected = json.loads((FIXTURES / "eval_expected.json").read_text())
    client = JevClient(api_key=api_key, base_url=base_url, model=model)
    rows = []
    failures = 0
    try:
        for name, text in cases.items():
            try:
                decision = await gate_transcript(client, text)
            except JevError as exc:
                print(f"{name}: ERROR {exc}", file=sys.stderr)
                failures += 1
                continue
            want = expected[name]["promises"]
            want_binding = any(p["terminal_status"] == "binding" for p in want)
            # A promise exists if the manifest has any entity at all.
            want_any = len(want) > 0
            call_it = decision.has_promise >= 0.20
            agree = call_it == want_any
            rows.append((name, decision, want_any, want_binding, agree))
    finally:
        await client.close()

    print(f"model: {model}")
    print(f"skip threshold: 0.20\n")
    print(f"{'case':<26}{'P(promise)':>11}  {'modality':<12}{'conf':>6}  verdict")
    for name, d, want_any, want_binding, agree in rows:
        verdict = "ok" if agree else "MISMATCH"
        if agree and want_binding:
            verdict = "ok, would bind"
        print(
            f"{name:<26}{d.has_promise:>11.3f}  {d.modality:<12}"
            f"{d.modality_confidence:>6.2f}  {verdict}"
        )

    agree_count = sum(1 for r in rows if r[4])
    print(f"\nagreement: {agree_count} of {len(rows)}")
    skipped = sum(1 for r in rows if r[1].has_promise < 0.20)
    print(f"would skip extraction: {skipped} of {len(rows)}")
    return 0 if failures == 0 else 5


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Live Jev gate check.")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--base-url", default=BASE_URL_DEFAULT)
    parser.add_argument("--model", default=MODEL_DEFAULT)
    parser.add_argument("--env-file", default=None)
    args = parser.parse_args(argv)
    load_dotenv_file(args.env_file)
    import os

    key = args.api_key or os.environ.get("TYPESAFE_API_KEY")
    if not key:
        print(
            "TYPESAFE_API_KEY is not set. Add it to .env or pass --api-key. "
            "No call was made.",
            file=sys.stderr,
        )
        return 2
    return asyncio.run(_run(key, args.base_url, args.model))


if __name__ == "__main__":
    raise SystemExit(main())
