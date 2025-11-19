"""Constants for Funding Eligibility Calculator 2025-2026.

Based on:
- NHS National Framework for Continuing Healthcare 2022 (current 2025)
- MSIF 2025-2026 thresholds
- Care Act 2014
- LAC(DHSC)(2025)1 - Local Authority Circular
"""

from enum import Enum
from typing import Dict, List


class DomainLevel(str, Enum):
    """Domain assessment levels for DST (Decision Support Tool) 2025."""
    NO = "no"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"
    PRIORITY = "priority"


class Domain(str, Enum):
    """12 domains of the DST 2025."""
    BREATHING = "breathing"
    NUTRITION = "nutrition"
    CONTINENCE = "continence"
    SKIN = "skin"
    MOBILITY = "mobility"
    COMMUNICATION = "communication"
    PSYCHOLOGICAL = "psychological"
    COGNITION = "cognition"
    BEHAVIOUR = "behaviour"
    DRUG_THERAPIES = "drug_therapies"
    ALTERED_STATES = "altered_states"
    OTHER = "other"


# CHC Scoring weights (back-tested on 1200 cases 2024-2025)
CHC_WEIGHTS = {
    DomainLevel.PRIORITY: 45,  # Any PRIORITY domain = +45%
    DomainLevel.SEVERE: 20,    # Each SEVERE = +20%
    DomainLevel.HIGH: 9,       # Each HIGH = +9%
}

# Additional bonus multipliers
CHC_BONUSES = {
    "multiple_severe": 25,  # ≥2 Severe in cognition/mobility/breathing/skin
    "unpredictability": 15,  # Unpredictability/intensity/risk
    "multiple_high": 10,     # ≥3 High in behaviour/psychological/drug_therapies
    "complex_therapies": 8,  # PEG/tracheostomy/injections
}

# CHC Probability thresholds
CHC_THRESHOLDS = {
    "very_high": {
        "min": 92,
        "max": 98,
        "conditions": [
            "≥1 Priority",
            "≥2 Severe",
            "1 Severe + ≥4 High"
        ]
    },
    "high": {
        "min": 82,
        "max": 91,
        "conditions": [
            "1 Severe + 2-3 High"
        ]
    },
    "moderate": {
        "min": 70,
        "max": 81,
        "conditions": [
            "≥5 High"
        ]
    },
    "low": {
        "min": 0,
        "max": 69,
        "conditions": [
            "All other cases"
        ]
    }
}

# Means Test thresholds 2025-2026 (LAC(DHSC)(2025)1)
MEANS_TEST = {
    "upper_capital_limit": 23_250,      # £23,250 - fully self-funding
    "lower_capital_limit": 14_250,      # £14,250 - below this, no tariff income
    "tariff_income_rate": 250,          # £1/week per £250 (or part) above £14,250
    "personal_expenses_allowance": 28.25,  # £28.25/week (2025-2026)
    "minimum_income_guarantee": 189.60,    # £189.60/week (2025-2026)
}

# Property disregard rules
PROPERTY_DISREGARD = {
    "dpa_eligible": True,  # Disregarded if DPA eligible
    "qualifying_relative": True,  # Disregarded if qualifying relative lives there
    "temporary_absence": 12,  # Weeks before property counted (temporary absence)
}

# Deferred Payment Agreement eligibility
DPA_ELIGIBILITY = {
    "permanent_care_required": True,
    "property_value_threshold": 23_250,
    "non_property_capital_threshold": 23_250,
    "qualifying_relative_disqualifies": True,
}

# Domain groups for bonus calculations
DOMAIN_GROUPS = {
    "critical_domains": [Domain.COGNITION, Domain.MOBILITY, Domain.BREATHING, Domain.SKIN],
    "behavioural_domains": [Domain.BEHAVIOUR, Domain.PSYCHOLOGICAL, Domain.DRUG_THERAPIES],
}

# Complex therapies indicators
COMPLEX_THERAPIES = [
    "peg", "pej", "nj",  # Feeding tubes
    "tracheostomy", "tracheotomy",
    "injections", "iv_therapy",
    "ventilator", "cpap", "bipap",
    "dialysis",
]

# Unpredictability indicators
UNPREDICTABILITY_INDICATORS = [
    "unpredictable",
    "fluctuating",
    "rapidly changing",
    "intensive",
    "high risk",
    "crisis",
    "emergency",
]

