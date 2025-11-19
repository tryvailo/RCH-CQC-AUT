"""Tests for PricingService."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pricing_core.service import PricingService
from pricing_core.models import CareType
from pricing_core.exceptions import DataNotFoundError, InvalidInputError


@pytest.fixture
def pricing_service():
    """Create PricingService instance."""
    return PricingService()


@pytest.fixture
def mock_postcode_info():
    """Mock postcode info."""
    mock_info = Mock()
    mock_info.postcode = "B15 2HQ"
    mock_info.local_authority = "Birmingham"
    mock_info.region = "West Midlands"
    return mock_info


class TestPricingService:
    """Test PricingService class."""
    
    def test_get_full_pricing_success(self, pricing_service, mock_postcode_info):
        """Test successful pricing calculation."""
        with patch.object(pricing_service, 'postcode_resolver') as mock_resolver, \
             patch.object(pricing_service, '_get_msif_fee', return_value=800.0), \
             patch.object(pricing_service, '_get_lottie_average', return_value=1000.0):
            
            mock_resolver.resolve.return_value = mock_postcode_info
            
            result = pricing_service.get_full_pricing(
                postcode="B15 2HQ",
                care_type=CareType.RESIDENTIAL,
                cqc_rating="Good",
                facilities_score=10,
                bed_count=25,
                is_chain=False
            )
            
            assert result.postcode == "B15 2HQ"
            assert result.care_type == CareType.RESIDENTIAL
            assert result.local_authority == "Birmingham"
            assert result.region == "West Midlands"
            assert result.base_price_gbp == 1000.0
            assert result.msif_lower_bound_gbp == 800.0
            assert result.final_price_gbp > 0
            assert result.affordability_band in ["A", "B", "C", "D", "E"]
    
    def test_get_full_pricing_with_scraped_price(self, pricing_service, mock_postcode_info):
        """Test pricing with scraped price override."""
        with patch.object(pricing_service, 'postcode_resolver') as mock_resolver, \
             patch.object(pricing_service, '_get_msif_fee', return_value=800.0), \
             patch.object(pricing_service, '_get_lottie_average', return_value=1000.0):
            
            mock_resolver.resolve.return_value = mock_postcode_info
            
            result = pricing_service.get_full_pricing(
                postcode="B15 2HQ",
                care_type=CareType.RESIDENTIAL,
                scraped_price=950.0
            )
            
            assert result.final_price_gbp == 950.0
            assert result.scraped_price_gbp == 950.0
            assert len(result.adjustments) == 0  # No adjustments when scraped price used
    
    def test_get_full_pricing_invalid_facilities(self, pricing_service):
        """Test pricing with invalid facilities score."""
        with pytest.raises(InvalidInputError):
            pricing_service.get_full_pricing(
                postcode="B15 2HQ",
                care_type=CareType.RESIDENTIAL,
                facilities_score=25  # Invalid: > 20
            )
    
    def test_get_full_pricing_invalid_bed_count(self, pricing_service):
        """Test pricing with invalid bed count."""
        with pytest.raises(InvalidInputError):
            pricing_service.get_full_pricing(
                postcode="B15 2HQ",
                care_type=CareType.RESIDENTIAL,
                bed_count=-5  # Invalid: negative
            )
    
    def test_get_msif_fee(self, pricing_service):
        """Test getting MSIF fee."""
        with patch('pricing_core.service.get_db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = (900.0,)
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value.__enter__.return_value = mock_conn
            
            fee = pricing_service._get_msif_fee("Birmingham", CareType.RESIDENTIAL)
            assert fee == 900.0
    
    def test_get_lottie_average(self, pricing_service):
        """Test getting Lottie average."""
        with patch('pricing_core.service.get_db_connection') as mock_db:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = (1000.0,)
            mock_conn.cursor.return_value = mock_cursor
            mock_db.return_value.__enter__.return_value = mock_conn
            
            avg = pricing_service._get_lottie_average("West Midlands", CareType.RESIDENTIAL)
            assert avg == 1000.0

