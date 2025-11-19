"""Tests for constants.py."""

from pricing_calculator.constants import get_lottie_average, REGION_NORMALIZATION
from pricing_calculator.models import CareType


def test_get_lottie_average_london():
    """Test Lottie average for London."""
    price = get_lottie_average("London", CareType.RESIDENTIAL)
    assert price == 950.0
    
    price_nursing = get_lottie_average("London", CareType.NURSING)
    assert price_nursing == 1200.0


def test_get_lottie_average_region_normalization():
    """Test region name normalization."""
    # Greater London should map to London
    price1 = get_lottie_average("Greater London", CareType.RESIDENTIAL)
    price2 = get_lottie_average("London", CareType.RESIDENTIAL)
    assert price1 == price2


def test_get_lottie_average_all_care_types():
    """Test all care types for a region."""
    region = "South East"
    
    residential = get_lottie_average(region, CareType.RESIDENTIAL)
    nursing = get_lottie_average(region, CareType.NURSING)
    residential_dementia = get_lottie_average(region, CareType.RESIDENTIAL_DEMENTIA)
    nursing_dementia = get_lottie_average(region, CareType.NURSING_DEMENTIA)
    respite = get_lottie_average(region, CareType.RESPITE)
    
    assert residential > 0
    assert nursing > residential  # Nursing should be more expensive
    assert residential_dementia >= residential  # Dementia care typically costs more
    assert nursing_dementia >= nursing
    assert respite > 0


def test_get_lottie_average_unknown_region():
    """Test fallback for unknown region."""
    price = get_lottie_average("Unknown Region", CareType.RESIDENTIAL)
    # Should fallback to England average
    assert price > 0


def test_region_normalization_mapping():
    """Test region normalization mapping."""
    assert REGION_NORMALIZATION["Greater London"] == "London"
    assert REGION_NORMALIZATION["South East England"] == "South East"
    assert REGION_NORMALIZATION["Yorkshire"] == "Yorkshire and the Humber"

