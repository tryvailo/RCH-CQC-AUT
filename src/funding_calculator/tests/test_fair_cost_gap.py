"""Tests for Fair Cost Gap calculator."""

import pytest
from funding_calculator.fair_cost_gap import FairCostGapCalculator


@pytest.fixture
def calculator():
    """Create FairCostGapCalculator instance."""
    return FairCostGapCalculator()


class TestFairCostGapCalculator:
    """Test FairCostGapCalculator class."""
    
    def test_calculate_gap_small(self, calculator):
        """Test gap calculation for small gap."""
        result = calculator.calculate_gap(50.0, emotional_tone="professional")
        
        assert result.weekly_gap == 50.0
        assert result.yearly_gap == 50.0 * 52
        assert result.five_year_gap == 50.0 * 52 * 5
        assert "minimal" in result.emotional_text.lower() or "small" in result.emotional_text.lower()
        assert len(result.report_block_html) > 0
        assert len(result.report_block_markdown) > 0
    
    def test_calculate_gap_large(self, calculator):
        """Test gap calculation for large gap."""
        result = calculator.calculate_gap(300.0, emotional_tone="empathetic")
        
        assert result.weekly_gap == 300.0
        assert result.yearly_gap == 300.0 * 52
        assert "substantial" in result.emotional_text.lower() or "considerable" in result.emotional_text.lower()
    
    def test_emotional_tone_professional(self, calculator):
        """Test professional emotional tone."""
        result = calculator.calculate_gap(150.0, emotional_tone="professional")
        
        assert "professional" in result.emotional_text.lower() or "difference" in result.emotional_text.lower()
    
    def test_emotional_tone_empathetic(self, calculator):
        """Test empathetic emotional tone."""
        result = calculator.calculate_gap(150.0, emotional_tone="empathetic")
        
        assert "families" in result.emotional_text.lower() or "emotional" in result.emotional_text.lower()
    
    def test_emotional_tone_urgent(self, calculator):
        """Test urgent emotional tone."""
        result = calculator.calculate_gap(150.0, emotional_tone="urgent")
        
        assert "critical" in result.emotional_text.lower() or "⚠️" in result.emotional_text or "immediate" in result.emotional_text.lower()
    
    def test_html_block_formatting(self, calculator):
        """Test HTML block formatting."""
        result = calculator.calculate_gap(100.0)
        
        assert "fair-cost-gap-block" in result.report_block_html
        assert "£100.00" in result.report_block_html or "100.00" in result.report_block_html
        assert "per week" in result.report_block_html.lower()
    
    def test_markdown_block_formatting(self, calculator):
        """Test Markdown block formatting."""
        result = calculator.calculate_gap(100.0)
        
        assert "Fair Cost Gap" in result.report_block_markdown
        assert "£" in result.report_block_markdown
        assert "|" in result.report_block_markdown  # Table format

