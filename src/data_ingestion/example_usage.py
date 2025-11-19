"""Example usage of data ingestion module."""

import structlog
from data_ingestion.service import DataIngestionService
from data_ingestion.scheduler import DataIngestionScheduler
from data_ingestion.database import init_database

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger(__name__)


def main():
    """Main example function."""
    logger.info("Initializing data ingestion module")
    
    # Initialize database tables
    logger.info("Initializing database tables")
    init_database()
    
    # Create service
    service = DataIngestionService()
    
    # Example 1: Refresh MSIF 2025 data (Excel with CSV fallback)
    logger.info("Refreshing MSIF 2025 data")
    result = service.refresh_msif_data(year=2025)
    logger.info("MSIF 2025 refresh result", result=result)
    
    # Example 1b: Refresh MSIF 2025 data using CSV (faster, for development)
    logger.info("Refreshing MSIF 2025 data from CSV")
    result = service.refresh_msif_data(year=2025, prefer_csv=True)
    logger.info("MSIF 2025 CSV refresh result", result=result)
    
    # Example 2: Refresh Lottie data
    logger.info("Refreshing Lottie data")
    result = service.refresh_lottie_data()
    logger.info("Lottie refresh result", result=result)
    
    # Example 3: Get update status
    logger.info("Getting update status")
    updates = service.get_update_status()
    logger.info("Update status", count=len(updates))
    
    # Example 4: Start scheduler (for production)
    # scheduler = DataIngestionScheduler()
    # scheduler.start()
    # logger.info("Scheduler started")
    
    logger.info("Example completed")


if __name__ == "__main__":
    main()

