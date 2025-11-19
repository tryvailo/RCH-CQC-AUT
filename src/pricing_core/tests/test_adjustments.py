"""Tests for price adjustments."""

import pytest
from pricing_core.adjustments import PriceAdjustments


class TestPriceAdjustments:
    """Test PriceAdjustments class."""
    
    def test_cqc_adjustment_outstanding(self):
        """Test CQC Outstanding adjustment."""
        adj = PriceAdjustments.calculate_cqc_adjustment("Outstanding")
        assert adj == 0.15
    
    def test_cqc_adjustment_good(self):
        """Test CQC Good adjustment."""
        adj = PriceAdjustments.calculate_cqc_adjustment("Good")
        assert adj == 0.05
    
    def test_cqc_adjustment_requires_improvement(self):
        """Test CQC Requires Improvement adjustment."""
        adj = PriceAdjustments.calculate_cqc_adjustment("Requires Improvement")
        assert adj == -0.05
    
    def test_cqc_adjustment_inadequate(self):
        """Test CQC Inadequate adjustment."""
        adj = PriceAdjustments.calculate_cqc_adjustment("Inadequate")
        assert adj == -0.15
    
    def test_cqc_adjustment_none(self):
        """Test CQC adjustment with None."""
        adj = PriceAdjustments.calculate_cqc_adjustment(None)
        assert adj == 0.0
    
    def test_care_type_nursing(self):
        """Test nursing care type adjustment."""
        adj = PriceAdjustments.calculate_care_type_adjustment("nursing")
        assert adj == 0.25
    
    def test_care_type_dementia(self):
        """Test dementia care type adjustment."""
        adj = PriceAdjustments.calculate_care_type_adjustment("residential_dementia")
        assert adj == 0.12
    
    def test_care_type_nursing_dementia(self):
        """Test nursing dementia care type adjustment."""
        adj = PriceAdjustments.calculate_care_type_adjustment("nursing_dementia")
        assert adj == 0.25 + 0.12  # Both adjustments
    
    def test_facilities_adjustment_min(self):
        """Test facilities adjustment minimum."""
        adj = PriceAdjustments.calculate_facilities_adjustment(0)
        assert adj == pytest.approx(-0.10)
    
    def test_facilities_adjustment_max(self):
        """Test facilities adjustment maximum."""
        adj = PriceAdjustments.calculate_facilities_adjustment(20)
        assert adj == pytest.approx(0.10)
    
    def test_facilities_adjustment_mid(self):
        """Test facilities adjustment middle."""
        adj = PriceAdjustments.calculate_facilities_adjustment(10)
        assert adj == pytest.approx(0.0)
    
    def test_size_adjustment_small(self):
        """Test size adjustment for small homes."""
        adj = PriceAdjustments.calculate_size_adjustment(15)
        assert adj == 0.05
    
    def test_size_adjustment_optimal(self):
        """Test size adjustment for optimal size."""
        adj = PriceAdjustments.calculate_size_adjustment(30)
        assert adj == 0.0
    
    def test_size_adjustment_large(self):
        """Test size adjustment for large homes."""
        adj = PriceAdjustments.calculate_size_adjustment(70)
        assert adj == -0.05
    
    def test_chain_adjustment(self):
        """Test chain adjustment."""
        adj = PriceAdjustments.calculate_chain_adjustment(True)
        assert adj == -0.08
        
        adj = PriceAdjustments.calculate_chain_adjustment(False)
        assert adj == 0.0
    
    def test_all_adjustments(self):
        """Test calculating all adjustments."""
        adjustments = PriceAdjustments.calculate_all_adjustments(
            care_type="nursing_dementia",
            cqc_rating="Outstanding",
            facilities_score=15,
            bed_count=25,
            is_chain=True
        )
        
        assert "cqc_rating" in adjustments
        assert "care_type" in adjustments
        assert "facilities" in adjustments
        assert "chain" in adjustments
    
    def test_apply_adjustments(self):
        """Test applying adjustments to base price."""
        base_price = 1000.0
        adjustments = {
            "cqc_rating": 0.15,
            "care_type": 0.25,
            "facilities": 0.05
        }
        
        adjusted = PriceAdjustments.apply_adjustments(base_price, adjustments)
        
        # Total adjustment: 45%
        expected = base_price * 1.45
        assert adjusted == pytest.approx(expected)

