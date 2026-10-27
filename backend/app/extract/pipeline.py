"""Transcript-to-promise extraction with validate-and-retry.

Baseten accepts but does NOT enforce `json_schema` for Muse Spark Open, so
constrained decoding is unavailable. This pipeline treats every model reply
as untrusted text: strip fences, parse defensively, Pydantic-validate, and
repair with the validation error fed back. Bounded to MAX_REPAIRS repairs;
anything beyond that raises instead of looping forever.
"""

import json
from typing import Any

from pydantic import ValidationError

from app.extract.client import MetaModelClient
from app.models import PromiseEntity

MAX_REPAIRS = 2

SYSTEM_PROMPT = """You extract binding promises an AI support agent made to a customer.
Reply with a JSON array only, no prose, no code fences. Each item has:
- action: one of refund, cancel, reship, credit, other
- amount: number in USD or null
- order_id: string or null
- target_system: one of stripe, shopify, unknown
- asserted_state: what the agent claimed is now true
- confidence: number 0.0 to 1.0
- evidence_span: verbatim quote from the transcript
- terminal_status: one of binding, conditional, superseded, retracted, info_only.
  binding means an unconditional commitment that still stands at the end of the
  transcript. conditional means it depends on a future customer action. superseded
  means a later turn replaced it. retracted means it was taken back. info_only
  means policy explanation, never a commitment.
If the transcript contains no promises, reply with []."""


class ExtractionError(Exception):
    """The model never produced valid promise JSON within the retry budget."""


def _strip_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    return cleaned.strip()


def _coerce_items(raw: Any) -> list[Any]:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in ("promises", "items", "results"):
            if isinstance(raw.get(key), list):
                return raw[key]
        return [raw]
    raise ExtractionError(f"Top-level JSON must be an array or object, got {type(raw)}")


def _parse_and_validate(reply: str) -> list[PromiseEntity]:
    try:
        raw = json.loads(_strip_fences(reply))
    except json.JSONDecodeError as exc:
        raise ExtractionError(f"Reply is not JSON: {exc}") from exc
    try:
        return [PromiseEntity.model_validate(item) for item in _coerce_items(raw)]
    except ValidationError as exc:
        raise ExtractionError(f"Reply failed schema validation: {exc}") from exc


async def extract_promises(transcript: str, client: MetaModelClient) -> list[PromiseEntity]:
    """Extract promise entities from a transcript, repairing at most twice."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": transcript},
    ]
    reply = await client.chat(messages)
    attempts = 0
    while True:
        try:
            return _parse_and_validate(reply)
        except ExtractionError as exc:
            if attempts >= MAX_REPAIRS:
                raise
            attempts += 1
            messages.append({"role": "assistant", "content": reply})
            messages.append({
                "role": "user",
                "content": (
                    "Your last reply was invalid. "
                    f"Error: {exc}. Reply with a JSON array only."
                ),
            })
            reply = await client.chat(messages)
