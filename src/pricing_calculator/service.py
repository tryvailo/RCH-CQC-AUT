"""Main PricingService facade for pricing calculations."""

from typing import Optional, List, Dict
import structlog
from .models import CareType, PricingResult
from .fair_cost_loader import load_fair_cost_data
from .lottie_scraper import get_lottie_price_sync
from .postcode_mapper import get_postcode_info, PostcodeMapper
from .band_calculator import calculate_band
from .exceptions import PricingCalculatorError

logger = structlog.get_logger(__name__)


class PricingService:
    """
    Main service for pricing calculations and Affordability Bands.
    
    This is the primary interface for all pricing calculations.
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize PricingService.
        
        Args:
            cache_dir: Optional cache directory path for data files
        """
        logger.info("Initializing PricingService")
        
        self.fair_cost_data: dict = {}
        self.postcode_mapper = PostcodeMapper()
        
        # Load fair cost data (synchronous, cached)
        try:
            self.fair_cost_data = load_fair_cost_data()
            logger.info("Loaded fair cost data", la_count=len(self.fair_cost_data))
        except Exception as e:
            logger.warning("Failed to load fair cost data", error=str(e))
            self.fair_cost_data = {}
    
    def get_pricing_for_postcode(
        self,
        postcode: str,
        care_type: CareType,
        cqc_rating: Optional[str] = None,
        facilities_score: Optional[int] = None,
        bed_count: Optional[int] = None,
        is_chain: bool = False
    ) -> PricingResult:
        """
        Get complete pricing calculation for a postcode and care type.
        
        Args:
            postcode: UK postcode
            care_type: Type of care required
            cqc_rating: Optional CQC rating (Outstanding/Good/Requires Improvement/Inadequate)
            facilities_score: Optional facilities score (0-20)
            bed_count: Optional number of beds
            is_chain: Whether care home is part of a chain
            
        Returns:
            PricingResult with all calculated values
            
        Raises:
            PricingCalculatorError: If calculation fails
        """
        logger.info(
            "Calculating pricing",
            postcode=postcode,
            care_type=care_type.value,
            cqc_rating=cqc_rating,
            facilities_score=facilities_score,
            bed_count=bed_count,
            is_chain=is_chain
        )
        
        try:
            # 1. Get postcode info (Local Authority, Region)
            postcode_info = self.postcode_mapper.get_postcode_info(postcode)
            logger.debug("Postcode info", info=postcode_info.model_dump())
            
            # 2. Get fair cost lower bound (MSIF median)
            fair_cost_lower = None
            care_type_key = care_type.value
            
            if postcode_info.local_authority in self.fair_cost_data:
                la_data = self.fair_cost_data[postcode_info.local_authority]
                fair_cost_lower = la_data.get(care_type_key)
            
            # 3. Get private average (Lottie 2025)
            private_average = get_lottie_price_sync(
                postcode_info.region,
                care_type
            )
            
            if private_average == 0:
                raise PricingCalculatorError(
                    f"No Lottie data available for region: {postcode_info.region}, "
                    f"care_type: {care_type.value}"
                )
            
            # 4. Calculate expected range
            # Range is typically ±15% of private average
            expected_range_min = private_average * 0.85
            expected_range_max = private_average * 1.15
            
            # Adjust range based on fair cost if available
            if fair_cost_lower:
                # Range should span from fair_cost to private_average + margin
                expected_range_min = min(expected_range_min, fair_cost_lower * 0.95)
                expected_range_max = max(expected_range_max, private_average * 1.20)
            
            # 5. Calculate affordability band
            band_result = calculate_band(
                base_private_avg=private_average,
                fair_cost_lower=fair_cost_lower,
                cqc_rating=cqc_rating,
                facilities_score=facilities_score,
                bed_count=bed_count,
                is_chain=is_chain
            )
            
            # 6. Calculate fair cost gap
            if fair_cost_lower:
                fair_cost_gap_gbp = private_average - fair_cost_lower
                fair_cost_gap_percent = (fair_cost_gap_gbp / fair_cost_lower) * 100
            else:
                fair_cost_gap_gbp = 0.0
                fair_cost_gap_percent = 0.0
            
            # 7. Generate negotiation leverage text
            negotiation_text = self._generate_negotiation_text(
                postcode_info=postcode_info,
                care_type=care_type,
                private_average=private_average,
                fair_cost_lower=fair_cost_lower,
                band=band_result.band,
                gap_gbp=fair_cost_gap_gbp,
                gap_percent=fair_cost_gap_percent,
                cqc_rating=cqc_rating
            )
            
            # 8. Build sources list
            sources = ["Lottie 2025 Regional Averages"]
            if fair_cost_lower:
                sources.append("MSIF 2025-2026 Fair Cost Data")
            if cqc_rating:
                sources.append("CQC Rating")
            
            # 9. Create result
            result = PricingResult(
                postcode=postcode,
                care_type=care_type,
                local_authority=postcode_info.local_authority,
                region=postcode_info.region,
                fair_cost_lower_bound_gbp=fair_cost_lower,
                private_average_gbp=private_average,
                expected_range_min_gbp=expected_range_min,
                expected_range_max_gbp=expected_range_max,
                affordability_band=band_result.band,
                band_confidence_percent=band_result.confidence_percent,
                fair_cost_gap_gbp=fair_cost_gap_gbp,
                fair_cost_gap_percent=fair_cost_gap_percent,
                negotiation_leverage_text=negotiation_text,
                sources_used=sources,
                cqc_rating=cqc_rating,
                facilities_score=facilities_score,
                bed_count=bed_count,
                is_chain=is_chain
            )
            
            logger.info(
                "Pricing calculated",
                band=band_result.band,
                confidence=band_result.confidence_percent,
                private_avg=private_average,
                fair_cost=fair_cost_lower
            )
            
            return result
            
        except Exception as e:
            logger.error("Failed to calculate pricing", error=str(e), postcode=postcode)
            raise PricingCalculatorError(f"Failed to calculate pricing: {e}") from e
    
    def get_all_locations_pricing(
        self,
        care_type: Optional[CareType] = None
    ) -> List[Dict]:
        """
        Get pricing data for all Local Authorities.
        
        This method returns a list of all locations with their pricing data,
        suitable for displaying in a table interface.
        
        Args:
            care_type: Optional care type filter. If None, returns all care types.
            
        Returns:
            List of dicts with location and pricing data
        """
        logger.info("Getting all locations pricing", care_type=care_type.value if care_type else None)
        
        result = []
        
        # Get all Local Authorities from MSIF data
        for la_name, la_data in self.fair_cost_data.items():
            # Try to get region for this LA (we'll need to map LA to region)
            # For now, we'll use a simplified approach
            
            # Get care types available for this LA
            care_types_to_process = [care_type] if care_type else [
                CareType.RESIDENTIAL,
                CareType.NURSING,
                CareType.RESIDENTIAL_DEMENTIA,
                CareType.NURSING_DEMENTIA,
                CareType.RESPITE
            ]
            
            for ct in care_types_to_process:
                fair_cost = la_data.get(ct.value)
                
                # Estimate region from LA name (simplified - in production would use proper mapping)
                region = self._estimate_region_from_la(la_name)
                
                # Get Lottie price for region
                lottie_price = get_lottie_price_sync(region, ct)
                
                # Calculate band
                band_result = calculate_band(
                    base_private_avg=lottie_price,
                    fair_cost_lower=fair_cost
                )
                
                gap_gbp = lottie_price - fair_cost if fair_cost else 0.0
                gap_percent = (gap_gbp / fair_cost * 100) if fair_cost and fair_cost > 0 else 0.0
                
                result.append({
                    "local_authority": la_name,
                    "region": region,
                    "care_type": ct.value,
                    "fair_cost_lower_bound_gbp": fair_cost,
                    "private_average_gbp": lottie_price,
                    "affordability_band": band_result.band,
                    "band_confidence_percent": band_result.confidence_percent,
                    "fair_cost_gap_gbp": gap_gbp,
                    "fair_cost_gap_percent": gap_percent,
                })
        
        logger.info("Generated pricing data", locations=len(result))
        return result
    
    def _estimate_region_from_la(self, la_name: str) -> str:
        """
        Estimate region from Local Authority name.
        This is a simplified mapping - in production would use proper ONS data.
        """
        la_lower = la_name.lower()
        
        # London boroughs
        london_boroughs = ["westminster", "camden", "islington", "hackney", "tower hamlets",
                           "greenwich", "lewisham", "southwark", "lambeth", "wandsworth",
                           "hammersmith", "kensington", "chelsea", "fulham", "brent",
                           "ealing", "hounslow", "richmond", "kingston", "merton",
                           "sutton", "croydon", "bromley", "bexley", "greenwich",
                           "hackney", "haringey", "enfield", "barnet", "harrow",
                           "hillingdon", "barking", "dagenham", "havering", "redbridge",
                           "newham", "waltham", "forest"]
        
        if any(borough in la_lower for borough in london_boroughs):
            return "London"
        
        # Regional keywords
        if any(word in la_lower for word in ["kent", "sussex", "surrey", "hampshire", "berkshire", "oxfordshire"]):
            return "South East"
        if any(word in la_lower for word in ["devon", "cornwall", "somerset", "dorset", "wiltshire", "gloucestershire"]):
            return "South West"
        if any(word in la_lower for word in ["birmingham", "coventry", "wolverhampton", "dudley", "walsall", "sandwell", "solihull"]):
            return "West Midlands"
        if any(word in la_lower for word in ["leicester", "nottingham", "derby", "northampton", "lincoln"]):
            return "East Midlands"
        if any(word in la_lower for word in ["york", "leeds", "sheffield", "bradford", "hull", "doncaster"]):
            return "Yorkshire and the Humber"
        if any(word in la_lower for word in ["manchester", "liverpool", "bolton", "bury", "oldham", "rochdale", "salford", "stockport", "tameside", "trafford", "wigan"]):
            return "North West"
        if any(word in la_lower for word in ["newcastle", "sunderland", "middlesbrough", "durham", "gateshead"]):
            return "North East"
        if any(word in la_lower for word in ["norfolk", "suffolk", "cambridgeshire", "essex", "hertfordshire", "bedfordshire"]):
            return "East of England"
        
        # Default fallback
        return "England"
    
    def _generate_negotiation_text(
        self,
        postcode_info,
        care_type: CareType,
        private_average: float,
        fair_cost_lower: Optional[float],
        band: str,
        gap_gbp: float,
        gap_percent: float,
        cqc_rating: Optional[str]
    ) -> str:
        """
        Generate negotiation leverage text for PDF report.
        
        Args:
            postcode_info: PostcodeInfo object
            care_type: Care type
            private_average: Private average price
            fair_cost_lower: Fair cost lower bound
            band: Affordability band
            gap_gbp: Gap in GBP
            gap_percent: Gap as percentage
            cqc_rating: CQC rating
            
        Returns:
            Formatted text for report
        """
        care_type_display = care_type.value.replace("_", " ").title()
        
        lines = [
            f"**Pricing Analysis for {care_type_display} Care in {postcode_info.local_authority}**",
            "",
            f"The average private fee for {care_type_display.lower()} care in the {postcode_info.region} region "
            f"is approximately **£{private_average:.0f} per week** (based on Lottie 2025 regional data)."
        ]
        
        if fair_cost_lower:
            lines.extend([
                "",
                f"The MSIF 2025-2026 fair cost lower bound for {postcode_info.local_authority} is "
                f"**£{fair_cost_lower:.0f} per week**. This represents the median fee that local authorities "
                f"typically pay for care in this area.",
                "",
                f"The gap between private average and fair cost is **£{gap_gbp:.0f} per week** "
                f"({gap_percent:.1f}% above fair cost)."
            ])
        
        # Band-specific guidance
        band_guidance = {
            "A": (
                "This represents **excellent value** for money. The pricing is competitive and "
                "closely aligned with fair cost benchmarks. You have strong leverage in negotiations, "
                "as the care home is pricing competitively."
            ),
            "B": (
                "This represents **good value** for money. The pricing is reasonable and within "
                "acceptable margins. You have moderate leverage in negotiations, with room to discuss "
                "potential discounts or value-added services."
            ),
            "C": (
                "This represents **fair value**. The pricing is within market norms but may have "
                "some room for negotiation. Consider discussing package deals or longer-term commitments "
                "for potential discounts."
            ),
            "D": (
                "This represents **premium pricing**. The care home is charging significantly above "
                "fair cost benchmarks. You have strong leverage to negotiate, particularly if you can "
                "demonstrate comparable alternatives at lower prices."
            ),
            "E": (
                "This represents **very expensive** pricing. The care home is charging substantially "
                "above fair cost and market averages. You have very strong leverage to negotiate, "
                "and should consider exploring alternative options if negotiations are unsuccessful."
            ),
        }
        
        lines.extend([
            "",
            f"**Affordability Band: {band}**",
            band_guidance.get(band, ""),
        ])
        
        if cqc_rating:
            rating_display = cqc_rating.title()
            lines.append(
                f"\nThe care home has a **{rating_display}** CQC rating, which has been factored "
                "into the affordability assessment."
            )
        
        lines.extend([
            "",
            "**Negotiation Recommendations:**",
            f"- Use the fair cost benchmark (£{fair_cost_lower:.0f}/week)" if fair_cost_lower else "",
            f"- Compare with regional average (£{private_average:.0f}/week)",
            "- Request detailed breakdown of fees and services",
            "- Explore package deals for longer-term commitments",
            "- Consider asking about availability discounts or promotional rates",
        ])
        
        # Remove empty strings
        lines = [line for line in lines if line]
        
        return "\n".join(lines)
