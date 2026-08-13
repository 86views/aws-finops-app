"""AWS clients – session management with optional profile / role assumption."""

from functools import lru_cache
from typing import Any

import boto3
from botocore.config import Config

from app.core.config import get_settings

_BOTO_CONFIG = Config(
    retries={"max_attempts": 5, "mode": "adaptive"},
    connect_timeout=10,
    read_timeout=60,
)


@lru_cache
def get_session() -> boto3.Session:
    settings = get_settings()
    if settings.aws_profile:
        return boto3.Session(profile_name=settings.aws_profile, region_name=settings.aws_region)
    return boto3.Session(region_name=settings.aws_region)


def get_client(service: str) -> Any:
    # mypy: ignore[call-overload] needed because `service` is a dynamic string
    return get_session().client(service, config=_BOTO_CONFIG)  # type: ignore[call-overload]


def get_ce_client() -> Any:
    """Cost Explorer client (always us-east-1)."""
    return get_session().client("ce", region_name="us-east-1", config=_BOTO_CONFIG)


def get_budgets_client() -> Any:
    return get_client("budgets")


def get_ses_client() -> Any:
    return get_client("ses")


def get_sts_client() -> Any:
    return get_client("sts")


def get_caller_identity() -> dict[str, str]:
    res: dict[str, str] = get_sts_client().get_caller_identity()
    return res
