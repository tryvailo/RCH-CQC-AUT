"""Pydantic models for pricing core module."""

from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class CareType(str, Enum):
    """Care type enumeration."""
    RESIDENTIAL = "residential"
    NURSING = "nursing"
    RESIDENTIAL_DEMENTIA = "residential_dementia"
    NURSING_DEMENTIA = "nursing_dementia"
    RESPITE = "respite"


class PricingResult(BaseModel):
    """Complete pricing calculation result."""
    
    # Input
    postcode: str = Field(..., description="Input postcode")
    care_type: CareType = Field(..., description="Care type")
    local_authority: str = Field(..., description="Local authority")
    region: str = Field(..., description="UK region")
    
    # Pricing data
    base_price_gbp: float = Field(..., description="Base price (Lottie regional average)")
    msif_lower_bound_gbp: Optional[float] = Field(None, description="MSIF 2025-2026 median fee (lower bound)")
    final_price_gbp: float = Field(..., description="Final calculated price after adjustments")
    expected_range_min_gbp: float = Field(..., description="Expected minimum price")
    expected_range_max_gbp: float = Field(..., description="Expected maximum price")
    
    # Adjustments applied
    adjustments: dict[str, float] = Field(default_factory=dict, description="Applied adjustments (%)")
    adjustment_total_percent: float = Field(0.0, description="Total adjustment percentage")
    
    # Affordability band
    affordability_band: Literal["A", "B", "C", "D", "E"] = Field(..., description="Affordability band")
    band_score: float = Field(..., description="Band score (0-1)")
    band_confidence_percent: int = Field(..., ge=60, le=100, description="Band confidence percentage")
    band_reasoning: str = Field(..., description="Band calculation reasoning")
    
    # Gap analysis
    fair_cost_gap_gbp: float = Field(..., description="Gap between final price and MSIF lower bound")
    fair_cost_gap_percent: float = Field(..., description="Gap as percentage")
    
    # Additional context
    cqc_rating: Optional[str] = Field(None, description="CQC rating if provided")
    facilities_score: Optional[int] = Field(None, ge=0, le=20, description="Facilities score if provided")
    bed_count: Optional[int] = Field(None, gt=0, description="Bed count if provided")
    is_chain: bool = Field(default=False, description="Whether care home is part of a chain")
    scraped_price_gbp: Optional[float] = Field(None, description="Scraped price if provided (overrides calculation)")
    
    # Output text
    negotiation_leverage_text: str = Field(..., description="Ready-to-use text for PDF report")
    sources_used: list[str] = Field(default_factory=list, description="Data sources used")
    
    @field_validator("band_score")
    @classmethod
    def validate_band_score(cls, v: float) -> float:
        """Validate band score is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("Band score must be between 0 and 1")
        return v

