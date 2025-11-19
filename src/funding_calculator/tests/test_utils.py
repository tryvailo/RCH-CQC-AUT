"""Tests for utility functions."""

import pytest
from funding_calculator.utils import (
    count_domain_levels,
    calculate_chc_base_score,
    calculate_chc_bonuses,
    calculate_tariff_income,
    assess_property_for_means_test,
    calculate_chc_probability_range
)
from funding_calculator.models import DomainAssessment, PatientProfile, PropertyDetails
from funding_calculator.constants import Domain, DomainLevel, MEANS_TEST


class TestCountDomainLevels:
    """Test count_domain_levels function."""
    
    def test_count_priority(self):
        """Test counting PRIORITY domains."""
        assessments = {
            Domain.BREATHING: DomainAssessment(
                domain=Domain.BREATHING,
                level=DomainLevel.PRIORITY,
                description="Critical"
            ),
            Domain.COGNITION: DomainAssessment(
                domain=Domain.COGNITION,
                level=DomainLevel.HIGH,
                description="High"
            )
        }
        
        count = count_domain_levels(assessments, DomainLevel.PRIORITY)
        assert count == 1
    
    def test_count_severe(self):
        """Test counting SEVERE domains."""
        assessments = {
            Domain.COGNITION: DomainAssessment(
                domain=Domain.COGNITION,
                level=DomainLevel.SEVERE,
                description="Severe"
            ),
            Domain.MOBILITY: DomainAssessment(
                domain=Domain.MOBILITY,
                level=DomainLevel.SEVERE,
                description="Severe"
            ),
            Domain.BREATHING: DomainAssessment(
                domain=Domain.BREATHING,
                level=DomainLevel.HIGH,
                description="High"
            )
        }
        
        count = count_domain_levels(assessments, DomainLevel.SEVERE)
        assert count == 2
    
    def test_count_with_domain_filter(self):
        """Test counting with domain filter."""
        assessments = {
            Domain.COGNITION: DomainAssessment(
                domain=Domain.COGNITION,
                level=DomainLevel.SEVERE,
                description="Severe"
            ),
            Domain.MOBILITY: DomainAssessment(
                domain=Domain.MOBILITY,
                level=DomainLevel.SEVERE,
                description="Severe"
            ),
            Domain.BREATHING: DomainAssessment(
                domain=Domain.BREATHING,
                level=DomainLevel.HIGH,
                description="High"
            )
        }
        
        # Count only in critical domains
        from funding_calculator.constants import DOMAIN_GROUPS
        critical_domains = DOMAIN_GROUPS["critical_domains"]
        count = count_domain_levels(assessments, DomainLevel.SEVERE, critical_domains)
        assert count == 2  # Both cognition and mobility are critical


class TestCHCBaseScore:
    """Test calculate_chc_base_score function."""
    
    def test_base_score_priority(self):
        """Test base score with PRIORITY."""
        assessments = {
            Domain.BREATHING: DomainAssessment(
                domain=Domain.BREATHING,
                level=DomainLevel.PRIORITY,
                description="Critical"
            )
        }
        
        score = calculate_chc_base_score(assessments)
        assert score >= 45  # PRIORITY weight
    
    def test_base_score_severe(self):
        """Test base score with SEVERE."""
        assessments = {
            Domain.COGNITION: DomainAssessment(
                domain=Domain.COGNITION,
                level=DomainLevel.SEVERE,
                description="Severe"
            )
        }
        
        score = calculate_chc_base_score(assessments)
        assert score == 20  # SEVERE weight
    
    def test_base_score_multiple(self):
        """Test base score with multiple levels."""
        assessments = {
            Domain.COGNITION: DomainAssessment(
                domain=Domain.COGNITION,
                level=DomainLevel.SEVERE,
                description="Severe"
            ),
            Domain.MOBILITY: DomainAssessment(
                domain=Domain.MOBILITY,
                level=DomainLevel.HIGH,
                description="High"
            ),
            Domain.BREATHING: DomainAssessment(
                domain=Domain.BREATHING,
                level=DomainLevel.HIGH,
                description="High"
            )
        }
        
        score = calculate_chc_base_score(assessments)
        assert score == 20 + 9 + 9  # 1 SEVERE + 2 HIGH


