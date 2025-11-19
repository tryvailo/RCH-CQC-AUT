"""
Pricing Calculator Module for RightCareHome

This module provides pricing calculations and Affordability Bands for UK care homes.
It integrates MSIF Fees data, Lottie regional averages, and postcode mapping.
"""

from .service import PricingService
from .models import CareType, PricingResult, PostcodeInfo, BandResult
from .postcode_mapper import get_postcode_info
from .lottie_scraper import get_lottie_price_sync
from .band_calculator import calculate_band

# API router for FastAPI integration
try:
    from .api import router as pricing_router
    __all__ = [
        "PricingService",
        "CareType",
        "PricingResult",
        "PostcodeInfo",
        "BandResult",
        "get_postcode_info",
        "get_lottie_price_sync",
        "calculate_band",
        "pricing_router",
    ]
except ImportError:
    # FastAPI not installed
    __all__ = [
        "PricingService",
        "CareType",
        "PricingResult",
        "PostcodeInfo",
        "BandResult",
        "get_postcode_info",
        "get_lottie_price_sync",
        "calculate_band",
    ]

__version__ = "1.0.0"
