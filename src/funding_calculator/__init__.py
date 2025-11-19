"""Funding calculator module for care home funding eligibility 2025-2026."""

from .calculator import FundingEligibilityCalculator
from .cache import FundingCache, CacheConfig
from .models import (
    PatientProfile,
    DomainAssessment,
    Domain,
    DomainLevel,
    CHCEligibilityResult,
    LASupportResult,
    DPAResult,
    SavingsResult,
    FundingEligibilityResult,
    PropertyDetails
)
from .constants import (
    DomainLevel as DomainLevelEnum,
    Domain as DomainEnum,
    MEANS_TEST,
    DPA_ELIGIBILITY,
    CHC_THRESHOLDS,
    CHC_WEIGHTS,
    CHC_BONUSES
)

# Legacy imports for backward compatibility
try:
    from .fair_cost_gap import FairCostGapCalculator
except ImportError:
    FairCostGapCalculator = None

# PDF generator is optional (requires jinja2)
try:
    from .pdf_generator import PDFReportGenerator
except ImportError:
    PDFReportGenerator = None

__all__ = [
    "FundingEligibilityCalculator",
    "FundingCache",
    "CacheConfig",
    "PatientProfile",
    "DomainAssessment",
    "Domain",
    "DomainLevel",
    "CHCEligibilityResult",
    "LASupportResult",
    "DPAResult",
    "SavingsResult",
    "FundingEligibilityResult",
    "PropertyDetails",
    "FairCostGapCalculator",
    "PDFReportGenerator",
    "MEANS_TEST",
    "DPA_ELIGIBILITY",
    "CHC_THRESHOLDS",
    "CHC_WEIGHTS",
    "CHC_BONUSES",
]
