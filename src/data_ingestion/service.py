"""Main service for data ingestion."""

from datetime import datetime
from typing import Optional
import structlog
from .msif_loader import MSIFLoader
from .lottie_scraper import LottieScraper
from .telegram_alerts import TelegramAlerts
from .database import get_db_connection
from .exceptions import DataIngestionError

logger = structlog.get_logger(__name__)


class DataIngestionService:
    """Main service for data ingestion operations."""
    
    def __init__(self):
        """Initialize data ingestion service."""
        self.msif_loader = MSIFLoader()
        self.lottie_scraper = LottieScraper()
        self.telegram_alerts = TelegramAlerts()
    
    def log_update_start(self, data_source: str) -> int:
        """
        Log start of data update.
        
        Args:
            data_source: Name of data source
            
        Returns:
            Log entry ID
            
        Note:
            If database is not available, returns None and continues without logging.
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO data_update_log (data_source, status, started_at)
                    VALUES (%s, 'running', CURRENT_TIMESTAMP)
                    RETURNING id
                """, (data_source,))
                log_id = cursor.fetchone()[0]
                conn.commit()
                return log_id
        except Exception as e:
            logger.warning("Could not log update start to database", error=str(e), data_source=data_source)
            return None
    
    def log_update_complete(self, log_id: Optional[int], records_updated: int, error: Optional[str] = None) -> None:
        """
        Log completion of data update.
        
        Args:
            log_id: Log entry ID (can be None if logging failed)
            records_updated: Number of records updated
            error: Optional error message
            
        Note:
            If database is not available, silently continues without logging.
        """
        if log_id is None:
            return
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE data_update_log
                    SET status = %s,
                        records_updated = %s,
                        error_message = %s,
                        completed_at = CURRENT_TIMESTAMP,
                        duration_seconds = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at))::INTEGER
                    WHERE id = %s
                """, ('success' if not error else 'failed', records_updated, error, log_id))
                conn.commit()
        except Exception as e:
            logger.warning("Could not log update complete to database", error=str(e), log_id=log_id)
    
    def refresh_msif_data(
        self, 
        year: int = 2025,
        prefer_csv: Optional[bool] = None,
        csv_path: Optional[str] = None
    ) -> dict:
        """
        Refresh MSIF data for a given year.
        
        Args:
            year: Year (2024 or 2025)
            prefer_csv: If True, try CSV first. If None, uses config default
            csv_path: Optional path to CSV file. If None, uses default from input/other
            
        Returns:
            Dict with status and details
        """
        from .config import config
        from pathlib import Path
        
        data_source = f"MSIF {year}"
        log_id = None
        
        try:
            log_id = self.log_update_start(data_source)
            logger.info("Refreshing MSIF data", year=year, prefer_csv=prefer_csv)
            
            # Use config defaults if not specified
            if prefer_csv is None:
                prefer_csv = config.msif_prefer_csv
            
            csv_path_obj = None
            if csv_path:
                csv_path_obj = Path(csv_path)
            
            records_updated = self.msif_loader.load_msif_data(
                year=year,
                prefer_csv=prefer_csv,
                csv_path=csv_path_obj,
                fallback_to_csv=config.msif_fallback_to_csv
            )
            
            self.log_update_complete(log_id, records_updated)
            try:
                self.telegram_alerts.send_success(data_source, records_updated)
            except Exception as e:
                logger.warning("Could not send Telegram alert", error=str(e))
            
            result = {
                "status": "success",
                "data_source": data_source,
                "records_updated": records_updated,
                "source": "csv" if prefer_csv else "excel"
            }
            
            # Add warning if records_updated is 0 but operation succeeded
            if records_updated == 0:
                result["warning"] = (
                    "Data was parsed successfully but not saved to database. "
                    "Possible reasons: "
                    "1) psycopg2 not installed (install with: pip install psycopg2-binary), "
                    "2) Database unavailable, "
                    "3) Database connection error. "
                    "Check server logs for details."
                )
                logger.warning("MSIF refresh completed with 0 records saved", year=year, **result)
            
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error("Failed to refresh MSIF data", year=year, error=error_msg)
            
            if log_id:
                self.log_update_complete(log_id, 0, error=error_msg)
            
            self.telegram_alerts.send_error(data_source, e)
            
            return {
                "status": "error",
                "data_source": data_source,
                "error": error_msg
            }
    
    def refresh_lottie_data(self, use_fallback: bool = True) -> dict:
        """
        Refresh Lottie regional averages.
        
        Args:
            use_fallback: If True, use fallback constants data if scraping fails
        
        Returns:
            Dict with status and details
        """
        data_source = "Lottie Regional Averages"
        log_id = None
        
        try:
            log_id = self.log_update_start(data_source)
            logger.info("Refreshing Lottie data", use_fallback=use_fallback)
            
            records_updated = self.lottie_scraper.load_lottie_data(use_fallback=use_fallback)
            
            self.log_update_complete(log_id, records_updated)
            try:
                self.telegram_alerts.send_success(data_source, records_updated)
            except Exception as e:
                logger.warning("Could not send Telegram alert", error=str(e))
            
            result = {
                "status": "success",
                "data_source": data_source,
                "records_updated": records_updated
            }
            
            # Add info if fallback was used
            if records_updated > 0:
                result["source"] = "scraped" if records_updated > 0 else "fallback"
            
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error("Failed to refresh Lottie data", error=error_msg)
            
            if log_id:
                self.log_update_complete(log_id, 0, error=error_msg)
            
            try:
                self.telegram_alerts.send_error(data_source, e)
            except Exception as alert_error:
                logger.warning("Could not send Telegram error alert", error=str(alert_error))
            
            result = {
                "status": "error",
                "data_source": data_source,
                "error": error_msg
            }
            
            # Add helpful message about fallback
            if use_fallback:
                result["hint"] = (
                    "Scraping failed, but system can still work using fallback constants data. "
                    "The pricing calculator will use hardcoded Lottie averages from constants.py."
                )
            
            return result
    
    def get_update_status(self) -> list:
        """
        Get status of recent data updates.
        
        Returns:
            List of update log entries
            
        Note:
            Returns empty list if database is not available.
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        id,
                        data_source,
                        status,
                        records_updated,
                        error_message,
                        started_at,
                        completed_at,
                        duration_seconds
                    FROM data_update_log
                    ORDER BY started_at DESC
                    LIMIT 50
                """)
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    result = dict(zip(columns, row))
                    results.append(result)
                
                return results
        except Exception as e:
            logger.warning("Could not get update status from database", error=str(e))
            return []

