"""Tests for FundingEligibilityCalculator 2025-2026."""

import pytest
from funding_calculator import (
    FundingEligibilityCalculator,
    Domain,
    DomainLevel,
    PatientProfile,
    PropertyDetails,
    DomainAssessment,
    MEANS_TEST,
    DPA_ELIGIBILITY
)

try:
    from pricing_core.models import PricingResult, CareType
    PRICING_AVAILABLE = True
except ImportError:
    PRICING_AVAILABLE = False
    PricingResult = None
    CareType = None


class TestCHCScoring:
    """Test CHC scoring logic."""
    
    def test_priority_domain_high_probability(self):
        """Test that PRIORITY domain gives high probability."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            domain_assessments={
                Domain.BREATHING: DomainAssessment(
                    domain=Domain.BREATHING,
                    level=DomainLevel.PRIORITY,
                    description="Critical breathing needs"
                )
            }
        )
        
        result = calc.calculate_chc_probability(profile)
        
        assert result.probability_percent >= 92
        assert result.probability_percent <= 98
        assert result.is_likely_eligible is True
        assert result.threshold_category == "very_high"
        assert DomainLevel.PRIORITY in [a.level for a in profile.domain_assessments.values()]
    
    def test_multiple_severe_domains(self):
        """Test that ≥2 Severe domains give very high probability."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            domain_assessments={
                Domain.COGNITION: DomainAssessment(
                    domain=Domain.COGNITION,
                    level=DomainLevel.SEVERE,
                    description="Severe cognitive impairment"
                ),
                Domain.MOBILITY: DomainAssessment(
                    domain=Domain.MOBILITY,
                    level=DomainLevel.SEVERE,
                    description="Severe mobility issues"
                )
            }
        )
        
        result = calc.calculate_chc_probability(profile)
        
        assert result.probability_percent >= 92
        assert result.is_likely_eligible is True
        assert "multiple_severe" in result.bonuses_applied
    
    def test_severe_plus_high_domains(self):
        """Test that 1 Severe + ≥4 High gives very high probability."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            domain_assessments={
                Domain.COGNITION: DomainAssessment(
                    domain=Domain.COGNITION,
                    level=DomainLevel.SEVERE,
                    description="Severe cognitive impairment"
                ),
                Domain.MOBILITY: DomainAssessment(
                    domain=Domain.MOBILITY,
                    level=DomainLevel.HIGH,
                    description="High mobility needs"
                ),
                Domain.BREATHING: DomainAssessment(
                    domain=Domain.BREATHING,
                    level=DomainLevel.HIGH,
                    description="High breathing needs"
                ),
                Domain.SKIN: DomainAssessment(
                    domain=Domain.SKIN,
                    level=DomainLevel.HIGH,
                    description="High skin care needs"
                ),
                Domain.COMMUNICATION: DomainAssessment(
                    domain=Domain.COMMUNICATION,
                    level=DomainLevel.HIGH,
                    description="High communication needs"
                )
            }
        )
        
        result = calc.calculate_chc_probability(profile)
        
        assert result.probability_percent >= 92
        assert result.is_likely_eligible is True
    
    def test_one_severe_plus_high(self):
        """Test that 1 Severe + 2-3 High gives high probability."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            domain_assessments={
                Domain.COGNITION: DomainAssessment(
                    domain=Domain.COGNITION,
                    level=DomainLevel.SEVERE,
                    description="Severe cognitive impairment"
                ),
                Domain.MOBILITY: DomainAssessment(
                    domain=Domain.MOBILITY,
                    level=DomainLevel.HIGH,
                    description="High mobility needs"
                ),
                Domain.BREATHING: DomainAssessment(
                    domain=Domain.BREATHING,
                    level=DomainLevel.HIGH,
                    description="High breathing needs"
                )
            }
        )
        
        result = calc.calculate_chc_probability(profile)
        
        assert 82 <= result.probability_percent <= 91
        assert result.threshold_category == "high"
    
    def test_multiple_high_domains(self):
        """Test that ≥5 High gives moderate probability."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            domain_assessments={
                Domain.COGNITION: DomainAssessment(
                    domain=Domain.COGNITION,
                    level=DomainLevel.HIGH,
                    description="High cognitive needs"
                ),
                Domain.MOBILITY: DomainAssessment(
                    domain=Domain.MOBILITY,
                    level=DomainLevel.HIGH,
                    description="High mobility needs"
                ),
                Domain.BREATHING: DomainAssessment(
                    domain=Domain.BREATHING,
                    level=DomainLevel.HIGH,
                    description="High breathing needs"
                ),
                Domain.SKIN: DomainAssessment(
                    domain=Domain.SKIN,
                    level=DomainLevel.HIGH,
                    description="High skin care needs"
                ),
                Domain.COMMUNICATION: DomainAssessment(
                    domain=Domain.COMMUNICATION,
                    level=DomainLevel.HIGH,
                    description="High communication needs"
                ),
                Domain.BEHAVIOUR: DomainAssessment(
                    domain=Domain.BEHAVIOUR,
                    level=DomainLevel.HIGH,
                    description="High behavioural needs"
                )
            }
        )
        
        result = calc.calculate_chc_probability(profile)
        
        assert 70 <= result.probability_percent <= 81
        assert result.threshold_category == "moderate"
    
    def test_low_needs(self):
        """Test that low needs give low probability."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            domain_assessments={
                Domain.MOBILITY: DomainAssessment(
                    domain=Domain.MOBILITY,
                    level=DomainLevel.MODERATE,
                    description="Moderate mobility needs"
                )
            }
        )
        
        result = calc.calculate_chc_probability(profile)
        
        assert result.probability_percent < 70
        assert result.threshold_category == "low"
        assert result.is_likely_eligible is False
    
    def test_complex_therapies_bonus(self):
        """Test that complex therapies add bonus."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            domain_assessments={
                Domain.NUTRITION: DomainAssessment(
                    domain=Domain.NUTRITION,
                    level=DomainLevel.HIGH,
                    description="High nutrition needs"
                )
            },
            has_peg_feeding=True
        )
        
        result = calc.calculate_chc_probability(profile)
        
        assert "complex_therapies" in result.bonuses_applied
    
    def test_unpredictability_bonus(self):
        """Test that unpredictability adds bonus."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            domain_assessments={
                Domain.BEHAVIOUR: DomainAssessment(
                    domain=Domain.BEHAVIOUR,
                    level=DomainLevel.HIGH,
                    description="High behavioural needs"
                )
            },
            has_unpredictable_needs=True
        )
        
        result = calc.calculate_chc_probability(profile)
        
        assert "unpredictability" in result.bonuses_applied
    
    def test_maximum_probability_cap(self):
        """Test that probability never exceeds 98%."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            domain_assessments={
                Domain.BREATHING: DomainAssessment(
                    domain=Domain.BREATHING,
                    level=DomainLevel.PRIORITY,
                    description="Critical"
                ),
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
            },
            has_unpredictable_needs=True,
            has_peg_feeding=True
        )
        
        result = calc.calculate_chc_probability(profile)
        
        assert result.probability_percent <= 98


class TestMeansTest:
    """Test means test calculations."""
    
    def test_below_lower_limit_fully_funded(self):
        """Test that capital below lower limit is fully funded."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            capital_assets=10000.0,  # Below £14,250
            weekly_income=200.0
        )
        
        result = calc.calculate_la_support(profile, dpa_eligible=False)
        
        assert result.is_fully_funded is True
        assert result.full_support_probability_percent == 100
        assert result.tariff_income_gbp_week == 0.0
    
    def test_between_limits_tariff_income(self):
        """Test tariff income calculation between limits."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            capital_assets=20000.0,  # Between £14,250 and £23,250
            weekly_income=200.0
        )
        
        result = calc.calculate_la_support(profile, dpa_eligible=False)
        
        assert result.is_fully_funded is False
        assert result.tariff_income_gbp_week > 0
        # £20,000 - £14,250 = £5,750 excess
        # £5,750 / £250 = 23 weeks tariff income
        assert result.tariff_income_gbp_week == 23.0
    
    def test_above_upper_limit_self_funding(self):
        """Test that capital above upper limit is self-funding."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            capital_assets=50000.0,  # Above £23,250
            weekly_income=200.0
        )
        
        result = calc.calculate_la_support(profile, dpa_eligible=False)
        
        assert result.is_fully_funded is False
        assert result.full_support_probability_percent == 0
        assert result.top_up_probability_percent == 0
    
    def test_property_disregarded_with_dpa(self):
        """Test that property is disregarded if DPA eligible."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            capital_assets=10000.0,
            property=PropertyDetails(
                value=200000.0,
                is_main_residence=True
            )
        )
        
        result = calc.calculate_la_support(profile, dpa_eligible=True)
        
        assert result.capital_assessed == 10000.0  # Property not counted
        assert result.is_fully_funded is True
    
    def test_property_disregarded_with_qualifying_relative(self):
        """Test that property is disregarded if qualifying relative lives there."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            capital_assets=10000.0,
            property=PropertyDetails(
                value=200000.0,
                is_main_residence=True,
                has_qualifying_relative=True
            )
        )
        
        result = calc.calculate_la_support(profile, dpa_eligible=False)
        
        assert result.capital_assessed == 10000.0  # Property not counted


