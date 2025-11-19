"""CHC (Continuing Healthcare) eligibility calculator."""

from typing import Dict
import structlog
from .models import PatientProfile, CHCEligibilityResult, LAFundingResult
from .exceptions import InvalidPatientProfileError

logger = structlog.get_logger(__name__)


class FundingEligibilityCalculator:
    """Calculate funding eligibility for care home patients."""
    
    # CHC eligibility factors and weights
    CHC_FACTORS = {
        "primary_health_need": 40,  # Highest weight
        "nursing_care": 25,
        "dementia": 15,
        "parkinsons": 15,
        "stroke": 10,
        "heart_condition": 10,
        "diabetes": 5,
        "mobility_bedbound": 20,
        "mobility_wheelchair": 10,
        "medication_management": 10,
        "personal_care": 5,
    }
    
    # LA funding thresholds (2025-2026)
    CAPITAL_THRESHOLD = 23_250  # Below this, LA fully funds
    CAPITAL_UPPER_THRESHOLD = 186_000  # Above this, self-funding
    WEEKLY_INCOME_ALLOWANCE = 24.90  # Personal expenses allowance per week
    
    def calculate_chc_eligibility(self, profile: PatientProfile) -> CHCEligibilityResult:
        """
        Calculate CHC eligibility probability.
        
        Args:
            profile: Patient profile
            
        Returns:
            CHCEligibilityResult
        """
        logger.info("Calculating CHC eligibility", age=profile.age)
        
        score = 0
        key_factors = []
        
        # Primary health need (highest weight)
        if profile.has_primary_health_need:
            score += self.CHC_FACTORS["primary_health_need"]
            key_factors.append("Primary health need identified")
        
        # Nursing care requirement
        if profile.requires_nursing_care:
            score += self.CHC_FACTORS["nursing_care"]
            key_factors.append("Requires nursing care")
        
        # Health conditions
        if profile.has_dementia:
            score += self.CHC_FACTORS["dementia"]
            key_factors.append("Dementia diagnosis")
        
        if profile.has_parkinsons:
            score += self.CHC_FACTORS["parkinsons"]
            key_factors.append("Parkinson's disease")
        
        if profile.has_stroke:
            score += self.CHC_FACTORS["stroke"]
            key_factors.append("Stroke history")
        
        if profile.has_heart_condition:
            score += self.CHC_FACTORS["heart_condition"]
            key_factors.append("Heart condition")
        
        if profile.has_diabetes:
            score += self.CHC_FACTORS["diabetes"]
            key_factors.append("Diabetes")
        
        # Mobility
        if profile.mobility_level == "bedbound":
            score += self.CHC_FACTORS["mobility_bedbound"]
            key_factors.append("Bedbound")
        elif profile.mobility_level == "wheelchair":
            score += self.CHC_FACTORS["mobility_wheelchair"]
            key_factors.append("Wheelchair user")
        
        # Care needs
        if profile.requires_medication_management:
            score += self.CHC_FACTORS["medication_management"]
            key_factors.append("Requires medication management")
        
        if profile.requires_personal_care:
            score += self.CHC_FACTORS["personal_care"]
            key_factors.append("Requires personal care")
        
        # Age factor (older = slightly higher probability)
        if profile.age >= 85:
            score += 5
        elif profile.age >= 75:
            score += 3
        
        # Calculate probability (score out of 100, but can exceed)
        probability = min(100, int(score * 0.8))  # Scale down slightly
        
        # Ensure minimum probability if has primary health need
        if profile.has_primary_health_need:
            probability = max(probability, 60)
        
        is_likely = probability >= 50
        
        # Generate reasoning
        if is_likely:
            reasoning = (
                f"Based on the assessment, there is a {probability}% probability of CHC eligibility. "
                f"The patient demonstrates significant health needs that may qualify for NHS Continuing Healthcare funding."
            )
        else:
            reasoning = (
                f"Based on the assessment, there is a {probability}% probability of CHC eligibility. "
                f"While some health needs are present, they may not meet the threshold for primary health need."
            )
        
        return CHCEligibilityResult(
            probability_percent=probability,
            is_likely_eligible=is_likely,
            reasoning=reasoning,
            key_factors=key_factors
        )
    
    def calculate_la_funding(self, profile: PatientProfile) -> LAFundingResult:
        """
        Calculate Local Authority funding eligibility.
        
        Args:
            profile: Patient profile
            
        Returns:
            LAFundingResult
        """
        logger.info("Calculating LA funding", capital=profile.capital_assets)
        
        # Determine funding status
        if profile.capital_assets < self.CAPITAL_THRESHOLD:
            # Fully funded by LA
            top_up_probability = 0
            weekly_contribution = 0.0
            deferred_payment_eligible = False
            deferred_reasoning = "Fully funded by Local Authority (capital below threshold)"
        elif profile.capital_assets > self.CAPITAL_UPPER_THRESHOLD:
            # Self-funding
            top_up_probability = 0
            weekly_contribution = None
            deferred_payment_eligible = True
            deferred_reasoning = (
                f"Eligible for Deferred Payment Agreement. Capital assets (£{profile.capital_assets:,.0f}) "
                f"exceed upper threshold (£{self.CAPITAL_UPPER_THRESHOLD:,.0f})."
            )
        else:
            # Partial funding with potential top-up
            # Calculate weekly contribution
            weekly_contribution = max(0, profile.weekly_income - self.WEEKLY_INCOME_ALLOWANCE)
            
            # Top-up probability increases with care cost
            if profile.care_cost_per_week:
                if profile.care_cost_per_week > weekly_contribution + 100:
                    top_up_probability = 80
                elif profile.care_cost_per_week > weekly_contribution + 50:
                    top_up_probability = 60
                else:
                    top_up_probability = 30
            else:
                top_up_probability = 50
            
            deferred_payment_eligible = True
            deferred_reasoning = (
                f"Eligible for Deferred Payment Agreement. Capital assets (£{profile.capital_assets:,.0f}) "
                f"are between thresholds. Weekly contribution: £{weekly_contribution:.2f}."
            )
        
        return LAFundingResult(
            top_up_probability_percent=top_up_probability,
            deferred_payment_eligible=deferred_payment_eligible,
            deferred_payment_reasoning=deferred_reasoning,
            weekly_contribution=weekly_contribution
        )
    
    def calculate_potential_savings(
        self,
        profile: PatientProfile,
        chc_eligibility: CHCEligibilityResult,
        la_funding: LAFundingResult,
        current_weekly_cost: float
    ) -> Dict[str, float]:
        """
        Calculate potential savings from funding.
        
        Args:
            profile: Patient profile
            chc_eligibility: CHC eligibility result
            la_funding: LA funding result
            current_weekly_cost: Current weekly care cost
            
        Returns:
            Dict with savings per week, year, and 5 years
        """
        savings_per_week = 0.0
        
        # CHC savings (if eligible, NHS covers full cost)
        if chc_eligibility.is_likely_eligible:
            # Assume 70% of cost covered by CHC (conservative estimate)
            chc_savings = current_weekly_cost * 0.70
            savings_per_week += chc_savings
        
        # LA funding savings (reduction in top-up)
        if la_funding.weekly_contribution is not None:
            if current_weekly_cost > la_funding.weekly_contribution:
                # Potential savings from reduced top-up
                top_up_savings = (current_weekly_cost - la_funding.weekly_contribution) * 0.3  # 30% reduction
                savings_per_week += top_up_savings
        
        # Deferred payment savings (cash flow benefit)
        if la_funding.deferred_payment_eligible:
            # Deferred payment doesn't reduce cost but improves cash flow
            # Estimate 10% benefit from deferred payment
            deferred_savings = current_weekly_cost * 0.10
            savings_per_week += deferred_savings
        
        savings_per_year = savings_per_week * 52
        savings_5_years = savings_per_year * 5
        
        return {
            "per_week": savings_per_week,
            "per_year": savings_per_year,
            "5_years": savings_5_years
        }
    
    def calculate_full_eligibility(self, profile: PatientProfile) -> 'FundingEligibilityResult':
        """
        Calculate full funding eligibility.
        
        Args:
            profile: Patient profile
            
        Returns:
            FundingEligibilityResult
        """
        from .models import FundingEligibilityResult
        
        # Calculate CHC eligibility
        chc_eligibility = self.calculate_chc_eligibility(profile)
        
        # Calculate LA funding
        la_funding = self.calculate_la_funding(profile)
        
        # Calculate savings
        current_cost = profile.care_cost_per_week or 1000.0  # Default estimate
        savings = self.calculate_potential_savings(profile, chc_eligibility, la_funding, current_cost)
        
        # Generate recommendations
        recommendations = []
        
        if chc_eligibility.is_likely_eligible:
            recommendations.append(
                "Consider applying for NHS Continuing Healthcare (CHC) funding. "
                "This could cover a significant portion of care costs."
            )
        
        if la_funding.deferred_payment_eligible:
            recommendations.append(
                "You may be eligible for a Deferred Payment Agreement, allowing you to "
                "defer payment until your property is sold."
            )
        
        if la_funding.top_up_probability_percent > 50:
            recommendations.append(
                "Consider negotiating care home fees to reduce top-up requirements."
            )
        
        if not recommendations:
            recommendations.append(
                "Review all available funding options and consider seeking professional "
                "financial advice for care home funding."
            )
        
        return FundingEligibilityResult(
            patient_profile=profile,
            chc_eligibility=chc_eligibility,
            la_funding=la_funding,
            potential_savings_per_week=savings["per_week"],
            potential_savings_per_year=savings["per_year"],
            potential_savings_5_years=savings["5_years"],
            recommendations=recommendations
        )

