"""Unit tests for cost explorer helpers (mocked)."""

from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.core.cost_explorer import (
    compute_mom_trend,
    results_to_dataframe,
    simple_forecast,
)


def test_results_to_dataframe_empty():
    df = results_to_dataframe([])
    assert df.empty


def test_results_to_dataframe_basic():
    results = [
        {
            "TimePeriod": {"Start": "2026-07-01", "End": "2026-07-02"},
            "Groups": [
                {
                    "Keys": ["Amazon EC2"],
                    "Metrics": {
                        "UnblendedCost": {"Amount": "42.50", "Unit": "USD"}
                    },
                }
            ],
            "Total": {
                "UnblendedCost": {"Amount": "42.50", "Unit": "USD"}
            },
        }
    ]
    df = results_to_dataframe(results, "SERVICE")
    assert len(df) == 2
    assert "Amazon EC2" in df["service"].values
    assert df[df["service"] == "Amazon EC2"]["amount"].iloc[0] == 42.50


def test_compute_mom_trend_insufficient_data():
    df = pd.DataFrame({"date": pd.to_datetime(["2026-07-01"]), "service": ["_TOTAL_"], "amount": [100.0]})
    result = compute_mom_trend(df)
    assert result["current"] == 100.0
    assert result["previous"] == 0.0


def test_simple_forecast_empty():
    assert simple_forecast(pd.DataFrame()) == []


def test_simple_forecast_short_series():
    df = pd.DataFrame(
        {
            "date": pd.date_range("2026-07-01", periods=5),
            "amount": [10, 12, 11, 13, 14],
        }
    )
    assert simple_forecast(df) == []
