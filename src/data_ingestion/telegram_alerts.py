"""Telegram alerts for data ingestion errors."""

from typing import Optional
import httpx
import structlog
from .config import config
from .exceptions import TelegramAlertError

logger = structlog.get_logger(__name__)


class TelegramAlerts:
    """Send alerts to Telegram."""
    
    def __init__(self):
        """Initialize Telegram alerts."""
        self.enabled = config.telegram_alerts_enabled
        self.bot_token = config.telegram_bot_token
        self.chat_id = config.telegram_chat_id
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
    
    def send_alert(self, message: str, error: Optional[Exception] = None) -> bool:
        """
        Send alert to Telegram.
        
        Args:
            message: Alert message
            error: Optional exception object
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Telegram alerts disabled, skipping alert")
            return False
        
        try:
            full_message = f"🚨 Data Ingestion Alert\n\n{message}"
            if error:
                full_message += f"\n\nError: {str(error)}"
            
            with httpx.Client(timeout=config.http_timeout) as client:
                response = client.post(
                    self.api_url,
                    json={
                        "chat_id": self.chat_id,
                        "text": full_message,
                        "parse_mode": "HTML"
                    }
                )
                response.raise_for_status()
            
            logger.info("Telegram alert sent", message=message[:50])
            return True
        except Exception as e:
            logger.error("Failed to send Telegram alert", error=str(e))
            # Don't raise exception - alerts shouldn't break the main flow
            return False
    
    def send_success(self, data_source: str, records_updated: int) -> bool:
        """
        Send success notification.
        
        Args:
            data_source: Name of data source (e.g., "MSIF 2025")
            records_updated: Number of records updated
            
        Returns:
            True if sent successfully
        """
        message = f"✅ {data_source} updated successfully\n\nRecords updated: {records_updated}"
        return self.send_alert(message)
    
    def send_error(self, data_source: str, error: Exception) -> bool:
        """
        Send error alert.
        
        Args:
            data_source: Name of data source
            error: Exception that occurred
            
        Returns:
            True if sent successfully
        """
        message = f"❌ Failed to update {data_source}"
        return self.send_alert(message, error=error)

