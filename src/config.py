"""Application configuration loaded from environment variables."""

import os
from enum import Enum
from typing import Optional
from pydantic_settings import BaseSettings


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class AlertChannel(str, Enum):
    SLACK = "slack"
    EMAIL = "email"
    PAGERDUTY = "pagerduty"
    WEBHOOK = "webhook"
    DASHBOARD = "dashboard"


class Settings(BaseSettings):
    # App
    app_name: str = "SentinelWatch"
    version: str = "1.0.0"
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO
    secret_key: str = "change-me-in-production"

    # Bright Data
    brightdata_api_key: str = ""
    brightdata_username: str = ""
    brightdata_api_base: str = "https://api.brightdata.com"
    brightdata_zone: str = ""
    brightdata_premium_zone: str = ""
    brightdata_browser_ws: str = ""

    # AI/ML API
    aiml_api_key: str = ""
    aiml_api_base: str = "https://api.aimlapi.com"
    aiml_default_model: str = "claude-opus-4-8"

    # Cognee
    cognee_api_key: Optional[str] = None
    cognee_api_base: str = "https://api.cognee.ai/v1"

    # Database
    database_url: str = "postgresql://sentinel:sentinel@localhost:5432/sentinelwatch"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Alerting
    slack_webhook_url: Optional[str] = None
    pagerduty_api_key: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    alert_from_email: str = "sentinel@sentinelwatch.io"

    # Collection cadences (minutes)
    threat_intel_interval_minutes: int = 15
    compliance_interval_minutes: int = 360  # 6 hours
    third_party_interval_minutes: int = 1440  # 24 hours
    brand_monitor_interval_minutes: int = 60

    # Risk thresholds
    critical_risk_threshold: float = 90.0
    high_risk_threshold: float = 70.0
    medium_risk_threshold: float = 40.0
    low_risk_threshold: float = 20.0

    # API server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
