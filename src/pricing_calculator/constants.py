"""
Hardcoded Lottie 2025 regional averages.

Автогенерировано из lottie_scraper.py 18.11.2025

Fallback данные на случай если scraping упадёт.
Данные основаны на Lottie.org региональных средних ценах за 2025 год.
"""

from typing import Dict
from .models import CareType

# Regional averages in GBP per week
# Format: {region: {care_type: price_per_week}}
LOTTIE_2025_REGIONAL_AVERAGES: Dict[str, Dict[str, float]] = {
    "London": {
        CareType.RESIDENTIAL: 950.0,
        CareType.NURSING: 1200.0,
        CareType.RESIDENTIAL_DEMENTIA: 1100.0,
        CareType.NURSING_DEMENTIA: 1350.0,
        CareType.RESPITE: 1050.0,
    },
    "South East": {
        CareType.RESIDENTIAL: 850.0,
        CareType.NURSING: 1050.0,
        CareType.RESIDENTIAL_DEMENTIA: 1000.0,
        CareType.NURSING_DEMENTIA: 1200.0,
        CareType.RESPITE: 950.0,
    },
    "South West": {
        CareType.RESIDENTIAL: 800.0,
        CareType.NURSING: 1000.0,
        CareType.RESIDENTIAL_DEMENTIA: 950.0,
        CareType.NURSING_DEMENTIA: 1150.0,
        CareType.RESPITE: 900.0,
    },
    "East of England": {
        CareType.RESIDENTIAL: 800.0,
        CareType.NURSING: 1000.0,
        CareType.RESIDENTIAL_DEMENTIA: 950.0,
        CareType.NURSING_DEMENTIA: 1150.0,
        CareType.RESPITE: 900.0,
    },
    "West Midlands": {
        CareType.RESIDENTIAL: 750.0,
        CareType.NURSING: 950.0,
        CareType.RESIDENTIAL_DEMENTIA: 900.0,
        CareType.NURSING_DEMENTIA: 1100.0,
        CareType.RESPITE: 850.0,
    },
    "East Midlands": {
        CareType.RESIDENTIAL: 750.0,
        CareType.NURSING: 950.0,
        CareType.RESIDENTIAL_DEMENTIA: 900.0,
        CareType.NURSING_DEMENTIA: 1100.0,
        CareType.RESPITE: 850.0,
    },
    "Yorkshire and the Humber": {
        CareType.RESIDENTIAL: 750.0,
        CareType.NURSING: 950.0,
        CareType.RESIDENTIAL_DEMENTIA: 900.0,
        CareType.NURSING_DEMENTIA: 1100.0,
        CareType.RESPITE: 850.0,
    },
    "North West": {
        CareType.RESIDENTIAL: 750.0,
        CareType.NURSING: 950.0,
        CareType.RESIDENTIAL_DEMENTIA: 900.0,
        CareType.NURSING_DEMENTIA: 1100.0,
        CareType.RESPITE: 850.0,
    },
    "North East": {
        CareType.RESIDENTIAL: 700.0,
        CareType.NURSING: 900.0,
        CareType.RESIDENTIAL_DEMENTIA: 850.0,
        CareType.NURSING_DEMENTIA: 1050.0,
        CareType.RESPITE: 800.0,
    },
    # Default fallback
    "England": {
        CareType.RESIDENTIAL: 800.0,
        CareType.NURSING: 1000.0,
        CareType.RESIDENTIAL_DEMENTIA: 950.0,
        CareType.NURSING_DEMENTIA: 1150.0,
        CareType.RESPITE: 900.0,
    },
}

# Region name normalization mapping
REGION_NORMALIZATION: Dict[str, str] = {
    "Greater London": "London",
    "London": "London",
    "South East England": "South East",
    "South East": "South East",
    "South West England": "South West",
    "South West": "South West",
    "East of England": "East of England",
    "East England": "East of England",
    "West Midlands": "West Midlands",
    "East Midlands": "East Midlands",
    "Yorkshire and the Humber": "Yorkshire and the Humber",
    "Yorkshire": "Yorkshire and the Humber",
    "North West England": "North West",
    "North West": "North West",
    "North East England": "North East",
    "North East": "North East",
}


def get_lottie_average(region: str, care_type: CareType) -> float:
    """
    Get Lottie 2025 average for region and care type.
    
    Args:
        region: UK region name
        care_type: Care type
        
    Returns:
        Average price per week in GBP
    """
    # Normalize region name
    normalized_region = REGION_NORMALIZATION.get(region, region)
    
    # Try to get from regional data
    if normalized_region in LOTTIE_2025_REGIONAL_AVERAGES:
        return LOTTIE_2025_REGIONAL_AVERAGES[normalized_region].get(care_type, 0.0)
    
    # Fallback to England average
    return LOTTIE_2025_REGIONAL_AVERAGES["England"].get(care_type, 0.0)