class TestDPA:
    """Test Deferred Payment Agreement eligibility."""
    
    def test_dpa_eligible(self):
        """Test DPA eligibility criteria."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            capital_assets=15000.0,  # Below threshold
            is_permanent_care=True,
            property=PropertyDetails(
                value=200000.0,
                is_main_residence=True,
                has_qualifying_relative=False
            )
        )
        
        result = calc.calculate_dpa_eligibility(profile)
        
        assert result.is_eligible is True
        assert result.property_disregarded is True
    
    def test_dpa_not_eligible_respite(self):
        """Test that respite care is not eligible for DPA."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            capital_assets=15000.0,
            is_permanent_care=False,  # Respite care
            property=PropertyDetails(
                value=200000.0,
                is_main_residence=True
            )
        )
        
        result = calc.calculate_dpa_eligibility(profile)
        
        assert result.is_eligible is False
    
    def test_dpa_not_eligible_qualifying_relative(self):
        """Test that qualifying relative disqualifies DPA."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            capital_assets=15000.0,
            is_permanent_care=True,
            property=PropertyDetails(
                value=200000.0,
                is_main_residence=True,
                has_qualifying_relative=True
            )
        )
        
        result = calc.calculate_dpa_eligibility(profile)
        
        assert result.is_eligible is False
    
    def test_dpa_not_eligible_high_capital(self):
        """Test that high non-property capital disqualifies DPA."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            capital_assets=50000.0,  # Above threshold
            is_permanent_care=True,
            property=PropertyDetails(
                value=200000.0,
                is_main_residence=True
            )
        )
        
        result = calc.calculate_dpa_eligibility(profile)
        
        assert result.is_eligible is False


