"""API smoke tests with TestClient."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@patch("app.api.routes.get_cost_summary")
def test_api_summary(mock_summary):
    mock_summary.return_value = {
        "current_total": 100.0,
        "previous_total": 90.0,
        "change_pct": 11.1,
        "top_services": [],
        "mom": {},
        "forecast": [],
        "start": "2026-07-01",
        "end": "2026-07-31",
        "generated_at": "2026-08-01T00:00:00Z",
        "period_days": 30,
    }
    r = client.get("/api/summary")
    assert r.status_code == 200
    assert r.json()["current_total"] == 100.0
