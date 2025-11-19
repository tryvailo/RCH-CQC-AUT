"""Configuration for data ingestion module."""

import os
from pathlib import Path
from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        # Fallback for pydantic v2
        from pydantic import BaseSettings
    except ImportError:
        # Fallback for older versions
        from pydantic import BaseModel as BaseSettings


class DataIngestionConfig(BaseSettings):
    """Configuration settings for data ingestion."""
    
    # Database
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "care_homes")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "")
    
    # MSIF URLs
    msif_2025_url: str = (
        "https://assets.publishing.service.gov.uk/media/"
        "68a3021cf49bec79d23d2940/market-sustainability-and-improvement-fund-fees-2025-to-2026.xlsx"
    )
    msif_2024_url: str = (
        "https://assets.publishing.service.gov.uk/media/"
        "6703d7cc3b919067bb482d39/market-sustainability-and-improvement-fund-fees-2024-to-2025.xlsx"
    )
    
    # Lottie URLs
    lottie_residential_url: str = "https://www.lottie.org/care-home-costs/residential-care-costs/"
    lottie_nursing_url: str = "https://www.lottie.org/care-home-costs/nursing-care-costs/"
    lottie_dementia_url: str = "https://www.lottie.org/care-home-costs/dementia-care-costs/"
    
    # Cache directory
    cache_dir: Path = Path.home() / ".cache" / "data_ingestion"
    
    # Scheduler
    scheduler_enabled: bool = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
    scheduler_interval_days: int = 7
    
    # Telegram alerts
    telegram_bot_token: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
    telegram_alerts_enabled: bool = (
        os.getenv("TELEGRAM_ALERTS_ENABLED", "false").lower() == "true"
        and telegram_bot_token is not None
        and telegram_chat_id is not None
    )
    
    # HTTP client settings
    http_timeout: int = 30
    http_max_retries: int = 3
    
    # MSIF data source preferences
    msif_prefer_csv: bool = os.getenv("MSIF_PREFER_CSV", "false").lower() == "true"
    msif_fallback_to_csv: bool = os.getenv("MSIF_FALLBACK_TO_CSV", "true").lower() == "true"
    msif_csv_path: Optional[str] = os.getenv("MSIF_CSV_PATH")  # Optional custom CSV path
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra environment variables


# Global config instance
config = DataIngestionConfig()

