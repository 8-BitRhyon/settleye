"""Thin client for the Meta model over an OpenAI-compatible endpoint.

Verified 2026-10-26: the canonical model ID is `meta-models/muse-spark-open`.
The `-1026` suffixed variant does not exist on Baseten, Modal, or anywhere
else. The ID lives in exactly one constant so a typo breaks loudly at the
wire level instead of silently at demo time.
"""

import os

import httpx

MODEL_ID = "meta-models/muse-spark-open-1026"
BASE_URL_DEFAULT = "https://inference.baseten.co/v1"


def model_id() -> str:
    """Active model ID: MODEL_ID override wins, event default otherwise.

    The event guide instructs `meta-models/muse-spark-open-1026` for this
    hackathon (a pinned event deployment), overriding the public catalog
    ID `meta-models/muse-spark-open`. Either works through MODEL_ID.
    """
    return os.environ.get("MODEL_ID", MODEL_ID)


class MetaModelClient:
    """Minimal OpenAI-compatible chat client with a startup health check."""

    def __init__(
        self,
        api_key: str,
        base_url: str = BASE_URL_DEFAULT,
        model: str = MODEL_ID,
        transport: httpx.BaseTransport | None = None,
        timeout_seconds: float = 60.0,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = httpx.AsyncClient(
            transport=transport,
            timeout=httpx.Timeout(timeout_seconds),
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def chat(
        self, messages: list[dict[str, str]], temperature: float = 0.2
    ) -> str:
        """Return the raw assistant message content (untrusted text)."""
        response = await self._client.post(
            f"{self._base_url}/chat/completions",
            headers=self._headers(),
            json={
                "model": self._model,
                "messages": messages,
                "temperature": temperature,
            },
        )
        response.raise_for_status()
        payload = response.json()
        return str(payload["choices"][0]["message"]["content"])

    async def health_check(self) -> bool:
        """True when the endpoint answers; never raises."""
        try:
            response = await self._client.get(
                f"{self._base_url}/models", headers=self._headers()
            )
            return response.status_code == 200
        except Exception:
            return False
