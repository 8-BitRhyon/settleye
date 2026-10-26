"""The dashboard runs on another origin during development and judging.

Without CORS headers the browser blocks every API call, so the inbox
would be dead on arrival. This pins the preflight behavior.
"""

from fastapi.testclient import TestClient

from app.main import app


def test_healthz_answers_cors_preflight() -> None:
    client = TestClient(app)
    response = client.options(
        "/healthz",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert "http://localhost:5173" in response.headers.get(
        "access-control-allow-origin", ""
    )
