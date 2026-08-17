"""Cost Explorer integration – fetch, aggregate, and analyse AWS costs."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

import pandas as pd
import structlog

from app.core.aws import get_ce_client

logger = structlog.get_logger(__name__)


def _date_str(value: date) -> str:
    return value.isoformat()


def get_cost_and_usage(
    start: date,
    end: date,
    granularity: str = "DAILY",
    group_by: list[dict[str, str]] | None = None,
    metrics: list[str] | None = None,
    filter_expr: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch AWS Cost & Usage data from Cost Explorer.

    Examples:

        [{"Type": "DIMENSION", "Key": "SERVICE"}]

        [{"Type": "DIMENSION", "Key": "REGION"}]

        [{"Type": "TAG", "Key": "Environment"}]
    """
    ce = get_ce_client()

    metrics = metrics or ["NetUnblendedCost"]
    group_by = group_by or [{"Type": "DIMENSION", "Key": "SERVICE"}]

    results: list[dict[str, Any]] = []
    next_token: str | None = None

    while True:
        params: dict[str, Any] = {
            "TimePeriod": {
                "Start": _date_str(start),
                "End": _date_str(end),
            },
            "Granularity": granularity,
            "Metrics": metrics,
            "GroupBy": group_by,
        }

        if filter_expr:
            params["Filter"] = filter_expr

        if next_token:
            params["NextPageToken"] = next_token

        response = ce.get_cost_and_usage(**params)

        results.extend(response.get("ResultsByTime", []))

        next_token = response.get("NextPageToken")

        if not next_token:
            break

    return results


def results_to_dataframe(
    results: list[dict[str, Any]],
    group_key: str = "SERVICE",
) -> pd.DataFrame:
    """Flatten Cost Explorer ResultsByTime into a tidy DataFrame."""
    rows: list[dict[str, Any]] = []

    for period in results:
        start = period["TimePeriod"]["Start"]

        # Grouped results, e.g. Amazon EC2, Amazon S3, etc.
        for group in period.get("Groups", []):
            keys = group.get("Keys", ["Unknown"])
            metric = group.get("Metrics", {}).get("NetUnblendedCost", {})

            amount = float(metric.get("Amount", 0.0))
            unit = metric.get("Unit", "USD")

            rows.append(
                {
                    "date": start,
                    group_key.lower(): keys[0] if keys else "Unknown",
                    "amount": amount,
                    "unit": unit,
                }
            )

        # Cost Explorer total for the period
        total = period.get("Total")
        if total:
            metric = total.get("NetUnblendedCost", {})

            rows.append(
                {
                    "date": start,
                    group_key.lower(): "_TOTAL_",
                    "amount": float(metric.get("Amount", 0.0)),
                    "unit": metric.get("Unit", "USD"),
                }
            )

    df = pd.DataFrame(rows)

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])

    return df


def get_service_costs(
    start: date,
    end: date,
    granularity: str = "DAILY",
) -> pd.DataFrame:
    results = get_cost_and_usage(
        start,
        end,
        granularity=granularity,
        group_by=[
            {
                "Type": "DIMENSION",
                "Key": "SERVICE",
            }
        ],
    )

    return results_to_dataframe(results, "SERVICE")


def get_tag_costs(
    start: date,
    end: date,
    tag_key: str = "Environment",
    granularity: str = "MONTHLY",
) -> pd.DataFrame:
    results = get_cost_and_usage(
        start,
        end,
        granularity=granularity,
        group_by=[
            {
                "Type": "TAG",
                "Key": tag_key,
            }
        ],
    )

    return results_to_dataframe(results, tag_key)


def get_region_costs(
    start: date,
    end: date,
    granularity: str = "MONTHLY",
) -> pd.DataFrame:
    results = get_cost_and_usage(
        start,
        end,
        granularity=granularity,
        group_by=[
            {
                "Type": "DIMENSION",
                "Key": "REGION",
            }
        ],
    )

    return results_to_dataframe(results, "REGION")


def get_account_costs(
    start: date,
    end: date,
    granularity: str = "MONTHLY",
) -> pd.DataFrame:
    results = get_cost_and_usage(
        start,
        end,
        granularity=granularity,
        group_by=[
            {
                "Type": "DIMENSION",
                "Key": "LINKED_ACCOUNT",
            }
        ],
    )

    return results_to_dataframe(results, "LINKED_ACCOUNT")


