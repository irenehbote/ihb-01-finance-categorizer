"""FastAPI application entry point.

Kept free of business logic so the app can be imported in tests without side effects
(no DB connection or model loading at import time).
"""

from fastapi import FastAPI

app = FastAPI(
    title="IHB-01 Finance Categorizer",
    version="0.1.0",
    description="Upload a bank CSV and get each transaction categorized.",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the service is up.

    Returns a fixed payload on purpose: a liveness check must not depend on the DB or
    an LLM provider, otherwise an outage there would make the whole service look down.
    """
    return {"status": "ok"}
