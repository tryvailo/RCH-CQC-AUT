"""Utility functions for funding eligibility calculations."""

from typing import Dict, List
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
from .constants import Domain, DomainLevel, CHC_WEIGHTS, CHC_BONUSES, DOMAIN_GROUPS
from .models import DomainAssessment, PatientProfile


def count_domain_levels(
    assessments: Dict[Domain, DomainAssessment],
    level: DomainLevel,
    domains: List[Domain] = None
) -> int:
    """
    Count domains with specific level.
    
    Args:
        assessments: Domain assessments
        level: Level to count
        domains: Optional list of domains to check (None = all)
        
    Returns:
        Count of domains with specified level
    """
    if domains is None:
        domains = list(assessments.keys())
    
    return sum(
        1 for domain in domains
        if domain in assessments and assessments[domain].level == level
    )


def calculate_chc_base_score(assessments: Dict[Domain, DomainAssessment]) -> int:
    """
    Calculate base CHC score from domain assessments.
    
    Args:
        assessments: Domain assessments
        
    Returns:
        Base score (before bonuses)
    """
    score = 0
    
    # Count levels
    priority_count = count_domain_levels(assessments, DomainLevel.PRIORITY)
    severe_count = count_domain_levels(assessments, DomainLevel.SEVERE)
    high_count = count_domain_levels(assessments, DomainLevel.HIGH)
    
    # Apply weights
    if priority_count > 0:
        score += CHC_WEIGHTS[DomainLevel.PRIORITY]
    
    score += severe_count * CHC_WEIGHTS[DomainLevel.SEVERE]
    score += high_count * CHC_WEIGHTS[DomainLevel.HIGH]
    
    return score


def calculate_chc_bonuses(
    assessments: Dict[Domain, DomainAssessment],
    profile: PatientProfile
) -> Dict[str, int]:
    """
    Calculate CHC bonus scores.
    
    Args:
        assessments: Domain assessments
        profile: Patient profile
        
    Returns:
        Dictionary of bonus name -> bonus score
    """
    bonuses = {}
    
    # Multiple Severe bonus (≥2 Severe in critical domains)
    critical_domains = DOMAIN_GROUPS["critical_domains"]
    severe_critical = count_domain_levels(assessments, DomainLevel.SEVERE, critical_domains)
    if severe_critical >= 2:
        bonuses["multiple_severe"] = CHC_BONUSES["multiple_severe"]
    
    # Unpredictability bonus
    if (profile.has_unpredictable_needs or 
        profile.has_fluctuating_condition or 
        profile.has_high_risk_behaviours):
        bonuses["unpredictability"] = CHC_BONUSES["unpredictability"]
    
    # Multiple High bonus (≥3 High in behavioural domains)
    behavioural_domains = DOMAIN_GROUPS["behavioural_domains"]
    high_behavioural = count_domain_levels(assessments, DomainLevel.HIGH, behavioural_domains)
    if high_behavioural >= 3:
        bonuses["multiple_high"] = CHC_BONUSES["multiple_high"]
    
    # Complex therapies bonus
    if (profile.has_peg_feeding or 
        profile.has_tracheostomy or 
        profile.requires_injections or 
        profile.requires_ventilator or 
        profile.requires_dialysis):
        bonuses["complex_therapies"] = CHC_BONUSES["complex_therapies"]
    
    return bonuses


def calculate_tariff_income(capital_assets: float) -> float:
    """
    Calculate tariff income from capital assets.
    
    Args:
        capital_assets: Capital assets (excluding property)
        
    Returns:
        Tariff income per week in GBP
    """
    from .constants import MEANS_TEST
    
    lower_limit = MEANS_TEST["lower_capital_limit"]
    rate = MEANS_TEST["tariff_income_rate"]
    
    if capital_assets <= lower_limit:
        return 0.0
    
    excess = capital_assets - lower_limit
    tariff_income = (excess // rate) + (1 if excess % rate > 0 else 0)
    
    return float(tariff_income)


def assess_property_for_means_test(property_details, dpa_eligible: bool) -> Dict[str, any]:
    """
    Assess property for means test.
    
    Args:
        property_details: PropertyDetails object
        dpa_eligible: Whether DPA eligible
        
    Returns:
        Dictionary with property assessment
    """
    if not property_details:
        return {
            "disregarded": True,
            "reason": "No property",
            "value_counted": 0.0
        }
    
    # Property disregarded if DPA eligible
    if dpa_eligible:
        return {
            "disregarded": True,
            "reason": "DPA eligible",
            "value_counted": 0.0
        }
    
    # Property disregarded if qualifying relative lives there
    if property_details.has_qualifying_relative:
        return {
            "disregarded": True,
            "reason": "Qualifying relative in residence",
            "value_counted": 0.0
        }
    
    return {
        "disregarded": False,
        "reason": "Property counted",
        "value_counted": property_details.value
    }


def calculate_chc_probability_range(
    priority_count: int,
    severe_count: int,
    high_count: int
) -> tuple[int, int, str]:
    """
    Calculate CHC probability range based on domain levels.
    
    Args:
        priority_count: Number of PRIORITY domains
        severe_count: Number of SEVERE domains
        high_count: Number of HIGH domains
        
    Returns:
        Tuple of (min_probability, max_probability, category)
    """
    from .constants import CHC_THRESHOLDS
    
    # Very high: ≥1 Priority OR ≥2 Severe OR (1 Severe + ≥4 High)
    if (priority_count >= 1 or 
        severe_count >= 2 or 
        (severe_count >= 1 and high_count >= 4)):
        threshold = CHC_THRESHOLDS["very_high"]
        return threshold["min"], threshold["max"], "very_high"
    
    # High: 1 Severe + 2-3 High
    if severe_count >= 1 and 2 <= high_count <= 3:
        threshold = CHC_THRESHOLDS["high"]
        return threshold["min"], threshold["max"], "high"
    
    # Moderate: ≥5 High
    if high_count >= 5:
        threshold = CHC_THRESHOLDS["moderate"]
        return threshold["min"], threshold["max"], "moderate"
    
    # Low: all other cases
    threshold = CHC_THRESHOLDS["low"]
    return threshold["min"], threshold["max"], "low"

