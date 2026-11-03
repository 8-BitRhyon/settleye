"""Jev gate: a calibrated decision layer in front of generative extraction.

Jev (TypeSafe AI) is discriminative. It does not generate text, so it cannot
pull a refund amount or an order number out of prose. What it can do is answer
bounded questions with calibrated probabilities:

- Does this transcript contain a financial promise at all?
- If so, what is the commitment's end state?

That is enough to skip the expensive generative call on transcripts that
promise nothing, and to attach a real probability to the modality decision
instead of trusting an overconfident token distribution.

The gate never decides whether money moved. Reconciliation stays deterministic
code. Jev only decides whether a promise is present and what kind it is.
"""

from dataclasses import dataclass

import httpx

BASE_URL_DEFAULT = "https://api.typesafe.ai/v1"
MODEL_DEFAULT = "jev-latest"
# Below this probability of a promise, skip the generative extraction call.
SKIP_THRESHOLD = 0.20

MODALITIES = (
    "binding",
    "conditional",
    "superseded",
    "retracted",
    "info_only",
)

QUESTIONS = {
    "has_promise": {
        "type": "noul",
        "instructions": (
            "The agent made a financial promise to the customer: a refund, "
            "credit, discount, or compensation that the agent claims is done "
            "or will be done."
        ),
    },
    "modality": {
        "type": "choice",
        "instructions": (
            "What is the end state of the agent's promise at the end of the "
            "transcript?"
        ),
        "criteria": {
            "binding": "An unconditional commitment that still stands.",
            "conditional": "Depends on a future customer action.",
            "superseded": "A later turn replaced it with a different amount or action.",
            "retracted": "The agent took it back.",
            "info_only": "Policy explanation, never a commitment.",
        },
    },
}


class JevError(Exception):
    """Jev answered with an error, or with a shape we cannot trust."""


@dataclass
class GateDecision:
    """What the gate concluded, with the probability attached."""

    has_promise: float
    modality: str
    modality_confidence: float

    @property
    def skip_extraction(self) -> bool:
        return self.has_promise < SKIP_THRESHOLD


class JevClient:
    """Minimal client for the System One endpoint."""

    def __init__(
        self,
        api_key: str,
        base_url: str = BASE_URL_DEFAULT,
        model: str = MODEL_DEFAULT,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = httpx.AsyncClient(
            transport=transport,
            timeout=httpx.Timeout(timeout_seconds),
        )

    async def system_one(
        self, state: str, questions: dict, model: str | None = None
    ) -> dict:
        """One request, one answer per question."""
        response = await self._client.post(
            f"{self._base_url}/systemone",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "state": state,
                "model": model or self._model,
                "questions": questions,
            },
        )
        try:
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            raise JevError(f"Jev call failed: {exc}") from exc
        if not isinstance(payload, dict):
            raise JevError("Jev returned a non-object payload.")
        if payload.get("error"):
            raise JevError(f"Jev error: {payload['error']}")
        answers = payload.get("answers")
        if not isinstance(answers, dict):
            raise JevError("Jev response has no answers object.")
        return answers

    async def close(self) -> None:
        await self._client.aclose()


def _prob(value: object) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise JevError(f"Expected a probability, got {value!r}") from exc
    if not 0.0 <= number <= 1.0:
        raise JevError(f"Probability out of range: {number}")
    return number


def read_decision(answers: dict) -> GateDecision:
    """Parse the two answers we asked for, failing loudly on anything else."""
    try:
        has_promise = _prob(answers["has_promise"]["noul"])
        modality_block = answers["modality"]
        modality = str(modality_block["choice"])
        confidence = _prob(modality_block["confidence"])
    except (KeyError, TypeError) as exc:
        raise JevError(f"Malformed Jev answer: {exc}") from exc
    if modality not in MODALITIES:
        raise JevError(f"Unknown modality from Jev: {modality}")
    return GateDecision(
        has_promise=has_promise,
        modality=modality,
        modality_confidence=confidence,
    )


async def gate_transcript(client: JevClient, transcript: str) -> GateDecision:
    """Ask Jev the two gating questions about one transcript."""
    answers = await client.system_one(transcript, QUESTIONS)
    return read_decision(answers)
