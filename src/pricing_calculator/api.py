"""FastAPI endpoints for pricing calculator."""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from .service import PricingService
from .models import CareType, PricingResult

router = APIRouter(prefix="/api/pricing", tags=["pricing"])

# Global service instance
_pricing_service: Optional[PricingService] = None


def get_pricing_service() -> PricingService:
    """Get or create PricingService instance."""
    global _pricing_service
    if _pricing_service is None:
        _pricing_service = PricingService()
    return _pricing_service


class LocationPricingRow(BaseModel):
    """Single row in locations pricing table."""
    local_authority: str
    region: str
    care_type: str
    fair_cost_lower_bound_gbp: Optional[float]
    private_average_gbp: float
    affordability_band: str
    band_confidence_percent: int
    fair_cost_gap_gbp: float
    fair_cost_gap_percent: float


class LocationsPricingResponse(BaseModel):
    """Response for all locations pricing."""
    total_locations: int
    care_types: List[str]
    data: List[LocationPricingRow]


@router.get("/postcode/{postcode}", response_model=PricingResult)
async def get_pricing_for_postcode(
    postcode: str,
    care_type: CareType = Query(..., description="Type of care"),
    cqc_rating: Optional[str] = Query(None, description="CQC rating"),
    facilities_score: Optional[int] = Query(None, ge=0, le=20, description="Facilities score"),
    bed_count: Optional[int] = Query(None, gt=0, description="Number of beds"),
    is_chain: bool = Query(False, description="Is part of a chain")
):
    """
    Get pricing calculation for a specific postcode.
    
    Returns complete pricing analysis including affordability band and negotiation leverage text.
    """
    try:
        service = get_pricing_service()
        result = service.get_pricing_for_postcode(
            postcode=postcode,
            care_type=care_type,
            cqc_rating=cqc_rating,
            facilities_score=facilities_score,
            bed_count=bed_count,
            is_chain=is_chain
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations")
async def get_all_locations_pricing(
    care_type: Optional[CareType] = Query(None, description="Filter by care type"),
    region: Optional[str] = Query(None, description="Filter by region"),
    min_fair_cost: Optional[float] = Query(None, description="Minimum fair cost"),
    max_fair_cost: Optional[float] = Query(None, description="Maximum fair cost"),
    band: Optional[str] = Query(None, description="Filter by affordability band (A-E)")
):
    """
    Get pricing data for all Local Authorities.
    
    Returns a table of all locations with their pricing data, suitable for display in UI.
    Supports filtering by care type, region, price range, and affordability band.
    """
    try:
        service = get_pricing_service()
        data = service.get_all_locations_pricing(care_type=care_type)
        
        # Apply filters
        if region:
            data = [row for row in data if row.get("region", "").lower() == region.lower()]
        
        if min_fair_cost is not None:
            data = [row for row in data if row.get("fair_cost_lower_bound_gbp") and row["fair_cost_lower_bound_gbp"] >= min_fair_cost]
        
        if max_fair_cost is not None:
            data = [row for row in data if row.get("fair_cost_lower_bound_gbp") and row["fair_cost_lower_bound_gbp"] <= max_fair_cost]
        
        if band:
            data = [row for row in data if row.get("affordability_band", "").upper() == band.upper()]
        
        # Return as dict for easier frontend consumption
        return {
            "data": data,
            "total": len(data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regions")
async def get_regions():
    """Get list of all available regions."""
    return {
        "regions": [
            "London",
            "South East",
            "South West",
            "West Midlands",
            "East Midlands",
            "Yorkshire and the Humber",
            "North West",
            "North East",
            "East of England"
        ]
    }


@router.get("/care-types")
async def get_care_types():
    """Get list of all available care types."""
    return {
        "care_types": [ct.value for ct in CareType]
    }

