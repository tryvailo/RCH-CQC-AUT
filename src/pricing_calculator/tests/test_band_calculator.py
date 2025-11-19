"""Tests for band_calculator.py."""

import pytest
from pricing_calculator.band_calculator import calculate_band
from pricing_calculator.models import BandResult


def test_band_a_excellent_value():
    """Test Band A calculation for excellent value."""
    result = calculate_band(
        base_private_avg=800.0,
        fair_cost_lower=800.0
    )
    assert result.band == "A"
    assert 60 <= result.confidence_percent <= 100


def test_band_b_good_value():
    """Test Band B calculation for good value."""
    result = calculate_band(
        base_private_avg=900.0,
        fair_cost_lower=800.0
    )
    assert result.band == "B"
    assert 60 <= result.confidence_percent <= 100


def test_band_c_fair_value():
    """Test Band C calculation for fair value."""
    result = calculate_band(
        base_private_avg=1000.0,
        fair_cost_lower=800.0
    )
    assert result.band == "C"
    assert 60 <= result.confidence_percent <= 100


def test_band_d_premium():
    """Test Band D calculation for premium pricing."""
    result = calculate_band(
        base_private_avg=1100.0,
        fair_cost_lower=800.0
    )
    assert result.band == "D"
    assert 60 <= result.confidence_percent <= 100


def test_band_e_very_expensive():
    """Test Band E calculation for very expensive."""
    result = calculate_band(
        base_private_avg=1200.0,
        fair_cost_lower=800.0
    )
    assert result.band == "E"
    assert 60 <= result.confidence_percent <= 100


def test_band_without_fair_cost():
    """Test band calculation without fair cost data."""
    result = calculate_band(
        base_private_avg=750.0,
        fair_cost_lower=None
    )
    assert result.band == "A"
    assert result.confidence_percent < 80  # Lower confidence without fair cost


def test_band_with_cqc_outstanding():
    """Test band calculation with Outstanding CQC rating."""
    result = calculate_band(
        base_private_avg=800.0,
        fair_cost_lower=800.0,
        cqc_rating="Outstanding"
    )
    assert result.confidence_percent >= 85  # Higher confidence with Outstanding rating


def test_band_with_facilities_score():
    """Test band calculation with facilities score."""
    result_high = calculate_band(
        base_private_avg=800.0,
        fair_cost_lower=800.0,
        facilities_score=18
    )
    assert result_high.confidence_percent >= 85
    
    result_low = calculate_band(
        base_private_avg=800.0,
        fair_cost_lower=800.0,
        facilities_score=8
    )
    assert result_low.confidence_percent < result_high.confidence_percent


def test_band_with_bed_count():
    """Test band calculation with bed count."""
    result_small = calculate_band(
        base_private_avg=800.0,
        fair_cost_lower=800.0,
        bed_count=5
    )
    
    result_large = calculate_band(
        base_private_avg=800.0,
        fair_cost_lower=800.0,
        bed_count=60
    )
    
    # Small homes may have different pricing
    assert isinstance(result_small, BandResult)
    assert isinstance(result_large, BandResult)


def test_band_with_chain():
    """Test band calculation with chain flag."""
    result = calculate_band(
        base_private_avg=800.0,
        fair_cost_lower=800.0,
        is_chain=True
    )
    assert result.confidence_percent >= 85  # Higher confidence for chains

