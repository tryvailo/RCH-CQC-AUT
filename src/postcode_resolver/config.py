"""Configuration for postcode resolver module."""

import os
from pathlib import Path
from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        from pydantic import BaseModel as BaseSettings


class PostcodeResolverConfig(BaseSettings):
    """Configuration settings for postcode resolver."""
    
    # Postcodes.io API
    postcodes_io_api: str = "https://api.postcodes.io/postcodes/{postcode}"
    postcodes_io_batch_api: str = "https://api.postcodes.io/postcodes"
    http_timeout: int = 10
    http_max_retries: int = 3
    
    # Cache settings
    cache_type: str = os.getenv("CACHE_TYPE", "sqlite")  # "redis" or "sqlite"
    cache_dir: Path = Path.home() / ".cache" / "postcode_resolver"
    cache_expiry_days: int = 90
    
    # Redis settings (if cache_type == "redis")
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Batch settings
    batch_size: int = 100
    batch_delay_seconds: float = 0.1  # Delay between batch requests
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra environment variables


# Global config instance
config = PostcodeResolverConfig()