class TestCHCBonuses:
    """Test calculate_chc_bonuses function."""
    
    def test_multiple_severe_bonus(self):
        """Test multiple severe bonus."""
        assessments = {
            Domain.COGNITION: DomainAssessment(
                domain=Domain.COGNITION,
                level=DomainLevel.SEVERE,
                description="Severe"
            ),
            Domain.MOBILITY: DomainAssessment(
                domain=Domain.MOBILITY,
                level=DomainLevel.SEVERE,
                description="Severe"
            )
        }
        
        profile = PatientProfile(age=80)
        bonuses = calculate_chc_bonuses(assessments, profile)
        
        assert "multiple_severe" in bonuses
        assert bonuses["multiple_severe"] == 25
    
    def test_unpredictability_bonus(self):
        """Test unpredictability bonus."""
        assessments = {
            Domain.BEHAVIOUR: DomainAssessment(
                domain=Domain.BEHAVIOUR,
                level=DomainLevel.HIGH,
                description="High"
            )
        }
        
        profile = PatientProfile(
            age=80,
            has_unpredictable_needs=True
        )
        
        bonuses = calculate_chc_bonuses(assessments, profile)
        
        assert "unpredictability" in bonuses
        assert bonuses["unpredictability"] == 15
    
    def test_complex_therapies_bonus(self):
        """Test complex therapies bonus."""
        assessments = {}
        
        profile = PatientProfile(
            age=80,
            has_peg_feeding=True
        )
        
        bonuses = calculate_chc_bonuses(assessments, profile)
        
        assert "complex_therapies" in bonuses
        assert bonuses["complex_therapies"] == 8


class TestTariffIncome:
    """Test calculate_tariff_income function."""
    
    def test_below_lower_limit(self):
        """Test tariff income below lower limit."""
        income = calculate_tariff_income(10000.0)
        assert income == 0.0
    
    def test_at_lower_limit(self):
        """Test tariff income at lower limit."""
        income = calculate_tariff_income(MEANS_TEST["lower_capital_limit"])
        assert income == 0.0
    
    def test_above_lower_limit(self):
        """Test tariff income above lower limit."""
        # £20,000 - £14,250 = £5,750
        # £5,750 / £250 = 23 weeks
        income = calculate_tariff_income(20000.0)
        assert income == 23.0
    
    def test_partial_weeks(self):
        """Test tariff income with partial weeks."""
        # £15,000 - £14,250 = £750
        # £750 / £250 = 3 weeks (rounds up)
        income = calculate_tariff_income(15000.0)
        assert income == 3.0


class TestPropertyAssessment:
    """Test assess_property_for_means_test function."""
    
    def test_no_property(self):
        """Test assessment with no property."""
        assessment = assess_property_for_means_test(None, dpa_eligible=False)
        
        assert assessment["disregarded"] is True
        assert assessment["value_counted"] == 0.0
    
    def test_property_with_dpa(self):
        """Test property disregarded with DPA."""
        property_details = PropertyDetails(
            value=200000.0,
            is_main_residence=True
        )
        
        assessment = assess_property_for_means_test(property_details, dpa_eligible=True)
        
        assert assessment["disregarded"] is True
        assert assessment["value_counted"] == 0.0
    
    def test_property_with_qualifying_relative(self):
        """Test property disregarded with qualifying relative."""
        property_details = PropertyDetails(
            value=200000.0,
            is_main_residence=True,
            has_qualifying_relative=True
        )
        
        assessment = assess_property_for_means_test(property_details, dpa_eligible=False)
        
        assert assessment["disregarded"] is True
        assert assessment["value_counted"] == 0.0
    
    def test_property_counted(self):
        """Test property counted when not disregarded."""
        property_details = PropertyDetails(
            value=200000.0,
            is_main_residence=True,
            has_qualifying_relative=False
        )
        
        assessment = assess_property_for_means_test(property_details, dpa_eligible=False)
        
        assert assessment["disregarded"] is False
        assert assessment["value_counted"] == 200000.0


class TestProbabilityRange:
    """Test calculate_chc_probability_range function."""
    
    def test_very_high_priority(self):
        """Test very high range with priority."""
        min_prob, max_prob, category = calculate_chc_probability_range(
            priority_count=1,
            severe_count=0,
            high_count=0
        )
        
        assert category == "very_high"
        assert 92 <= min_prob <= max_prob <= 98
    
    def test_very_high_multiple_severe(self):
        """Test very high range with multiple severe."""
        min_prob, max_prob, category = calculate_chc_probability_range(
            priority_count=0,
            severe_count=2,
            high_count=0
        )
        
        assert category == "very_high"
        assert 92 <= min_prob <= max_prob <= 98
    
    def test_very_high_severe_plus_high(self):
        """Test very high range with severe + high."""
        min_prob, max_prob, category = calculate_chc_probability_range(
            priority_count=0,
            severe_count=1,
            high_count=4
        )
        
        assert category == "very_high"
        assert 92 <= min_prob <= max_prob <= 98
    
    def test_high_range(self):
        """Test high range."""
        min_prob, max_prob, category = calculate_chc_probability_range(
            priority_count=0,
            severe_count=1,
            high_count=2
        )
        
        assert category == "high"
        assert 82 <= min_prob <= max_prob <= 91
    
    def test_moderate_range(self):
        """Test moderate range."""
        min_prob, max_prob, category = calculate_chc_probability_range(
            priority_count=0,
            severe_count=0,
            high_count=5
        )
        
        assert category == "moderate"
        assert 70 <= min_prob <= max_prob <= 81
    
    def test_low_range(self):
        """Test low range."""
        min_prob, max_prob, category = calculate_chc_probability_range(
            priority_count=0,
            severe_count=0,
            high_count=2
        )
        
        assert category == "low"
        assert 0 <= min_prob <= max_prob < 70


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