class TestSavings:
    """Test savings calculations."""
    
    @pytest.mark.skipif(not PRICING_AVAILABLE, reason="PricingResult not available")
    def test_savings_with_pricing_result(self):
        """Test savings calculation with PricingResult."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(age=80)
        
        pricing_result = PricingResult(
            postcode="B15 2HQ",
            care_type=CareType.RESIDENTIAL,
            local_authority="Birmingham",
            region="West Midlands",
            base_price_gbp=1000.0,
            msif_lower_bound_gbp=800.0,
            final_price_gbp=1000.0,
            expected_range_min_gbp=900.0,
            expected_range_max_gbp=1100.0,
            adjustments={},
            adjustment_total_percent=0.0,
            affordability_band="C",
            band_score=0.5,
            band_confidence_percent=75,
            band_reasoning="Test",
            fair_cost_gap_gbp=200.0,
            fair_cost_gap_percent=25.0,
            cqc_rating=None,
            facilities_score=None,
            bed_count=None,
            is_chain=False,
            scraped_price_gbp=None,
            negotiation_leverage_text="Test",
            sources_used=[]
        )
        
        savings = calc.calculate_all_savings(
            profile=profile,
            pricing_result=pricing_result,
            chc_probability=50,
            la_top_up_probability=30
        )
        
        assert savings.annual_gbp > 0
        assert savings.five_year_gbp == savings.annual_gbp * 5
        assert savings.weekly_savings > 0
    
    def test_savings_without_pricing_result(self):
        """Test savings calculation without PricingResult."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(age=80)
        
        savings = calc.calculate_all_savings(
            profile=profile,
            pricing_result=None,
            chc_probability=50,
            la_top_up_probability=30
        )
        
        assert savings.annual_gbp > 0
        assert savings.five_year_gbp == savings.annual_gbp * 5


