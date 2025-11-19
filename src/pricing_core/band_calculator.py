"""Affordability Band v5 calculation logic."""

from typing import Optional
import structlog
from .models import PricingResult, CareType
from .exceptions import CalculationError

logger = structlog.get_logger(__name__)


class BandCalculatorV5:
    """Calculate Affordability Bands using v5 logic."""
    
    # Band thresholds (as fraction of range between MSIF lower and Lottie average)
    BAND_A_MAX = 0.05   # ≤5% above MSIF lower bound
    BAND_B_MAX = 0.15   # 5-15% above MSIF lower bound
    BAND_C_MAX = 0.25   # 15-25% above MSIF lower bound
    BAND_D_MAX = 0.40   # 25-40% above MSIF lower bound
    # BAND_E: >40% above MSIF lower bound
    
    @classmethod
    def calculate_band_score(
        cls,
        final_price: float,
        msif_lower: Optional[float],
        lottie_average: float
    ) -> float:
        """
        Calculate band score using v5 formula.
        
        Formula: (final_price - MSIF_lower) / (Lottie_average - MSIF_lower)
        
        Args:
            final_price: Final calculated price
            msif_lower: MSIF lower bound (median fee)
            lottie_average: Lottie regional average
            
        Returns:
            Band score (0-1, where 0 = MSIF lower, 1 = Lottie average)
        """
        if msif_lower is None:
            # Fallback: use absolute thresholds
            if final_price <= lottie_average * 0.95:
                return 0.0
            elif final_price <= lottie_average:
                return 0.5
            else:
                return min(1.0, (final_price - lottie_average) / lottie_average)
        
        # Normal case: use MSIF lower bound
        price_range = lottie_average - msif_lower
        
        if price_range <= 0:
            # Edge case: MSIF >= Lottie (shouldn't happen normally)
            logger.warning("MSIF lower >= Lottie average", msif_lower=msif_lower, lottie_average=lottie_average)
            if final_price <= msif_lower:
                return 0.0
            else:
                return min(1.0, (final_price - msif_lower) / msif_lower)
        
        band_score = (final_price - msif_lower) / price_range
        
        # Clamp to [0, 1]
        band_score = max(0.0, min(1.0, band_score))
        
        return band_score
    
    @classmethod
    def calculate_band(cls, band_score: float) -> tuple[str, str]:
        """
        Determine affordability band from band score.
        
        Args:
            band_score: Band score (0-1)
            
        Returns:
            Tuple of (band_letter, reasoning)
        """
        if band_score <= cls.BAND_A_MAX:
            band = "A"
            reasoning = (
                f"Excellent value: Price is ≤{cls.BAND_A_MAX*100:.0f}% above MSIF fair cost lower bound. "
                f"This represents exceptional affordability relative to government benchmarks."
            )
        elif band_score <= cls.BAND_B_MAX:
            band = "B"
            reasoning = (
                f"Good value: Price is {cls.BAND_A_MAX*100:.0f}-{cls.BAND_B_MAX*100:.0f}% above MSIF fair cost. "
                f"Competitive pricing within acceptable range."
            )
        elif band_score <= cls.BAND_C_MAX:
            band = "C"
            reasoning = (
                f"Fair value: Price is {cls.BAND_B_MAX*100:.0f}-{cls.BAND_C_MAX*100:.0f}% above MSIF fair cost. "
                f"Market-rate pricing, reasonable for the quality level."
            )
        elif band_score <= cls.BAND_D_MAX:
            band = "D"
            reasoning = (
                f"Premium pricing: Price is {cls.BAND_C_MAX*100:.0f}-{cls.BAND_D_MAX*100:.0f}% above MSIF fair cost. "
                f"Higher-end pricing reflecting premium facilities or location."
            )
        else:
            band = "E"
            reasoning = (
                f"Very expensive: Price is >{cls.BAND_D_MAX*100:.0f}% above MSIF fair cost. "
                f"Significant premium pricing, may require justification."
            )
        
        return band, reasoning
    
    @classmethod
    def calculate_confidence(
        cls,
        msif_lower: Optional[float],
        lottie_average: float,
        adjustments_applied: dict[str, float],
        cqc_rating: Optional[str] = None
    ) -> int:
        """
        Calculate confidence percentage for band calculation.
        
        Args:
            msif_lower: MSIF lower bound (None if not available)
            lottie_average: Lottie regional average
            adjustments_applied: Dict of adjustments applied
            cqc_rating: CQC rating if available
            
        Returns:
            Confidence percentage (60-100)
        """
        confidence = 100
        
        # Reduce confidence if MSIF data missing
        if msif_lower is None:
            confidence -= 20
            logger.debug("MSIF data missing, reducing confidence")
        
        # Reduce confidence if no adjustments applied (less precise)
        if not adjustments_applied:
            confidence -= 10
        
        # Increase confidence if CQC rating available
        if cqc_rating:
            confidence += 5
        
        # Clamp to [60, 100]
        confidence = max(60, min(100, confidence))
        
        return confidence
    
    @classmethod
    def calculate_expected_range(
        cls,
        final_price: float,
        band_score: float
    ) -> tuple[float, float]:
        """
        Calculate expected price range based on final price and band score.
        
        Args:
            final_price: Final calculated price
            band_score: Band score
            
        Returns:
            Tuple of (min_price, max_price)
        """
        # Range width depends on band
        if band_score <= cls.BAND_A_MAX:
            # Band A: narrow range (±3%)
            range_percent = 0.03
        elif band_score <= cls.BAND_B_MAX:
            # Band B: moderate range (±5%)
            range_percent = 0.05
        elif band_score <= cls.BAND_C_MAX:
            # Band C: wider range (±8%)
            range_percent = 0.08
        elif band_score <= cls.BAND_D_MAX:
            # Band D: wide range (±12%)
            range_percent = 0.12
        else:
            # Band E: very wide range (±15%)
            range_percent = 0.15
        
        min_price = final_price * (1 - range_percent)
        max_price = final_price * (1 + range_percent)
        
        return min_price, max_price

