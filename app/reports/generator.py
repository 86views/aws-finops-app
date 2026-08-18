"""Report generation – CSV, HTML, PDF via Pandas + Jinja2 + WeasyPrint."""

from __future__ import annotations

import csv
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.alerts.notifier import notify_cost_summary
from app.core.config import get_settings
from app.core.cost_explorer import (
    get_cost_summary,
    get_region_costs,
    get_service_costs,
    get_tag_costs,
)

logger = structlog.get_logger(__name__)

Period = Literal["daily", "weekly", "monthly"]


def _period_dates(period: Period) -> tuple[date, date]:
    end = date.today()
    if period == "daily":
        start = end - timedelta(days=1)
    elif period == "weekly":
        start = end - timedelta(days=7)
    else:
        start = end - timedelta(days=30)
    return start, end


def _jinja_env() -> Environment:
    template_dir = Path(__file__).resolve().parent.parent / "dashboard" / "templates"
    return Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )


def generate_csv(summary: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Period Start", summary["start"]])
        writer.writerow(["Period End", summary["end"]])
        writer.writerow(["Current Total (USD)", summary["current_total"]])
        writer.writerow(["Previous Total (USD)", summary["previous_total"]])
        writer.writerow(["Change %", summary["change_pct"]])
        writer.writerow([])
        writer.writerow(["Service", "Amount (USD)"])
        for item in summary.get("top_services", []):
            writer.writerow([item["service"], item["amount"]])
        writer.writerow([])
        writer.writerow(["Forecast Date", "Predicted Amount (USD)"])
        for f in summary.get("forecast", []):
            writer.writerow([f["date"], f["predicted_amount"]])
    logger.info("csv_report_written", path=str(output_path))
    return output_path


def generate_html(summary: dict[str, Any], period: Period, output_path: Path) -> Path:
    env = _jinja_env()
    template = env.get_template("report.html")
    html = template.render(
        title=f"AWS FinOps {period.capitalize()} Report",
        summary=summary,
        period=period,
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    logger.info("html_report_written", path=str(output_path))
    return output_path


def generate_pdf(html_path: Path, output_path: Path) -> Path:
    try:
        from weasyprint import HTML
    except ImportError:
        logger.warning("weasyprint_not_available", msg="Skipping PDF generation")
        return output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(filename=str(html_path)).write_pdf(str(output_path))
    logger.info("pdf_report_written", path=str(output_path))
    return output_path


def generate_reports(period: Period = "daily") -> dict[str, Any]:
    """Generate CSV + HTML + PDF for the given period and return paths."""
    settings = get_settings()
    start, end = _period_dates(period)
    days = (end - start).days or 1

    summary = get_cost_summary(days=days)
    # enrich with extra breakdowns
    service_df = get_service_costs(start, end)
    region_df = get_region_costs(start, end)
    try:
        tag_df = get_tag_costs(start, end, tag_key="Environment")
        summary["by_tag"] = (
            tag_df.groupby("environment")["amount"].sum().sort_values(ascending=False).to_dict()
            if not tag_df.empty
            else {}
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("tag_costs_failed", error=str(exc))
        summary["by_tag"] = {}

    summary["by_region"] = (
        region_df.groupby("region")["amount"].sum().sort_values(ascending=False).to_dict()
        if not region_df.empty
        else {}
    )
    summary["by_service_full"] = (
        service_df.groupby("service")["amount"].sum().sort_values(ascending=False).to_dict()
        if not service_df.empty
        else {}
    )

    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    base = settings.report_output_dir / f"finops_{period}_{ts}"

    csv_path = generate_csv(summary, base.with_suffix(".csv"))
    html_path = generate_html(summary, period, base.with_suffix(".html"))
    pdf_path = generate_pdf(html_path, base.with_suffix(".pdf"))

    try:
        notify_cost_summary(summary, period=period)
    except Exception as exc:  # noqa: BLE001
        logger.warning("notify_cost_summary_failed", error=str(exc), period=period)

    return {"csv": csv_path, "html": html_path, "pdf": pdf_path, "summary": summary}