def compute_mom_trend(
    df: pd.DataFrame,
) -> dict[str, Any]:
    """Calculate month-over-month total cost trend."""

    if df.empty:
        return {
            "current": 0.0,
            "previous": 0.0,
            "change_pct": 0.0,
            "change_abs": 0.0,
        }

    monthly = df.groupby(df["date"].dt.to_period("M"))["amount"].sum().sort_index()

    if monthly.empty:
        return {
            "current": 0.0,
            "previous": 0.0,
            "change_pct": 0.0,
            "change_abs": 0.0,
        }

    if len(monthly) < 2:
        current = float(monthly.iloc[-1])

        return {
            "current": round(current, 2),
            "previous": 0.0,
            "change_pct": 0.0,
            "change_abs": 0.0,
        }

    current = float(monthly.iloc[-1])
    previous = float(monthly.iloc[-2])

    change_abs = current - previous

    change_pct = (change_abs / previous) * 100 if previous else 0.0

    return {
        "current": round(current, 2),
        "previous": round(previous, 2),
        "change_pct": round(change_pct, 2),
        "change_abs": round(change_abs, 2),
    }


def simple_forecast(
    df: pd.DataFrame,
    periods: int = 3,
) -> list[dict[str, Any]]:
    """
    Simple linear forecast based on daily AWS costs.

    This is a baseline forecast, not an AWS Forecast prediction.
    """

    if df.empty:
        return []

    daily = df.groupby("date")["amount"].sum().sort_index()

    if len(daily) < 7:
        return []

    recent = daily.tail(30)

    x = list(range(len(recent)))
    y = recent.values.tolist()

    n = len(x)

    sum_x = sum(x)
    sum_y = sum(y)

    sum_xy = sum(a * b for a, b in zip(x, y, strict=True))

    sum_x2 = sum(a * a for a in x)

    denominator = n * sum_x2 - sum_x * sum_x

    if denominator == 0:
        return []

    slope = (n * sum_xy - sum_x * sum_y) / denominator

    intercept = (sum_y - slope * sum_x) / n

    last_date = recent.index[-1]

    forecasts: list[dict[str, Any]] = []

    for i in range(1, periods + 1):
        predicted = intercept + slope * (n - 1 + i)

        forecasts.append(
            {
                "date": (last_date + timedelta(days=i)).strftime("%Y-%m-%d"),
                "predicted_amount": round(
                    max(0.0, float(predicted)),
                    2,
                ),
            }
        )

    return forecasts


def get_cost_summary(
    days: int = 30,
) -> dict[str, Any]:
    """Generate the high-level dashboard cost summary."""

    end = date.today()
    start = end - timedelta(days=days)

    previous_end = start
    previous_start = previous_end - timedelta(days=days)

    current_df = get_service_costs(
        start,
        end,
        granularity="DAILY",
    )

    previous_df = get_service_costs(
        previous_start,
        previous_end,
        granularity="DAILY",
    )

    current_total = float(current_df["amount"].sum()) if not current_df.empty else 0.0

    previous_total = float(previous_df["amount"].sum()) if not previous_df.empty else 0.0

    change_pct = (
        ((current_total - previous_total) / previous_total) * 100 if previous_total else 0.0
    )

    by_service = (
        current_df.groupby("service")["amount"].sum().sort_values(ascending=False).head(15)
        if not current_df.empty
        else pd.Series(dtype=float)
    )

    mom = compute_mom_trend(current_df)

    forecast = simple_forecast(
        current_df,
        periods=3,
    )

    return {
        "period_days": days,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "current_total": round(
            current_total,
            2,
        ),
        "previous_total": round(
            previous_total,
            2,
        ),
        "change_pct": round(
            change_pct,
            2,
        ),
        "top_services": [
            {
                "service": service,
                "amount": round(
                    float(amount),
                    2,
                ),
            }
            for service, amount in by_service.items()
        ],
        "mom": mom,
        "forecast": forecast,
        "generated_at": datetime.now(UTC).isoformat(),
    }
