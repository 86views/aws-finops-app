"""FastAPI routes for the FinOps dashboard & API."""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
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

if TYPE_CHECKING:
    from starlette.requests import Request

router = APIRouter()
templates = Jinja2Templates(directory="app/dashboard/templates")


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if settings.is_production and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "aws-finops"}


@router.get("/api/summary")
async def api_summary(
    days: int = Query(30, ge=1, le=90),
    _: None = Depends(verify_api_key),
) -> dict[str, Any]:
    return get_cost_summary(days=days)


@router.get("/api/services")
async def api_services(
    days: int = Query(30, ge=1, le=90),
    _: None = Depends(verify_api_key),
) -> list[dict[str, Any]]:
    end = date.today()
    start = end - timedelta(days=days)
    df = get_service_costs(start, end)
    if df.empty:
        return []
    grouped = df.groupby("service")["amount"].sum().sort_values(ascending=False)
    return [{"service": k, "amount": round(float(v), 2)} for k, v in grouped.items()]


@router.get("/api/regions")
async def api_regions(
    days: int = Query(30, ge=1, le=90),
    _: None = Depends(verify_api_key),
) -> list[dict[str, Any]]:
    end = date.today()
    start = end - timedelta(days=days)
    df = get_region_costs(start, end)
    if df.empty:
        return []
    grouped = df.groupby("region")["amount"].sum().sort_values(ascending=False)
    return [{"region": k, "amount": round(float(v), 2)} for k, v in grouped.items()]


@router.get("/api/tags")
async def api_tags(
    tag_key: str = Query("Environment"),
    days: int = Query(30, ge=1, le=90),
    _: None = Depends(verify_api_key),
) -> list[dict[str, Any]]:
    end = date.today()
    start = end - timedelta(days=days)
    try:
        df = get_tag_costs(start, end, tag_key=tag_key)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if df.empty:
        return []
    col = tag_key.lower()
    grouped = df.groupby(col)["amount"].sum().sort_values(ascending=False)
    return [{col: k, "amount": round(float(v), 2)} for k, v in grouped.items()]


@router.get("/api/anomalies")
async def api_anomalies(
    days: int = Query(14, ge=1, le=90),
    _: None = Depends(verify_api_key),
) -> list[dict[str, Any]]:
    return get_anomalies(days=days)


@router.post("/api/reports/{period}")
async def api_generate_report(
    period: str,
    _: None = Depends(verify_api_key),
) -> dict[str, Any]:
    if period not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="period must be daily|weekly|monthly")
    result = generate_reports(period=period)  # type: ignore[arg-type]
    return {
        "csv": str(result["csv"]),
        "html": str(result["html"]),
        "pdf": str(result["pdf"]),
        "summary": result.get("summary"),
    }


@router.post("/api/alerts/anomalies")
async def api_process_anomalies(_: None = Depends(verify_api_key)) -> dict[str, int]:
    count = process_anomalies()
    return {"notified": count}


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    settings = get_settings()
    summary = get_cost_summary(days=30)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "title": settings.dashboard_title,
            "summary": summary,
            "summary_json": json.dumps(summary, default=str),
        },
    )
