"""Tests for models.py."""

import pytest
from pydantic import ValidationError
from pricing_calculator.models import CareType, PostcodeInfo, PricingResult, BandResult


def test_care_type_enum():
    """Test CareType enum values."""
    assert CareType.RESIDENTIAL == "residential"
    assert CareType.NURSING == "nursing"
    assert CareType.RESIDENTIAL_DEMENTIA == "residential_dementia"
    assert CareType.NURSING_DEMENTIA == "nursing_dementia"
    assert CareType.RESPITE == "respite"


def test_postcode_info_valid():
    """Test valid PostcodeInfo creation."""
    info = PostcodeInfo(
        postcode="SW1A 1AA",
        local_authority="Westminster",
        region="London"
    )
    assert info.postcode == "SW1A 1AA"
    assert info.local_authority == "Westminster"
    assert info.region == "London"
    assert info.country == "England"


def test_postcode_info_normalization():
    """Test postcode normalization."""
    info1 = PostcodeInfo(
        postcode="sw1a1aa",
        local_authority="Westminster",
        region="London"
    )
    assert info1.postcode == "SW1A 1AA"
    
    info2 = PostcodeInfo(
        postcode="B15 2HQ",
        local_authority="Birmingham",
        region="West Midlands"
    )
    assert info2.postcode == "B15 2HQ"


def test_postcode_info_invalid():
    """Test invalid postcode raises error."""
    with pytest.raises(ValidationError):
        PostcodeInfo(
            postcode="INVALID",
            local_authority="Test",
            region="Test"
        )


def test_band_result_valid():
    """Test valid BandResult creation."""
    result = BandResult(
        band="A",
        confidence_percent=85,
        reasoning="Test reasoning"
    )
    assert result.band == "A"
    assert result.confidence_percent == 85
    assert result.reasoning == "Test reasoning"


def test_band_result_invalid_confidence():
    """Test invalid confidence raises error."""
    with pytest.raises(ValidationError):
        BandResult(
            band="A",
            confidence_percent=50,  # Below minimum
            reasoning="Test"
        )
    
    with pytest.raises(ValidationError):
        BandResult(
            band="A",
            confidence_percent=150,  # Above maximum
            reasoning="Test"
        )


def test_pricing_result_valid():
    """Test valid PricingResult creation."""
    result = PricingResult(
        postcode="SW1A 1AA",
        care_type=CareType.NURSING,
        local_authority="Westminster",
        region="London",
        private_average_gbp=1200.0,
        expected_range_min_gbp=1000.0,
        expected_range_max_gbp=1400.0,
        affordability_band="B",
        band_confidence_percent=80,
        fair_cost_gap_gbp=200.0,
        fair_cost_gap_percent=20.0,
        negotiation_leverage_text="Test text",
        sources_used=["Lottie"]
    )
    assert result.postcode == "SW1A 1AA"
    assert result.care_type == CareType.NURSING
    assert result.affordability_band == "B"
    assert result.band_confidence_percent == 80


def test_pricing_result_with_fair_cost():
    """Test PricingResult with fair cost data."""
    result = PricingResult(
        postcode="B15 2HQ",
        care_type=CareType.RESIDENTIAL,
        local_authority="Birmingham",
        region="West Midlands",
        fair_cost_lower_bound_gbp=750.0,
        private_average_gbp=850.0,
        expected_range_min_gbp=700.0,
        expected_range_max_gbp=1000.0,
        affordability_band="B",
        band_confidence_percent=85,
        fair_cost_gap_gbp=100.0,
        fair_cost_gap_percent=13.3,
        negotiation_leverage_text="Test"
    )
    assert result.fair_cost_lower_bound_gbp == 750.0
    assert result.fair_cost_gap_gbp == 100.0

