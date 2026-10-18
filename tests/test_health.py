"""Smoke test: the installed package imports and the app answers HTTP requests."""

from fastapi.testclient import TestClient

from finance_api.main import app


def test_health_returns_ok() -> None:
    """GET /health returns 200 with status ok.

    Importing `finance_api` (not a relative path) proves the src/ layout is installed
    correctly in the venv: if packaging were broken, this import would fail here first.
    """
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
