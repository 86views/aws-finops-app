"""Unit tests for report generation module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.reports.generator import (
    _period_dates,
    generate_csv,
    generate_html,
    generate_pdf,
    generate_reports,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    ("period", "expected_days"),
    [
        ("daily", 1),
        ("weekly", 7),
        ("monthly", 30),
    ],
)
def test_period_dates(period: Any, expected_days: int) -> None:
    start, end = _period_dates(period)
    assert (end - start).days == expected_days


def test_generate_csv(tmp_path: Path) -> None:
    summary = {
        "start": "2026-08-01",
        "end": "2026-08-13",
        "current_total": 1500.50,
        "previous_total": 1200.00,
        "change_pct": 25.04,
        "top_services": [{"service": "Amazon EC2", "amount": 800.00}],
        "forecast": [{"date": "2026-08-14", "predicted_amount": 1550.00}],
    }
    output_file = tmp_path / "reports" / "test.csv"
    result_path = generate_csv(summary, output_file)

    assert result_path.exists()
    content = result_path.read_text(encoding="utf-8")
    assert "Amazon EC2" in content
    assert "1500.5" in content


@patch("app.reports.generator._jinja_env")
def test_generate_html(mock_jinja: MagicMock, tmp_path: Path) -> None:
    mock_template = MagicMock()
    mock_template.render.return_value = "<html><body>FinOps Report</body></html>"
    mock_jinja.return_value.get_template.return_value = mock_template

    output_file = tmp_path / "test.html"
    result_path = generate_html({}, "daily", output_file)

    assert result_path.exists()
    assert result_path.read_text(encoding="utf-8") == "<html><body>FinOps Report</body></html>"


def test_generate_pdf_weasyprint_missing(tmp_path: Path) -> None:
    html_file = tmp_path / "test.html"
    html_file.write_text("<html></html>", encoding="utf-8")
    pdf_file = tmp_path / "test.pdf"

    with patch.dict("sys.modules", {"weasyprint": None}):
        result_path = generate_pdf(html_file, pdf_file)
        assert result_path == pdf_file
        assert not pdf_file.exists()


@patch("app.reports.generator.generate_pdf")
@patch("app.reports.generator.generate_html")
@patch("app.reports.generator.generate_csv")
@patch("app.reports.generator.get_tag_costs")
@patch("app.reports.generator.get_region_costs")
@patch("app.reports.generator.get_service_costs")
@patch("app.reports.generator.get_cost_summary")
@patch("app.reports.generator.get_settings")
def test_generate_reports_success(
    mock_settings: MagicMock,
    mock_summary: MagicMock,
    mock_service: MagicMock,
    mock_region: MagicMock,
    mock_tag: MagicMock,
    mock_csv: MagicMock,
    mock_html: MagicMock,
    mock_pdf: MagicMock,
    tmp_path: Path,
) -> None:
    mock_settings.return_value.report_output_dir = tmp_path
    mock_summary.return_value = {"current_total": 500.0}

    mock_service.return_value = pd.DataFrame([{"service": "Amazon EC2", "amount": 300.0}])
    mock_region.return_value = pd.DataFrame([{"region": "us-east-1", "amount": 500.0}])
    mock_tag.return_value = pd.DataFrame([{"environment": "production", "amount": 500.0}])

    mock_csv.return_value = tmp_path / "report.csv"
    mock_html.return_value = tmp_path / "report.html"
    mock_pdf.return_value = tmp_path / "report.pdf"

    result = generate_reports("daily")

    assert result["csv"] == tmp_path / "report.csv"
    assert result["summary"]["by_region"] == {"us-east-1": 500.0}
    assert result["summary"]["by_tag"] == {"production": 500.0}


@patch("app.reports.generator.generate_pdf")
@patch("app.reports.generator.generate_html")
@patch("app.reports.generator.generate_csv")
@patch("app.reports.generator.get_tag_costs")
@patch("app.reports.generator.get_region_costs")
@patch("app.reports.generator.get_service_costs")
@patch("app.reports.generator.get_cost_summary")
@patch("app.reports.generator.get_settings")
def test_generate_reports_tag_failure_fallback(
    mock_settings: MagicMock,
    mock_summary: MagicMock,
    mock_service: MagicMock,
    mock_region: MagicMock,
    mock_tag: MagicMock,
    mock_csv: MagicMock,
    mock_html: MagicMock,
    mock_pdf: MagicMock,
    tmp_path: Path,
) -> None:
    mock_settings.return_value.report_output_dir = tmp_path
    mock_summary.return_value = {"current_total": 100.0}
    mock_service.return_value = pd.DataFrame()
    mock_region.return_value = pd.DataFrame()

    mock_tag.side_effect = Exception("AWS Tag Error")

    result = generate_reports("monthly")

    assert result["summary"]["by_tag"] == {}
