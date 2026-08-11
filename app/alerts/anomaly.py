"""Fetch and process AWS Cost Anomaly Detection results."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import structlog

from app.alerts.notifier import notify_anomaly
from app.core.aws import get_ce_client
from app.core.config import get_settings

logger = structlog.get_logger(__name__)


def get_anomalies(days: int = 14) -> list[dict[str, Any]]:
    """List recent cost anomalies from Cost Explorer Anomaly Detection."""
    ce = get_ce_client()
    end = date.today()
    start = end - timedelta(days=days)

    try:
        response = ce.get_anomalies(
            DateInterval={"StartDate": start.isoformat(), "EndDate": end.isoformat()},
            MaxResults=20,
        )
        return response.get("Anomalies", [])
    except Exception as exc:  # noqa: BLE001
        logger.warning("get_anomalies_failed", error=str(exc))
        return []


def process_anomalies() -> int:
    """Fetch recent anomalies and notify if impact exceeds threshold."""
    settings = get_settings()
    anomalies = get_anomalies()
    notified = 0
    for anomaly in anomalies:
        impact = float(anomaly.get("Impact", {}).get("TotalImpact", 0) or 0)
        if impact >= settings.anomaly_impact_threshold:
            notify_anomaly(anomaly)
            notified += 1
    logger.info("anomalies_processed", total=len(anomalies), notified=notified)
    return notified
