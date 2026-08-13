"""Application configuration via pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import Any, Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve project root dynamically (/home/oluseun/projects/aws-finops-app)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_profile: str | None = None

    # App Environment
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./data/finops.db"

    # Directory Paths
    data_dir: Path = BASE_DIR / "data"
    report_output_dir: Path = BASE_DIR / "data" / "reports"

    # Scheduling
    scheduler_enabled: bool = True
    daily_report_cron: str = "0 8 * * *"
    weekly_report_cron: str = "0 9 * * 1"

    # Notifications
    slack_webhook_url: str | None = None
    slack_channel: str = "#finops-alerts"
    ses_from_email: str | None = None
    ses_to_emails: list[str] = Field(default_factory=list)

    # Financial Thresholds
    budget_alert_threshold: float = 80.0
    anomaly_impact_threshold: float = 50.0

    # Dashboard
    dashboard_title: str = "AWS FinOps Dashboard"
    api_key: str = "change-me-in-production"

    @field_validator("data_dir", "report_output_dir", mode="before")
    @classmethod
    def resolve_relative_paths(cls, v: Any) -> Path:
        """Ensure paths starting with /app or relative paths stay inside BASE_DIR when running locally."""
        if isinstance(v, (str, Path)):
            path_str = str(v)
            # If path was set to /app/..., re-route it to project BASE_DIR
            if path_str.startswith("/app"):
                clean_path = path_str.replace("/app", "").lstrip("/")
                return BASE_DIR / clean_path

            p = Path(v)
            if not p.is_absolute():
                return BASE_DIR / p
            return p
        return BASE_DIR / "data"

    @field_validator("ses_to_emails", mode="before")
    @classmethod
    def parse_emails(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [e.strip() for e in v.split(",") if e.strip()]
        return v

    @model_validator(mode="after")
    def create_required_directories(self) -> Self:
        """Create data and report output directories safely under project root."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.report_output_dir.mkdir(parents=True, exist_ok=True)
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
