"""Tests for Telegram alerts."""

import pytest
from unittest.mock import Mock, patch
import httpx
from data_ingestion.telegram_alerts import TelegramAlerts
from data_ingestion.config import config


@pytest.fixture
def telegram_alerts():
    """Create TelegramAlerts instance."""
    return TelegramAlerts()


class TestTelegramAlerts:
    """Test TelegramAlerts class."""
    
    def test_send_alert_disabled(self, telegram_alerts):
        """Test sending alert when disabled."""
        with patch.object(telegram_alerts, 'enabled', False):
            result = telegram_alerts.send_alert("Test message")
            assert result is False
    
    def test_send_alert_success(self, telegram_alerts):
        """Test successful alert sending."""
        with patch.object(telegram_alerts, 'enabled', True), \
             patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_client.return_value.__enter__.return_value.post.return_value = mock_response
            
            result = telegram_alerts.send_alert("Test message")
            
            assert result is True
            assert mock_client.return_value.__enter__.return_value.post.called
    
    def test_send_alert_error(self, telegram_alerts):
        """Test alert sending with error."""
        with patch.object(telegram_alerts, 'enabled', True), \
             patch('httpx.Client') as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPError("HTTP 400")
            mock_client.return_value.__enter__.return_value.post.return_value = mock_response
            
            result = telegram_alerts.send_alert("Test message")
            
            assert result is False
    
    def test_send_success(self, telegram_alerts):
        """Test sending success notification."""
        with patch.object(telegram_alerts, 'send_alert', return_value=True) as mock_send:
            result = telegram_alerts.send_success("MSIF 2025", 150)
            
            assert result is True
            assert mock_send.called
    
    def test_send_error(self, telegram_alerts):
        """Test sending error alert."""
        error = Exception("Test error")
        
        with patch.object(telegram_alerts, 'send_alert', return_value=True) as mock_send:
            result = telegram_alerts.send_error("MSIF 2025", error)
            
            assert result is True
            assert mock_send.called

