"""Tests for service.py."""

import pytest
from unittest.mock import patch, MagicMock
from pricing_calculator.service import PricingService
from pricing_calculator.models import CareType
from pricing_calculator.exceptions import PricingCalculatorError


@patch("pricing_calculator.service.load_fair_cost_data")
def test_service_init(mock_load):
    """Test PricingService initialization."""
    mock_load.return_value = {
        "Birmingham": {
            "residential": 750.0,
            "nursing": 950.0
        }
    }
    
    service = PricingService()
    assert service.fair_cost_data is not None
    assert service.postcode_mapper is not None


@patch("pricing_calculator.service.get_postcode_info")
@patch("pricing_calculator.service.get_lottie_price_sync")
@patch("pricing_calculator.service.calculate_band")
def test_get_pricing_for_postcode_success(
    mock_calc_band,
    mock_lottie,
    mock_postcode
):
    """Test successful pricing calculation."""
    from pricing_calculator.models import PostcodeInfo, BandResult
    
    # Setup mocks
    mock_postcode.return_value = PostcodeInfo(
        postcode="B15 2HQ",
        local_authority="Birmingham",
        region="West Midlands"
    )
    
    mock_lottie.return_value = 850.0
    
    mock_calc_band.return_value = BandResult(
        band="B",
        confidence_percent=85,
        reasoning="Test"
    )
    
    # Create service with mocked fair cost data
    service = PricingService()
    service.fair_cost_data = {
        "Birmingham": {
            "residential": 750.0
        }
    }
    
    # Calculate pricing
    result = service.get_pricing_for_postcode(
        postcode="B15 2HQ",
        care_type=CareType.RESIDENTIAL,
        cqc_rating="Good"
    )
    
    assert result.postcode == "B15 2HQ"
    assert result.care_type == CareType.RESIDENTIAL
    assert result.local_authority == "Birmingham"
    assert result.affordability_band == "B"
    assert result.private_average_gbp == 850.0
    assert result.fair_cost_lower_bound_gbp == 750.0
    assert "Lottie" in result.sources_used


@patch("pricing_calculator.service.get_postcode_info")
@patch("pricing_calculator.service.get_lottie_price_sync")
def test_get_pricing_no_lottie_data(mock_lottie, mock_postcode):
    """Test pricing calculation when Lottie data is unavailable."""
    from pricing_calculator.models import PostcodeInfo
    
    mock_postcode.return_value = PostcodeInfo(
        postcode="B15 2HQ",
        local_authority="Birmingham",
        region="West Midlands"
    )
    
    mock_lottie.return_value = 0.0  # No data
    
    service = PricingService()
    
    with pytest.raises(PricingCalculatorError):
        service.get_pricing_for_postcode(
            postcode="B15 2HQ",
            care_type=CareType.RESIDENTIAL
        )


@patch("pricing_calculator.service.get_postcode_info")
@patch("pricing_calculator.service.get_lottie_price_sync")
@patch("pricing_calculator.service.calculate_band")
def test_get_pricing_with_all_factors(
    mock_calc_band,
    mock_lottie,
    mock_postcode
):
    """Test pricing calculation with all optional factors."""
    from pricing_calculator.models import PostcodeInfo, BandResult
    
    mock_postcode.return_value = PostcodeInfo(
        postcode="SW1A 1AA",
        local_authority="Westminster",
        region="London"
    )
    
    mock_lottie.return_value = 1200.0
    
    mock_calc_band.return_value = BandResult(
        band="A",
        confidence_percent=90,
        reasoning="Test"
    )
    
    service = PricingService()
    service.fair_cost_data = {
        "Westminster": {
            "nursing": 1100.0
        }
    }
    
    result = service.get_pricing_for_postcode(
        postcode="SW1A 1AA",
        care_type=CareType.NURSING,
        cqc_rating="Outstanding",
        facilities_score=18,
        bed_count=30,
        is_chain=True
    )
    
    assert result.cqc_rating == "Outstanding"
    assert result.facilities_score == 18
    assert result.bed_count == 30
    assert result.is_chain is True
    assert result.negotiation_leverage_text is not None
    assert len(result.negotiation_leverage_text) > 0


def test_generate_negotiation_text():
    """Test negotiation text generation."""
    from pricing_calculator.models import PostcodeInfo
    
    service = PricingService()
    
    postcode_info = PostcodeInfo(
        postcode="B15 2HQ",
        local_authority="Birmingham",
        region="West Midlands"
    )
    
    text = service._generate_negotiation_text(
        postcode_info=postcode_info,
        care_type=CareType.RESIDENTIAL,
        private_average=850.0,
        fair_cost_lower=750.0,
        band="B",
        gap_gbp=100.0,
        gap_percent=13.3,
        cqc_rating="Good"
    )
    
    assert "Birmingham" in text
    assert "£850" in text
    assert "£750" in text
    assert "Band: B" in text or "Band B" in text

