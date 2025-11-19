"""Tests for Band Calculator v5."""

import pytest
from pricing_core.band_calculator import BandCalculatorV5


class TestBandCalculatorV5:
    """Test BandCalculatorV5 class."""
    
    def test_band_score_calculation(self):
        """Test band score calculation."""
        msif_lower = 800.0
        lottie_average = 1000.0
        
        # Price at MSIF lower bound
        score = BandCalculatorV5.calculate_band_score(800.0, msif_lower, lottie_average)
        assert score == pytest.approx(0.0)
        
        # Price at Lottie average
        score = BandCalculatorV5.calculate_band_score(1000.0, msif_lower, lottie_average)
        assert score == pytest.approx(1.0)
        
        # Price in middle
        score = BandCalculatorV5.calculate_band_score(900.0, msif_lower, lottie_average)
        assert score == pytest.approx(0.5)
    
    def test_band_score_no_msif(self):
        """Test band score calculation without MSIF."""
        lottie_average = 1000.0
        
        score = BandCalculatorV5.calculate_band_score(950.0, None, lottie_average)
        assert 0.0 <= score <= 1.0
    
    def test_band_a(self):
        """Test Band A calculation."""
        band, reasoning = BandCalculatorV5.calculate_band(0.03)
        assert band == "A"
        assert "Excellent" in reasoning
    
    def test_band_b(self):
        """Test Band B calculation."""
        band, reasoning = BandCalculatorV5.calculate_band(0.10)
        assert band == "B"
        assert "Good" in reasoning
    
    def test_band_c(self):
        """Test Band C calculation."""
        band, reasoning = BandCalculatorV5.calculate_band(0.20)
        assert band == "C"
        assert "Fair" in reasoning
    
    def test_band_d(self):
        """Test Band D calculation."""
        band, reasoning = BandCalculatorV5.calculate_band(0.30)
        assert band == "D"
        assert "Premium" in reasoning
    
    def test_band_e(self):
        """Test Band E calculation."""
        band, reasoning = BandCalculatorV5.calculate_band(0.50)
        assert band == "E"
        assert "Very expensive" in reasoning
    
    def test_confidence_with_msif(self):
        """Test confidence calculation with MSIF."""
        confidence = BandCalculatorV5.calculate_confidence(
            msif_lower=800.0,
            lottie_average=1000.0,
            adjustments_applied={"cqc_rating": 0.15},
            cqc_rating="Good"
        )
        assert 60 <= confidence <= 100
    
    def test_confidence_without_msif(self):
        """Test confidence calculation without MSIF."""
        confidence = BandCalculatorV5.calculate_confidence(
            msif_lower=None,
            lottie_average=1000.0,
            adjustments_applied={},
            cqc_rating=None
        )
        assert 60 <= confidence <= 100
        assert confidence < 100  # Should be reduced
    
    def test_expected_range_band_a(self):
        """Test expected range for Band A."""
        min_price, max_price = BandCalculatorV5.calculate_expected_range(1000.0, 0.03)
        assert min_price < 1000.0
        assert max_price > 1000.0
        assert abs(max_price - min_price) < 100.0  # Narrow range
    
    def test_expected_range_band_e(self):
        """Test expected range for Band E."""
        min_price, max_price = BandCalculatorV5.calculate_expected_range(1000.0, 0.50)
        assert min_price < 1000.0
        assert max_price > 1000.0
        assert abs(max_price - min_price) > 100.0  # Wide range

