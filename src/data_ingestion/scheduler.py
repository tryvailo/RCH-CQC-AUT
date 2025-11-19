"""APScheduler configuration for automatic data updates."""

import structlog
from .config import config
from .service import DataIngestionService

logger = structlog.get_logger(__name__)

# Lazy import apscheduler to avoid import errors if not installed
_BackgroundScheduler = None
_IntervalTrigger = None

def _get_apscheduler():
    """Lazy import apscheduler."""
    global _BackgroundScheduler, _IntervalTrigger
    if _BackgroundScheduler is None:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.interval import IntervalTrigger
            _BackgroundScheduler = BackgroundScheduler
            _IntervalTrigger = IntervalTrigger
        except ImportError:
            raise ImportError(
                "apscheduler is not installed. Install it with: pip install apscheduler"
            )
    return _BackgroundScheduler, _IntervalTrigger


class DataIngestionScheduler:
    """Scheduler for automatic data ingestion updates."""
    
    def __init__(self):
        """Initialize scheduler."""
        BackgroundScheduler, IntervalTrigger = _get_apscheduler()
        self.scheduler = BackgroundScheduler()
        self.service = DataIngestionService()
        self.enabled = config.scheduler_enabled
    
    def _refresh_msif_2025(self):
        """Refresh MSIF 2025-2026 data."""
        logger.info("Scheduled refresh: MSIF 2025")
        self.service.refresh_msif_data(year=2025)
    
    def _refresh_msif_2024(self):
        """Refresh MSIF 2024-2025 data."""
        logger.info("Scheduled refresh: MSIF 2024")
        self.service.refresh_msif_data(year=2024)
    
    def _refresh_lottie(self):
        """Refresh Lottie regional averages."""
        logger.info("Scheduled refresh: Lottie")
        self.service.refresh_lottie_data()
    
    def start(self):
        """Start the scheduler."""
        if not self.enabled:
            logger.info("Scheduler disabled in config")
            return
        
        _, IntervalTrigger = _get_apscheduler()
        
        # Add jobs
        self.scheduler.add_job(
            func=self._refresh_msif_2025,
            trigger=IntervalTrigger(days=config.scheduler_interval_days),
            id='refresh_msif_2025',
            name='Refresh MSIF 2025-2026',
            replace_existing=True
        )
        
        self.scheduler.add_job(
            func=self._refresh_msif_2024,
            trigger=IntervalTrigger(days=config.scheduler_interval_days),
            id='refresh_msif_2024',
            name='Refresh MSIF 2024-2025',
            replace_existing=True
        )
        
        self.scheduler.add_job(
            func=self._refresh_lottie,
            trigger=IntervalTrigger(days=config.scheduler_interval_days),
            id='refresh_lottie',
            name='Refresh Lottie Regional Averages',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(
            "Data ingestion scheduler started",
            interval_days=config.scheduler_interval_days,
            jobs=len(self.scheduler.get_jobs())
        )
    
    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Data ingestion scheduler stopped")
    
    def get_jobs(self):
        """Get list of scheduled jobs."""
        return self.scheduler.get_jobs()

