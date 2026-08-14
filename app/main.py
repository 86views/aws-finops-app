"""FastAPI application entrypoint + optional scheduler."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.alerts.anomaly import process_anomalies
from app.alerts.notifier import notify_cost_summary
from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import init_db
from app.reports.generator import generate_reports

logger = structlog.get_logger(__name__)

scheduler = AsyncIOScheduler()


def _parse_cron(expr: str) -> CronTrigger:
    """Convert a standard 5-field cron expression to APScheduler trigger."""
    parts = expr.split()

    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {expr}")

    minute, hour, day, month, day_of_week = parts

    return CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
    )


async def _run_daily_report() -> None:
    """Generate the daily report and send notifications."""
    logger.info("scheduled_daily_report_start")

    try:
        # Generate report
        result = generate_reports(period="daily")

        logger.info(
            "scheduled_daily_report_generated",
            result_keys=list(result.keys()),
        )

        # Extract summary
        summary = result.get("summary")

        if summary:
            logger.info(
                "scheduled_daily_report_summary_found",
                current_total=summary.get("current_total"),
                previous_total=summary.get("previous_total"),
                change_pct=summary.get("change_pct"),
            )

            # Send Slack/email notifications
            slack_result = notify_cost_summary(
                summary,
                period="daily",
            )

            logger.info(
                "scheduled_daily_report_notification_complete",
                slack_result=slack_result,
            )
        else:
            logger.warning(
                "scheduled_daily_report_no_summary",
            )

        # Process cost anomalies
        anomaly_count = process_anomalies()

        logger.info(
            "scheduled_daily_report_complete",
            anomaly_count=anomaly_count,
        )

    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "scheduled_daily_report_failed",
            error=str(exc),
        )


async def _run_weekly_report() -> None:
    """Generate the weekly report and send notifications."""
    logger.info("scheduled_weekly_report_start")

    try:
        # Generate report
        result = generate_reports(period="weekly")

        logger.info(
            "scheduled_weekly_report_generated",
            result_keys=list(result.keys()),
        )

        # Extract summary
        summary = result.get("summary")

        if summary:
            logger.info(
                "scheduled_weekly_report_summary_found",
                current_total=summary.get("current_total"),
                previous_total=summary.get("previous_total"),
                change_pct=summary.get("change_pct"),
            )

            # Send Slack/email notifications
            slack_result = notify_cost_summary(
                summary,
                period="weekly",
            )

            logger.info(
                "scheduled_weekly_report_notification_complete",
                slack_result=slack_result,
            )
        else:
            logger.warning(
                "scheduled_weekly_report_no_summary",
            )

        logger.info(
            "scheduled_weekly_report_complete",
        )

    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "scheduled_weekly_report_failed",
            error=str(exc),
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown lifecycle."""
    setup_logging()

    settings = get_settings()

    await init_db()

    logger.info(
        "app_startup",
        env=settings.app_env,
    )

    if settings.scheduler_enabled:
        scheduler.add_job(
            _run_daily_report,
            trigger=_parse_cron(settings.daily_report_cron),
            id="daily_report",
            replace_existing=True,
        )

        scheduler.add_job(
            _run_weekly_report,
            trigger=_parse_cron(settings.weekly_report_cron),
            id="weekly_report",
            replace_existing=True,
        )

        scheduler.start()

        logger.info(
            "scheduler_started",
            daily_report_cron=settings.daily_report_cron,
            weekly_report_cron=settings.weekly_report_cron,
        )

    yield

    if scheduler.running:
        scheduler.shutdown(wait=False)

    logger.info("app_shutdown")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="AWS FinOps Platform",
        version="1.0.0",
        description="Monitor, analyse and optimise AWS spend",
        lifespan=lifespan,
    )

    app.include_router(router)

    app.mount(
        "/static",
        StaticFiles(directory="app/dashboard/static"),
        name="static",
    )

    return app


app = create_app()


def run() -> None:
    """Run the application with Uvicorn."""
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=not settings.is_production,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
