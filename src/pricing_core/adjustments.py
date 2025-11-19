"""Price adjustment calculations for various factors."""

from typing import Optional
import structlog

logger = structlog.get_logger(__name__)


class PriceAdjustments:
    """Calculate price adjustments based on various factors."""
    
    # Adjustment percentages
    CQC_RATING_ADJUSTMENTS = {
        "Outstanding": 0.15,  # +15%
        "Good": 0.05,         # +5%
        "Requires Improvement": -0.05,  # -5%
        "Inadequate": -0.15,  # -15%
    }
    
    NURSING_ADJUSTMENT = 0.25  # +25% for nursing vs residential
    DEMENTIA_ADJUSTMENT = 0.12  # +12% for dementia care
    
    # Facilities score adjustment (0-20 scale)
    # Linear: 0 = -10%, 20 = +10%
    FACILITIES_MIN_ADJUSTMENT = -0.10
    FACILITIES_MAX_ADJUSTMENT = 0.10
    
    # Size adjustment (bed count)
    # Optimal: 30-50 beds = 0%
    # Smaller (<20): +5%
    # Larger (>60): -5%
    SIZE_OPTIMAL_MIN = 20
    SIZE_OPTIMAL_MAX = 60
    SIZE_SMALL_ADJUSTMENT = 0.05
    SIZE_LARGE_ADJUSTMENT = -0.05
    
    # Chain adjustment
    CHAIN_ADJUSTMENT = -0.08  # -8% for chain homes (economies of scale)
    
    @classmethod
    def calculate_cqc_adjustment(cls, cqc_rating: Optional[str]) -> float:
        """
        Calculate CQC rating adjustment.
        
        Args:
            cqc_rating: CQC rating string
            
        Returns:
            Adjustment percentage
        """
        if not cqc_rating:
            return 0.0
        
        rating = cqc_rating.strip()
        return cls.CQC_RATING_ADJUSTMENTS.get(rating, 0.0)
    
    @classmethod
    def calculate_care_type_adjustment(cls, care_type: str) -> float:
        """
        Calculate care type adjustment (nursing, dementia).
        
        Args:
            care_type: Care type string
            
        Returns:
            Adjustment percentage
        """
        adjustment = 0.0
        
        # Nursing adjustment
        if "nursing" in care_type.lower():
            adjustment += cls.NURSING_ADJUSTMENT
        
        # Dementia adjustment
        if "dementia" in care_type.lower():
            adjustment += cls.DEMENTIA_ADJUSTMENT
        
        return adjustment
    
    @classmethod
    def calculate_facilities_adjustment(cls, facilities_score: Optional[int]) -> float:
        """
        Calculate facilities score adjustment.
        
        Args:
            facilities_score: Facilities score (0-20)
            
        Returns:
            Adjustment percentage
        """
        if facilities_score is None:
            return 0.0
        
        # Linear interpolation: 0 -> -10%, 20 -> +10%
        normalized = facilities_score / 20.0
        adjustment = cls.FACILITIES_MIN_ADJUSTMENT + (
            (cls.FACILITIES_MAX_ADJUSTMENT - cls.FACILITIES_MIN_ADJUSTMENT) * normalized
        )
        
        return adjustment
    
    @classmethod
    def calculate_size_adjustment(cls, bed_count: Optional[int]) -> float:
        """
        Calculate size adjustment based on bed count.
        
        Args:
            bed_count: Number of beds
            
        Returns:
            Adjustment percentage
        """
        if bed_count is None:
            return 0.0
        
        if bed_count < cls.SIZE_OPTIMAL_MIN:
            return cls.SIZE_SMALL_ADJUSTMENT
        elif bed_count > cls.SIZE_OPTIMAL_MAX:
            return cls.SIZE_LARGE_ADJUSTMENT
        else:
            return 0.0
    
    @classmethod
    def calculate_chain_adjustment(cls, is_chain: bool) -> float:
        """
        Calculate chain adjustment.
        
        Args:
            is_chain: Whether care home is part of a chain
            
        Returns:
            Adjustment percentage
        """
        return cls.CHAIN_ADJUSTMENT if is_chain else 0.0
    
    @classmethod
    def calculate_all_adjustments(
        cls,
        care_type: str,
        cqc_rating: Optional[str] = None,
        facilities_score: Optional[int] = None,
        bed_count: Optional[int] = None,
        is_chain: bool = False
    ) -> dict[str, float]:
        """
        Calculate all adjustments.
        
        Args:
            care_type: Care type
            cqc_rating: CQC rating
            facilities_score: Facilities score (0-20)
            bed_count: Number of beds
            is_chain: Whether part of a chain
            
        Returns:
            Dict of adjustment name -> percentage
        """
        adjustments = {}
        
        # CQC rating
        cqc_adj = cls.calculate_cqc_adjustment(cqc_rating)
        if cqc_adj != 0:
            adjustments["cqc_rating"] = cqc_adj
        
        # Care type (nursing + dementia)
        care_adj = cls.calculate_care_type_adjustment(care_type)
        if care_adj != 0:
            adjustments["care_type"] = care_adj
        
        # Facilities
        facilities_adj = cls.calculate_facilities_adjustment(facilities_score)
        if facilities_adj != 0:
            adjustments["facilities"] = facilities_adj
        
        # Size
        size_adj = cls.calculate_size_adjustment(bed_count)
        if size_adj != 0:
            adjustments["size"] = size_adj
        
        # Chain
        chain_adj = cls.calculate_chain_adjustment(is_chain)
        if chain_adj != 0:
            adjustments["chain"] = chain_adj
        
        return adjustments
    
    @classmethod
    def apply_adjustments(cls, base_price: float, adjustments: dict[str, float]) -> float:
        """
        Apply adjustments to base price.
        
        Args:
            base_price: Base price
            adjustments: Dict of adjustment name -> percentage
            
        Returns:
            Adjusted price
        """
        total_adjustment = sum(adjustments.values())
        adjusted_price = base_price * (1 + total_adjustment)
        
        logger.debug(
            "Applied adjustments",
            base_price=base_price,
            adjustments=adjustments,
            total_adjustment=total_adjustment,
            adjusted_price=adjusted_price
        )
        
        return adjusted_price

