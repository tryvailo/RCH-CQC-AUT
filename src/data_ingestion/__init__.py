"""Data ingestion module for RightCareHome."""

from .service import DataIngestionService
from .config import config

# Lazy import scheduler to avoid import errors if apscheduler is not installed
try:
    from .scheduler import DataIngestionScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    DataIngestionScheduler = None

__all__ = [
    "DataIngestionService",
    "config",
]

if SCHEDULER_AVAILABLE:
    __all__.append("DataIngestionScheduler")

