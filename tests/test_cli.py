"""Unit tests for report generation CLI."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.reports.cli import main


@patch("app.reports.cli.generate_reports")
def test_cli_report_generation(mock_generate: MagicMock) -> None:
    mock_generate.return_value = {
        "csv": Path("/tmp/finops_daily.csv"),
        "html": Path("/tmp/finops_daily.html"),
        "pdf": Path("/tmp/finops_daily.pdf"),
        "summary": {"current_total": 100.0},
    }

    with patch("sys.argv", ["cli.py", "--period", "daily"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