class TestFullCalculation:
    """Test full eligibility calculation."""
    
    def test_full_calculation_with_dict(self):
        """Test full calculation with dict input."""
        calc = FundingEligibilityCalculator()
        
        profile_dict = {
            "age": 80,
            "domain_assessments": {
                "cognition": {
                    "domain": "cognition",
                    "level": "severe",
                    "description": "Severe dementia"
                },
                "mobility": {
                    "domain": "mobility",
                    "level": "severe",
                    "description": "Bedbound"
                }
            },
            "capital_assets": 15000.0,
            "weekly_income": 200.0,
            "care_type": "residential",
            "is_permanent_care": True
        }
        
        result = calc.calculate_full_eligibility(patient_profile=profile_dict)
        
        assert result.chc_eligibility.probability_percent >= 92
        assert result.la_support is not None
        assert result.dpa_eligibility is not None
        assert result.savings is not None
        assert len(result.recommendations) > 0
    
    def test_full_calculation_with_profile_object(self):
        """Test full calculation with PatientProfile object."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            domain_assessments={
                Domain.COGNITION: DomainAssessment(
                    domain=Domain.COGNITION,
                    level=DomainLevel.HIGH,
                    description="High cognitive needs"
                )
            },
            capital_assets=15000.0,
            weekly_income=200.0
        )
        
        result = calc.calculate_full_eligibility(patient_profile=profile)
        
        assert result.chc_eligibility is not None
        assert result.la_support is not None
        assert result.dpa_eligibility is not None
        assert result.savings is not None


class TestReportGeneration:
    """Test report generation."""
    
    def test_generate_full_report(self):
        """Test full report generation."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            domain_assessments={
                Domain.COGNITION: DomainAssessment(
                    domain=Domain.COGNITION,
                    level=DomainLevel.HIGH,
                    description="High cognitive needs"
                )
            },
            capital_assets=15000.0
        )
        
        result = calc.calculate_full_eligibility(patient_profile=profile)
        report = calc.generate_report(result, report_type="full")
        
        assert len(report) > 0
        assert "CHC" in report or "chc" in report.lower()
        assert "Funding" in report or "funding" in report.lower()
    
    def test_generate_teaser_report(self):
        """Test teaser report generation."""
        calc = FundingEligibilityCalculator()
        
        profile = PatientProfile(
            age=80,
            domain_assessments={
                Domain.COGNITION: DomainAssessment(
                    domain=Domain.COGNITION,
                    level=DomainLevel.HIGH,
                    description="High cognitive needs"
                )
            },
            capital_assets=15000.0
        )
        
        result = calc.calculate_full_eligibility(patient_profile=profile)
        report = calc.generate_report(result, report_type="teaser")
        
        assert len(report) > 0
        assert "CHC" in report or "chc" in report.upper()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

