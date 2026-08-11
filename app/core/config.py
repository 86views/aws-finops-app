"""Application configuration via pydantic-settings (2026 best practice)."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # AWS
    aws_region: str = "us-east-1"
    aws_profile: str | None = None

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./data/finops.db"
    report_output_dir: Path = Path("./data/reports")
    scheduler_enabled: bool = True
    daily_report_cron: str = "0 8 * * *"
    weekly_report_cron: str = "0 9 * * 1"

    # Slack
    slack_webhook_url: str | None = None
    slack_channel: str = "#finops-alerts"

    # SES
    ses_from_email: str | None = None
    ses_to_emails: list[str] = Field(default_factory=list)

    # Thresholds
    budget_alert_threshold: float = 80.0  # % of budget
    anomaly_impact_threshold: float = 50.0  # USD

    # Dashboard
    dashboard_title: str = "AWS FinOps Dashboard"
    api_key: str = "change-me-in-production"

    @field_validator("ses_to_emails", mode="before")
    @classmethod
    def parse_emails(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [e.strip() for e in v.split(",") if e.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    def ensure_dirs(self) -> None:
        self.report_output_dir.mkdir(parents=True, exist_ok=True)
        Path("./data").mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
