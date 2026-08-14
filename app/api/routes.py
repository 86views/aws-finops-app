"""FastAPI routes for the FinOps dashboard & API."""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.alerts.anomaly import get_anomalies, process_anomalies
from app.core.config import get_settings
from app.core.cost_explorer import (
    get_cost_summary,
    get_region_costs,
    get_service_costs,
    get_tag_costs,
)
from app.reports.generator import generate_reports

router = APIRouter()

templates = Jinja2Templates(directory="app/dashboard/templates")


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Verify API key when running in production."""
    settings = get_settings()

    if settings.is_production and x_api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
        )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "aws-finops",
    }


# ---------------------------------------------------------------------------
# Cost Summary API
# ---------------------------------------------------------------------------


@router.get("/api/summary")
async def api_summary(
    days: int = Query(30, ge=1, le=90),
    _: None = Depends(verify_api_key),
) -> dict[str, Any]:
    """Return AWS cost summary."""
    return get_cost_summary(days=days)


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


@router.get("/api/services")
async def api_services(
    days: int = Query(30, ge=1, le=90),
    _: None = Depends(verify_api_key),
) -> list[dict[str, Any]]:
    """Return AWS costs grouped by service."""
    end = date.today()
    start = end - timedelta(days=days)

    df = get_service_costs(start, end)

    if df.empty:
        return []

    grouped = df.groupby("service")["amount"].sum().sort_values(ascending=False)

    return [
        {
            "service": service,
            "amount": round(float(amount), 2),
        }
        for service, amount in grouped.items()
    ]


# ---------------------------------------------------------------------------
# Regions
# ---------------------------------------------------------------------------


@router.get("/api/regions")
async def api_regions(
    days: int = Query(30, ge=1, le=90),
    _: None = Depends(verify_api_key),
) -> list[dict[str, Any]]:
    """Return AWS costs grouped by region."""
    end = date.today()
    start = end - timedelta(days=days)

    df = get_region_costs(start, end)

    if df.empty:
        return []

    grouped = df.groupby("region")["amount"].sum().sort_values(ascending=False)

    return [
        {
            "region": region,
            "amount": round(float(amount), 2),
        }
        for region, amount in grouped.items()
    ]


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


@router.get("/api/tags")
async def api_tags(
    tag_key: str = Query("Environment"),
    days: int = Query(30, ge=1, le=90),
    _: None = Depends(verify_api_key),
) -> list[dict[str, Any]]:
    """Return AWS costs grouped by tag."""
    end = date.today()
    start = end - timedelta(days=days)

    try:
        df = get_tag_costs(
            start,
            end,
            tag_key=tag_key,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    if df.empty:
        return []

    col = tag_key.lower()

    grouped = df.groupby(col)["amount"].sum().sort_values(ascending=False)

    return [
        {
            col: value,
            "amount": round(float(amount), 2),
        }
        for value, amount in grouped.items()
    ]


# ---------------------------------------------------------------------------
# Anomalies
# ---------------------------------------------------------------------------


@router.get("/api/anomalies")
async def api_anomalies(
    days: int = Query(14, ge=1, le=90),
    _: None = Depends(verify_api_key),
) -> list[dict[str, Any]]:
    """Return AWS cost anomalies."""
    return get_anomalies(days=days)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


@router.post("/api/reports/{period}")
async def api_generate_report(
    period: str,
    _: None = Depends(verify_api_key),
) -> dict[str, Any]:
    """Generate a FinOps report."""
    if period not in ("daily", "weekly", "monthly"):
        raise HTTPException(
            status_code=400,
            detail="period must be daily|weekly|monthly",
        )

    result = generate_reports(period=period)  # type: ignore[arg-type]

    return {
        "csv": str(result["csv"]),
        "html": str(result["html"]),
        "pdf": str(result["pdf"]),
        "summary": result.get("summary"),
    }


# ---------------------------------------------------------------------------
# Anomaly Alerts
# ---------------------------------------------------------------------------


@router.post("/api/alerts/anomalies")
async def api_process_anomalies(
    _: None = Depends(verify_api_key),
) -> dict[str, int]:
    """Process and notify about AWS cost anomalies."""
    count = process_anomalies()

    return {
        "notified": count,
    }


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """Render the FinOps dashboard."""
    settings = get_settings()

    summary = get_cost_summary(days=30)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "title": settings.dashboard_title,
            "summary": summary,
            "summary_json": json.dumps(
                summary,
                default=str,
            ),
        },
    )
