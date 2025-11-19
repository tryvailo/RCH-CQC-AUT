"""Calculate Affordability Bands (A-E) with confidence scores."""

from typing import Optional
import structlog
from .models import BandResult

logger = structlog.get_logger(__name__)


def calculate_band(
    base_private_avg: float,
    fair_cost_lower: Optional[float],
    cqc_rating: Optional[str] = None,
    facilities_score: Optional[int] = None,
    bed_count: Optional[int] = None,
    is_chain: bool = False
) -> BandResult:
    """
    Calculate Affordability Band (A-E) with confidence.
    
    Band definitions:
    - A: Excellent value (private_avg <= fair_cost * 1.05, or <£800/week)
    - B: Good value (fair_cost * 1.05 < private_avg <= fair_cost * 1.15, or £800-950/week)
    - C: Fair value (fair_cost * 1.15 < private_avg <= fair_cost * 1.25, or £950-1100/week)
    - D: Premium pricing (fair_cost * 1.25 < private_avg <= fair_cost * 1.40, or £1100-1300/week)
    - E: Very expensive (private_avg > fair_cost * 1.40, or >£1300/week)
    
    Confidence adjustments:
    - Base confidence: 80%
    - +10% if fair_cost_lower is available
    - +5% if CQC rating is Outstanding
    - +5% if facilities_score >= 15
    - -5% if facilities_score < 10
    - -5% if bed_count < 10 (small homes may have higher per-bed costs)
    - +5% if is_chain (chains have more predictable pricing)
    
    Args:
        base_private_avg: Base private average price per week (GBP)
        fair_cost_lower: MSIF fair cost lower bound (GBP per week), optional
        cqc_rating: CQC rating (Outstanding/Good/Requires Improvement/Inadequate), optional
        facilities_score: Facilities score (0-20), optional
        bed_count: Number of beds, optional
        is_chain: Whether care home is part of a chain
        
    Returns:
        BandResult with band (A-E) and confidence percentage
    """
    logger.info(
        "Calculating affordability band",
        base_private_avg=base_private_avg,
        fair_cost_lower=fair_cost_lower,
        cqc_rating=cqc_rating,
        facilities_score=facilities_score,
        bed_count=bed_count,
        is_chain=is_chain
    )
    
    # Start with base confidence
    confidence = 80
    reasoning_parts = []
    
    # Adjust base price based on factors
    adjusted_price = base_private_avg
    
    # CQC rating adjustments
    if cqc_rating:
        rating_upper = cqc_rating.upper()
        if rating_upper == "OUTSTANDING":
            adjusted_price *= 1.05  # Outstanding homes command premium
            confidence += 5
            reasoning_parts.append("Outstanding CQC rating adds premium")
        elif rating_upper == "GOOD":
            # No adjustment
            reasoning_parts.append("Good CQC rating")
        elif rating_upper in ["REQUIRES IMPROVEMENT", "INADEQUATE"]:
            adjusted_price *= 0.95  # Lower ratings may reduce price
            confidence -= 5
            reasoning_parts.append(f"{cqc_rating} CQC rating may reduce value")
    
    # Facilities score adjustments
    if facilities_score is not None:
        if facilities_score >= 15:
            adjusted_price *= 1.03  # High facilities score adds value
            confidence += 5
            reasoning_parts.append(f"High facilities score ({facilities_score}/20)")
        elif facilities_score < 10:
            adjusted_price *= 0.97  # Low facilities score reduces value
            confidence -= 5
            reasoning_parts.append(f"Low facilities score ({facilities_score}/20)")
    
    # Bed count adjustments
    if bed_count is not None:
        if bed_count < 10:
            adjusted_price *= 1.05  # Small homes have higher per-bed costs
            confidence -= 5
            reasoning_parts.append(f"Small home ({bed_count} beds) may have higher costs")
        elif bed_count > 50:
            adjusted_price *= 0.98  # Large homes may have economies of scale
            reasoning_parts.append(f"Large home ({bed_count} beds) may have economies of scale")
    
    # Chain adjustments
    if is_chain:
        confidence += 5
        reasoning_parts.append("Chain home has more predictable pricing")
    
    # Calculate band
    if fair_cost_lower and fair_cost_lower > 0:
        confidence += 10  # Having fair cost data increases confidence
        ratio = adjusted_price / fair_cost_lower
        
        if ratio <= 1.05:
            band = "A"
            reasoning_parts.append(f"Price ({adjusted_price:.0f}) is within 5% of fair cost ({fair_cost_lower:.0f})")
        elif ratio <= 1.15:
            band = "B"
            reasoning_parts.append(f"Price ({adjusted_price:.0f}) is {ratio:.1%} of fair cost ({fair_cost_lower:.0f})")
        elif ratio <= 1.25:
            band = "C"
            reasoning_parts.append(f"Price ({adjusted_price:.0f}) is {ratio:.1%} of fair cost ({fair_cost_lower:.0f})")
        elif ratio <= 1.40:
            band = "D"
            reasoning_parts.append(f"Price ({adjusted_price:.0f}) is {ratio:.1%} of fair cost ({fair_cost_lower:.0f})")
        else:
            band = "E"
            reasoning_parts.append(f"Price ({adjusted_price:.0f}) is {ratio:.1%} of fair cost ({fair_cost_lower:.0f})")
    else:
        # Fallback to absolute pricing bands if no fair cost data
        confidence -= 10  # Less confidence without fair cost comparison
        
        if adjusted_price < 800:
            band = "A"
            reasoning_parts.append(f"Price ({adjusted_price:.0f}) is below £800/week threshold")
        elif adjusted_price < 950:
            band = "B"
            reasoning_parts.append(f"Price ({adjusted_price:.0f}) is in £800-950/week range")
        elif adjusted_price < 1100:
            band = "C"
            reasoning_parts.append(f"Price ({adjusted_price:.0f}) is in £950-1100/week range")
        elif adjusted_price < 1300:
            band = "D"
            reasoning_parts.append(f"Price ({adjusted_price:.0f}) is in £1100-1300/week range")
        else:
            band = "E"
            reasoning_parts.append(f"Price ({adjusted_price:.0f}) is above £1300/week threshold")
    
    # Ensure confidence is within bounds
    confidence = max(60, min(100, confidence))
    
    reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Base calculation"
    
    logger.info(
        "Band calculated",
        band=band,
        confidence=confidence,
        adjusted_price=adjusted_price
    )
    
    return BandResult(
        band=band,
        confidence_percent=confidence,
        reasoning=reasoning
    )

