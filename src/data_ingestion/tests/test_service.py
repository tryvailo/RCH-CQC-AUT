"""Tests for DataIngestionService."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from data_ingestion.service import DataIngestionService
from data_ingestion.exceptions import MSIFDownloadError, LottieScrapingError


@pytest.fixture
def service():
    """Create DataIngestionService instance."""
    return DataIngestionService()


class TestDataIngestionService:
    """Test DataIngestionService class."""
    
    def test_init(self):
        """Test service initialization."""
        service = DataIngestionService()
        assert service.msif_loader is not None
        assert service.lottie_scraper is not None
        assert service.telegram_alerts is not None
    
    def test_refresh_msif_data_success(self, service):
        """Test successful MSIF data refresh."""
        with patch.object(service.msif_loader, 'load_msif_data', return_value=150), \
             patch.object(service, 'log_update_start', return_value=1), \
             patch.object(service, 'log_update_complete'), \
             patch.object(service.telegram_alerts, 'send_success'):
            
            result = service.refresh_msif_data(year=2025)
            
            assert result["status"] == "success"
            assert result["records_updated"] == 150
    
    def test_refresh_msif_data_error(self, service):
        """Test MSIF data refresh with error."""
        error = MSIFDownloadError("Download failed")
        
        with patch.object(service.msif_loader, 'load_msif_data', side_effect=error), \
             patch.object(service, 'log_update_start', return_value=1), \
             patch.object(service, 'log_update_complete'), \
             patch.object(service.telegram_alerts, 'send_error'):
            
            result = service.refresh_msif_data(year=2025)
            
            assert result["status"] == "error"
            assert "error" in result
    
    def test_refresh_lottie_data_success(self, service):
        """Test successful Lottie data refresh."""
        with patch.object(service.lottie_scraper, 'load_lottie_data', return_value=27), \
             patch.object(service, 'log_update_start', return_value=1), \
             patch.object(service, 'log_update_complete'), \
             patch.object(service.telegram_alerts, 'send_success'):
            
            result = service.refresh_lottie_data()
            
            assert result["status"] == "success"
            assert result["records_updated"] == 27
    
    def test_refresh_lottie_data_error(self, service):
        """Test Lottie data refresh with error."""
        error = LottieScrapingError("Scraping failed")
        
        with patch.object(service.lottie_scraper, 'load_lottie_data', side_effect=error), \
             patch.object(service, 'log_update_start', return_value=1), \
             patch.object(service, 'log_update_complete'), \
             patch.object(service.telegram_alerts, 'send_error'):
            
            result = service.refresh_lottie_data()
            
            assert result["status"] == "error"
            assert "error" in result
    
    def test_get_update_status(self, service):
        """Test getting update status."""
        mock_updates = [
            {
                "id": 1,
                "data_source": "MSIF 2025",
                "status": "success",
                "records_updated": 150,
                "error_message": None,
                "started_at": None,
                "completed_at": None,
                "duration_seconds": 10
            }
        ]
        
        with patch('data_ingestion.service.get_db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.description = [
                ("id",), ("data_source",), ("status",), ("records_updated",),
                ("error_message",), ("started_at",), ("completed_at",), ("duration_seconds",)
            ]
            mock_cursor.fetchall.return_value = [(1, "MSIF 2025", "success", 150, None, None, None, 10)]
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value.__enter__.return_value = mock_conn
            
            updates = service.get_update_status()
            
            assert len(updates) == 1
            assert updates[0]["data_source"] == "MSIF 2025"

