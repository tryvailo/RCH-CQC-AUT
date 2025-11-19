"""Tests for CHC calculator."""

import pytest
from funding_calculator.chc_calculator import FundingEligibilityCalculator
from funding_calculator.models import PatientProfile


@pytest.fixture
def calculator():
    """Create FundingEligibilityCalculator instance."""
    return FundingEligibilityCalculator()


@pytest.fixture
def sample_profile():
    """Create sample patient profile."""
    return PatientProfile(
        age=85,
        has_primary_health_need=True,
        has_dementia=True,
        requires_nursing_care=True,
        mobility_level="bedbound",
        capital_assets=100000.0,
        weekly_income=200.0,
        care_cost_per_week=1200.0
    )


class TestFundingEligibilityCalculator:
    """Test FundingEligibilityCalculator class."""
    
    def test_chc_eligibility_high_probability(self, calculator, sample_profile):
        """Test CHC eligibility with high probability factors."""
        result = calculator.calculate_chc_eligibility(sample_profile)
        
        assert result.probability_percent >= 50
        assert result.is_likely_eligible is True
        assert len(result.key_factors) > 0
        assert "Primary health need" in result.reasoning
    
    def test_chc_eligibility_low_probability(self, calculator):
        """Test CHC eligibility with low probability factors."""
        profile = PatientProfile(
            age=70,
            has_primary_health_need=False,
            requires_nursing_care=False,
            mobility_level="independent",
            capital_assets=50000.0
        )
        
        result = calculator.calculate_chc_eligibility(profile)
        
        assert result.probability_percent < 50
        assert result.is_likely_eligible is False
    
    def test_la_funding_fully_funded(self, calculator):
        """Test LA funding for low capital assets."""
        profile = PatientProfile(
            age=80,
            capital_assets=15000.0,  # Below threshold
            weekly_income=100.0
        )
        
        result = calculator.calculate_la_funding(profile)
        
        assert result.top_up_probability_percent == 0
        assert result.weekly_contribution == 0.0
    
    def test_la_funding_self_funding(self, calculator):
        """Test LA funding for high capital assets."""
        profile = PatientProfile(
            age=80,
            capital_assets=200000.0,  # Above upper threshold
            weekly_income=500.0
        )
        
        result = calculator.calculate_la_funding(profile)
        
        assert result.deferred_payment_eligible is True
        assert "Deferred Payment" in result.deferred_payment_reasoning
    
    def test_la_funding_partial(self, calculator):
        """Test LA funding for middle capital assets."""
        profile = PatientProfile(
            age=80,
            capital_assets=100000.0,  # Between thresholds
            weekly_income=200.0,
            care_cost_per_week=1200.0
        )
        
        result = calculator.calculate_la_funding(profile)
        
        assert result.top_up_probability_percent > 0
        assert result.deferred_payment_eligible is True
    
    def test_calculate_potential_savings(self, calculator, sample_profile):
        """Test potential savings calculation."""
        chc_result = calculator.calculate_chc_eligibility(sample_profile)
        la_result = calculator.calculate_la_funding(sample_profile)
        
        savings = calculator.calculate_potential_savings(
            sample_profile,
            chc_result,
            la_result,
            1200.0
        )
        
        assert savings["per_week"] >= 0
        assert savings["per_year"] == savings["per_week"] * 52
        assert savings["5_years"] == savings["per_year"] * 5
    
    def test_calculate_full_eligibility(self, calculator, sample_profile):
        """Test full eligibility calculation."""
        result = calculator.calculate_full_eligibility(sample_profile)
        
        assert result.chc_eligibility is not None
        assert result.la_funding is not None
        assert result.potential_savings_per_week >= 0
        assert result.potential_savings_per_year >= 0
        assert result.potential_savings_5_years >= 0
        assert len(result.recommendations) > 0

