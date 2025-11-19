"""Pydantic models for Funding Eligibility Calculator 2025-2026."""

from typing import Optional, Dict, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from .constants import Domain, DomainLevel


class DomainAssessment(BaseModel):
    """Assessment for a single DST domain."""
    domain: Domain = Field(..., description="Domain name")
    level: DomainLevel = Field(..., description="Assessment level")
    description: str = Field(..., description="Description of assessment")
    evidence: Optional[str] = Field(None, description="Supporting evidence")


class PropertyDetails(BaseModel):
    """Property details for means test."""
    value: float = Field(..., ge=0, description="Property value in GBP")
    is_main_residence: bool = Field(True, description="Is main residence")
    has_qualifying_relative: bool = Field(False, description="Has qualifying relative living there")
    qualifying_relative_details: Optional[str] = Field(None, description="Details of qualifying relative")


class PatientProfile(BaseModel):
    """Enhanced patient profile for funding calculation."""
    
    # Basic info
    age: int = Field(..., ge=0, le=120, description="Patient age")
    
    # DST Domain assessments (12 domains)
    domain_assessments: Dict[Domain, DomainAssessment] = Field(
        default_factory=dict,
        description="Domain assessments"
    )
    
    # Additional health indicators
    has_primary_health_need: bool = Field(False, description="Has primary health need")
    requires_nursing_care: bool = Field(False, description="Requires nursing care")
    
    # Complex therapies
    has_peg_feeding: bool = Field(False, description="Has PEG/PEJ/NJ feeding")
    has_tracheostomy: bool = Field(False, description="Has tracheostomy")
    requires_injections: bool = Field(False, description="Requires regular injections")
    requires_ventilator: bool = Field(False, description="Requires ventilator support")
    requires_dialysis: bool = Field(False, description="Requires dialysis")
    
    # Unpredictability indicators
    has_unpredictable_needs: bool = Field(False, description="Has unpredictable needs")
    has_fluctuating_condition: bool = Field(False, description="Has fluctuating condition")
    has_high_risk_behaviours: bool = Field(False, description="Has high risk behaviours")
    
    # Financial
    capital_assets: float = Field(0.0, ge=0, description="Capital assets in GBP (excluding property)")
    weekly_income: float = Field(0.0, ge=0, description="Weekly income in GBP")
    property: Optional[PropertyDetails] = Field(None, description="Property details")
    
    # Care context
    care_type: Literal["residential", "nursing", "residential_dementia", "nursing_dementia", "respite"] = Field(
        "residential",
        description="Type of care"
    )
    is_permanent_care: bool = Field(True, description="Is permanent care (not respite)")
    
    @field_validator("capital_assets", "weekly_income")
    @classmethod
    def validate_financial(cls, v: float) -> float:
        """Validate financial values."""
        if v < 0:
            raise ValueError("Financial values cannot be negative")
        return v


class CHCEligibilityResult(BaseModel):
    """CHC eligibility calculation result."""
    
    probability_percent: int = Field(..., ge=0, le=98, description="CHC eligibility probability (max 98%)")
    is_likely_eligible: bool = Field(..., description="Whether likely eligible")
    reasoning: str = Field(..., description="Detailed reasoning")
    key_factors: List[str] = Field(default_factory=list, description="Key factors")
    domain_scores: Dict[str, int] = Field(default_factory=dict, description="Scores by domain")
    bonuses_applied: List[str] = Field(default_factory=list, description="Bonuses applied")
    threshold_category: Literal["very_high", "high", "moderate", "low"] = Field(
        ..., description="Threshold category"
    )


class LASupportResult(BaseModel):
    """Local Authority support calculation result."""
    
    top_up_probability_percent: int = Field(..., ge=0, le=100, description="Top-up probability")
    full_support_probability_percent: int = Field(..., ge=0, le=100, description="Full support probability")
    tariff_income_gbp_week: float = Field(..., ge=0, description="Tariff income per week")
    weekly_contribution: Optional[float] = Field(None, ge=0, description="Weekly contribution required")
    capital_assessed: float = Field(..., ge=0, description="Assessed capital (after property disregard)")
    is_fully_funded: bool = Field(..., description="Is fully funded by LA")
    reasoning: str = Field(..., description="Reasoning for LA support")


class DPAResult(BaseModel):
    """Deferred Payment Agreement eligibility result."""
    
    is_eligible: bool = Field(..., description="Is eligible for DPA")
    reasoning: str = Field(..., description="Reasoning for DPA eligibility")
    property_disregarded: bool = Field(..., description="Is property disregarded")
    weekly_charge: Optional[float] = Field(None, ge=0, description="Weekly charge if DPA")


class SavingsResult(BaseModel):
    """Savings calculation result."""
    
    annual_gbp: float = Field(..., ge=0, description="Annual savings in GBP")
    five_year_gbp: float = Field(..., ge=0, description="5-year savings in GBP")
    lifetime_gbp: Optional[float] = Field(None, ge=0, description="Lifetime savings estimate")
    weekly_savings: float = Field(..., ge=0, description="Weekly savings in GBP")
    breakdown: Dict[str, float] = Field(default_factory=dict, description="Savings breakdown by source")


class FundingEligibilityResult(BaseModel):
    """Complete funding eligibility calculation result."""
    
    # Input
    patient_profile: PatientProfile = Field(..., description="Input patient profile")
    calculation_date: datetime = Field(default_factory=datetime.now, description="Calculation date")
    
    # CHC eligibility
    chc_eligibility: CHCEligibilityResult = Field(..., description="CHC eligibility assessment")
    
    # LA support
    la_support: LASupportResult = Field(..., description="LA support assessment")
    
    # DPA
    dpa_eligibility: DPAResult = Field(..., description="DPA eligibility")
    
    # Savings
    savings: SavingsResult = Field(..., description="Potential savings")
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list, description="Funding recommendations")
    
    # Report generation
    report_text: Optional[str] = Field(None, description="Generated report text")
    
    def as_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return self.model_dump(mode='json', exclude_none=True)
