"""Pydantic models for pricing calculator."""

from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
import re


class CareType(str, Enum):
    """Care type enumeration."""
    RESIDENTIAL = "residential"
    NURSING = "nursing"
    RESIDENTIAL_DEMENTIA = "residential_dementia"
    NURSING_DEMENTIA = "nursing_dementia"
    RESPITE = "respite"


class PostcodeInfo(BaseModel):
    """Postcode information model."""
    postcode: str = Field(..., description="Normalized postcode")
    local_authority: str = Field(..., description="Local authority name")
    region: str = Field(..., description="UK region name")
    county: Optional[str] = Field(None, description="County name if available")
    country: str = Field(default="England", description="Country (default: England)")

    @field_validator("postcode")
    @classmethod
    def validate_postcode(cls, v: str) -> str:
        """Normalize postcode format."""
        # Remove spaces and convert to uppercase
        normalized = re.sub(r"\s+", "", v.upper())
        # Basic UK postcode validation
        if not re.match(r"^[A-Z]{1,2}[0-9]{1,2}[A-Z]?[0-9][A-Z]{2}$", normalized):
            raise ValueError(f"Invalid UK postcode format: {v}")
        # Format with space: SW1A 1AA
        if len(normalized) > 3:
            formatted = f"{normalized[:-3]} {normalized[-3:]}"
            return formatted
        return normalized


class BandResult(BaseModel):
    """Affordability band calculation result."""
    band: Literal["A", "B", "C", "D", "E"] = Field(..., description="Affordability band")
    confidence_percent: int = Field(..., ge=60, le=100, description="Confidence percentage")
    reasoning: str = Field(..., description="Explanation of band calculation")


class PricingResult(BaseModel):
    """Complete pricing calculation result."""
    postcode: str = Field(..., description="Input postcode")
    care_type: CareType = Field(..., description="Care type")
    local_authority: str = Field(..., description="Local authority")
    region: str = Field(..., description="UK region")
    
    # Pricing data
    fair_cost_lower_bound_gbp: Optional[float] = Field(
        None, 
        description="MSIF 2025-2026 median fee (fair cost lower bound)"
    )
    private_average_gbp: float = Field(..., description="Lottie 2025 baseline average")
    expected_range_min_gbp: float = Field(..., description="Expected minimum price")
    expected_range_max_gbp: float = Field(..., description="Expected maximum price")
    
    # Affordability band
    affordability_band: Literal["A", "B", "C", "D", "E"] = Field(..., description="Affordability band")
    band_confidence_percent: int = Field(..., ge=60, le=100, description="Band confidence percentage")
    
    # Gap analysis
    fair_cost_gap_gbp: float = Field(..., description="Gap between private average and fair cost")
    fair_cost_gap_percent: float = Field(..., description="Gap as percentage")
    
    # Output text
    negotiation_leverage_text: str = Field(..., description="Ready-to-use text for PDF report")
    sources_used: list[str] = Field(default_factory=list, description="Data sources used")
    
    # Additional context
    cqc_rating: Optional[str] = Field(None, description="CQC rating if provided")
    facilities_score: Optional[int] = Field(None, ge=0, le=20, description="Facilities score if provided")
    bed_count: Optional[int] = Field(None, gt=0, description="Bed count if provided")
    is_chain: bool = Field(default=False, description="Whether care home is part of a chain")

    @field_validator("fair_cost_gap_percent", mode="before")
    @classmethod
    def validate_gap_percent(cls, v: float) -> float:
        """Calculate gap percent if not provided."""
        # This will be calculated in service.py, so just return the value
        return v or 0.0

