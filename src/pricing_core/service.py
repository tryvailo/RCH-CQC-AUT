"""Main PricingService for pricing calculations."""

from typing import Optional
import structlog
from .models import PricingResult, CareType
from .adjustments import PriceAdjustments
from .band_calculator import BandCalculatorV5
from .exceptions import DataNotFoundError, InvalidInputError, CalculationError

# Import external modules
try:
    from postcode_resolver import PostcodeResolver
except ImportError:
    PostcodeResolver = None

try:
    from data_ingestion.database import get_db_connection
except ImportError:
    get_db_connection = None

# Import fallback constants for Lottie averages
try:
    from pricing_calculator.constants import get_lottie_average as get_lottie_average_fallback
    LOTTIE_FALLBACK_AVAILABLE = True
except ImportError:
    LOTTIE_FALLBACK_AVAILABLE = False
    get_lottie_average_fallback = None

logger = structlog.get_logger(__name__)


class PricingService:
    """Main pricing service with Band v5 logic."""
    
    def __init__(self):
        """Initialize PricingService."""
        self.postcode_resolver = PostcodeResolver() if PostcodeResolver else None
        self.adjustments = PriceAdjustments()
        self.band_calculator = BandCalculatorV5()
    
    def get_full_pricing(
        self,
        postcode: str,
        care_type: CareType,
        cqc_rating: Optional[str] = None,
        facilities_score: Optional[int] = None,
        bed_count: Optional[int] = None,
        is_chain: bool = False,
        scraped_price: Optional[float] = None
    ) -> PricingResult:
        """
        Calculate full pricing with Band v5 logic.
        
        Args:
            postcode: UK postcode
            care_type: Care type enum
            cqc_rating: Optional CQC rating
            facilities_score: Optional facilities score (0-20)
            bed_count: Optional bed count
            is_chain: Whether part of a chain
            scraped_price: Optional scraped price (overrides calculation)
            
        Returns:
            PricingResult object
            
        Raises:
            DataNotFoundError: If required data not found
            InvalidInputError: If input parameters invalid
            CalculationError: If calculation fails
        """
        logger.info(
            "Calculating pricing",
            postcode=postcode,
            care_type=care_type.value,
            cqc_rating=cqc_rating,
            facilities_score=facilities_score,
            bed_count=bed_count,
            is_chain=is_chain,
            scraped_price=scraped_price
        )
        
        # Validate inputs
        if facilities_score is not None and not (0 <= facilities_score <= 20):
            raise InvalidInputError("Facilities score must be between 0 and 20")
        
        if bed_count is not None and bed_count <= 0:
            raise InvalidInputError("Bed count must be positive")
        
        # Resolve postcode
        if not self.postcode_resolver:
            raise DataNotFoundError("Postcode resolver not available")
        
        try:
            postcode_info = self.postcode_resolver.resolve(postcode, use_cache=True)
            local_authority = postcode_info.local_authority
            region = postcode_info.region
        except Exception as e:
            logger.error("Failed to resolve postcode", postcode=postcode, error=str(e))
            raise DataNotFoundError(f"Failed to resolve postcode: {e}") from e
        
        # Load MSIF data
        msif_lower = self._get_msif_fee(local_authority, care_type)
        
        # Load Lottie data
        lottie_average = self._get_lottie_average(region, care_type)
        
        if lottie_average is None:
            raise DataNotFoundError(f"Lottie average not found for region: {region}, care_type: {care_type.value}")
        
        # Calculate base price (Lottie regional average)
        base_price = lottie_average
        
        # Apply adjustments if scraped_price not provided
        if scraped_price is not None:
            final_price = scraped_price
            adjustments = {}
            adjustment_total = 0.0
            logger.info("Using scraped price", scraped_price=scraped_price)
        else:
            # Calculate adjustments
            adjustments = self.adjustments.calculate_all_adjustments(
                care_type=care_type.value,
                cqc_rating=cqc_rating,
                facilities_score=facilities_score,
                bed_count=bed_count,
                is_chain=is_chain
            )
            
            adjustment_total = sum(adjustments.values())
            
            # Apply adjustments to base price
            final_price = self.adjustments.apply_adjustments(base_price, adjustments)
        
        # Calculate band score
        band_score = self.band_calculator.calculate_band_score(
            final_price=final_price,
            msif_lower=msif_lower,
            lottie_average=lottie_average
        )
        
        # Determine band
        band, band_reasoning = self.band_calculator.calculate_band(band_score)
        
        # Calculate confidence
        confidence = self.band_calculator.calculate_confidence(
            msif_lower=msif_lower,
            lottie_average=lottie_average,
            adjustments_applied=adjustments,
            cqc_rating=cqc_rating
        )
        
        # Calculate expected range
        expected_min, expected_max = self.band_calculator.calculate_expected_range(
            final_price=final_price,
            band_score=band_score
        )
        
        # Calculate gap
        if msif_lower:
            fair_cost_gap_gbp = final_price - msif_lower
            fair_cost_gap_percent = (fair_cost_gap_gbp / msif_lower) * 100
        else:
            fair_cost_gap_gbp = final_price - lottie_average
            fair_cost_gap_percent = (fair_cost_gap_gbp / lottie_average) * 100
        
        # Generate negotiation leverage text
        negotiation_text = self._generate_negotiation_text(
            final_price=final_price,
            msif_lower=msif_lower,
            lottie_average=lottie_average,
            band=band,
            band_score=band_score,
            adjustments=adjustments
        )
        
        # Build sources list
        sources = ["Lottie 2025 Regional Averages"]
        if msif_lower:
            sources.append("MSIF 2025-2026 Median Fees")
        if scraped_price:
            sources.append("Scraped Price")
        
        return PricingResult(
            postcode=postcode,
            care_type=care_type,
            local_authority=local_authority,
            region=region,
            base_price_gbp=base_price,
            msif_lower_bound_gbp=msif_lower,
            final_price_gbp=final_price,
            expected_range_min_gbp=expected_min,
            expected_range_max_gbp=expected_max,
            adjustments=adjustments,
            adjustment_total_percent=adjustment_total * 100,
            affordability_band=band,
            band_score=band_score,
            band_confidence_percent=confidence,
            band_reasoning=band_reasoning,
            fair_cost_gap_gbp=fair_cost_gap_gbp,
            fair_cost_gap_percent=fair_cost_gap_percent,
            cqc_rating=cqc_rating,
            facilities_score=facilities_score,
            bed_count=bed_count,
            is_chain=is_chain,
            scraped_price_gbp=scraped_price,
            negotiation_leverage_text=negotiation_text,
            sources_used=sources
        )
    
    def _get_msif_fee(self, local_authority: str, care_type: CareType) -> Optional[float]:
        """
        Get MSIF fee for local authority and care type.
        
        Args:
            local_authority: Local authority name
            care_type: Care type
            
        Returns:
            MSIF fee or None if not found
        """
        if not get_db_connection:
            logger.warning("Database connection not available")
            return None
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Map care_type to MSIF column
                column_map = {
                    CareType.RESIDENTIAL: "residential_fee_65_plus",
                    CareType.NURSING: "nursing_fee_65_plus",
                    CareType.RESIDENTIAL_DEMENTIA: "residential_dementia_fee",
                    CareType.NURSING_DEMENTIA: "nursing_dementia_fee",
                    CareType.RESPITE: "respite_fee",
                }
                
                column = column_map.get(care_type)
                if not column:
                    return None
                
                cursor.execute(f"""
                    SELECT {column}
                    FROM msif_fees_2025
                    WHERE local_authority = %s
                    LIMIT 1
                """, (local_authority,))
                
                row = cursor.fetchone()
                if row and row[0]:
                    return float(row[0])
                
                return None
        except Exception as e:
            logger.warning("Failed to get MSIF fee", la=local_authority, error=str(e))
            return None
    
    def _get_lottie_average(self, region: str, care_type: CareType) -> Optional[float]:
        """
        Get Lottie regional average for region and care type.
        
        Args:
            region: UK region name
            care_type: Care type
            
        Returns:
            Lottie average or None if not found
        """
        # Normalize region name for consistency
        normalized_region = region
        if LOTTIE_FALLBACK_AVAILABLE and get_lottie_average_fallback:
            try:
                from pricing_calculator.constants import REGION_NORMALIZATION
                normalized_region = REGION_NORMALIZATION.get(region, region)
            except ImportError:
                pass
        
        if not get_db_connection:
            logger.warning("Database connection not available")
            # Use fallback immediately if no database
            if LOTTIE_FALLBACK_AVAILABLE and get_lottie_average_fallback:
                logger.info("Using fallback Lottie average (no database)", region=normalized_region, care_type=care_type.value)
                fallback_price = get_lottie_average_fallback(normalized_region, care_type)
                if fallback_price and fallback_price > 0:
                    return fallback_price
            return None
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Map care_type to Lottie care_type
                care_type_map = {
                    CareType.RESIDENTIAL: "residential",
                    CareType.NURSING: "nursing",
                    CareType.RESIDENTIAL_DEMENTIA: "dementia",
                    CareType.NURSING_DEMENTIA: "dementia",
                    CareType.RESPITE: "residential",  # Respite typically same as residential
                }
                
                lottie_care_type = care_type_map.get(care_type, "residential")
                
                # Try with normalized region first
                cursor.execute("""
                    SELECT price_per_week
                    FROM lottie_regional_averages
                    WHERE region = %s AND care_type = %s
                    ORDER BY updated_at DESC
                    LIMIT 1
                """, (normalized_region, lottie_care_type))
                
                row = cursor.fetchone()
                if row and row[0]:
                    return float(row[0])
                
                # Try with original region name if different from normalized
                if normalized_region != region:
                    cursor.execute("""
                        SELECT price_per_week
                        FROM lottie_regional_averages
                        WHERE region = %s AND care_type = %s
                        ORDER BY updated_at DESC
                        LIMIT 1
                    """, (region, lottie_care_type))
                    
                    row = cursor.fetchone()
                    if row and row[0]:
                        return float(row[0])
                
                # Fallback: try residential if dementia not found
                if lottie_care_type == "dementia":
                    cursor.execute("""
                        SELECT price_per_week
                        FROM lottie_regional_averages
                        WHERE region = %s AND care_type = 'residential'
                        ORDER BY updated_at DESC
                        LIMIT 1
                    """, (region,))
                    
                    row = cursor.fetchone()
                    if row and row[0]:
                        # Apply dementia adjustment
                        return float(row[0]) * 1.12
                
                # Fallback to constants if database doesn't have data
                if LOTTIE_FALLBACK_AVAILABLE and get_lottie_average_fallback:
                    logger.info("Using fallback Lottie average from constants", region=normalized_region, care_type=care_type.value)
                    fallback_price = get_lottie_average_fallback(normalized_region, care_type)
                    if fallback_price and fallback_price > 0:
                        return fallback_price
                
                return None
        except Exception as e:
            logger.warning("Failed to get Lottie average from database", region=normalized_region, error=str(e))
            # Try fallback even on exception
            if LOTTIE_FALLBACK_AVAILABLE and get_lottie_average_fallback:
                try:
                    logger.info("Using fallback Lottie average from constants after error", region=normalized_region, care_type=care_type.value)
                    fallback_price = get_lottie_average_fallback(normalized_region, care_type)
                    if fallback_price and fallback_price > 0:
                        return fallback_price
                except Exception as fallback_error:
                    logger.warning("Fallback also failed", error=str(fallback_error))
            return None
    
    def _generate_negotiation_text(
        self,
        final_price: float,
        msif_lower: Optional[float],
        lottie_average: float,
        band: str,
        band_score: float,
        adjustments: dict[str, float]
    ) -> str:
        """
        Generate negotiation leverage text.
        
        Args:
            final_price: Final calculated price
            msif_lower: MSIF lower bound
            lottie_average: Lottie average
            band: Affordability band
            band_score: Band score
            adjustments: Applied adjustments
            
        Returns:
            Negotiation leverage text
        """
        lines = []
        
        lines.append(f"Pricing Analysis - Affordability Band {band}")
        lines.append("")
        
        if msif_lower:
            gap = final_price - msif_lower
            gap_percent = (gap / msif_lower) * 100
            lines.append(
                f"The calculated weekly fee of £{final_price:.2f} is "
                f"£{gap:.2f} ({gap_percent:+.1f}%) above the MSIF 2025-2026 "
                f"median fee of £{msif_lower:.2f} for this local authority."
            )
        else:
            lines.append(
                f"The calculated weekly fee of £{final_price:.2f} compares to "
                f"the regional average of £{lottie_average:.2f}."
            )
        
        lines.append("")
        lines.append(f"Band Assessment: {band}")
        
        if band in ["A", "B"]:
            lines.append(
                "This pricing represents good to excellent value relative to "
                "government benchmarks and regional averages."
            )
        elif band == "C":
            lines.append(
                "This pricing is fair and competitive, aligned with market rates "
                "for the quality level provided."
            )
        else:
            lines.append(
                "This pricing is at a premium level. Consider negotiating or "
                "requesting justification for the premium."
            )
        
        if adjustments:
            lines.append("")
            lines.append("Adjustments Applied:")
            for adj_name, adj_value in adjustments.items():
                lines.append(f"  - {adj_name.replace('_', ' ').title()}: {adj_value*100:+.1f}%")
        
        return "\n".join(lines)

