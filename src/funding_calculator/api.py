"""FastAPI endpoints for funding calculator module 2025-2026."""

from typing import Optional, Dict
from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import StreamingResponse
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# New calculator
from .calculator import FundingEligibilityCalculator
from .models import PatientProfile, PropertyDetails, DomainAssessment, Domain, DomainLevel

# Legacy support
try:
    from .fair_cost_gap import FairCostGapCalculator
except ImportError:
    FairCostGapCalculator = None

# Pricing service
try:
    from pricing_core import PricingService, CareType
    from pricing_core.models import PricingResult
    PRICING_AVAILABLE = True
except ImportError:
    PricingService = None
    CareType = None
    PricingResult = None
    PRICING_AVAILABLE = False

# PDF generator (optional)
try:
    from .pdf_generator import PDFReportGenerator
    PDF_GENERATOR_AVAILABLE = True
except ImportError:
    PDFReportGenerator = None
    PDF_GENERATOR_AVAILABLE = False

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/funding", tags=["funding"])

# Global service instances
_funding_calculator: Optional[FundingEligibilityCalculator] = None
_fair_cost_calculator: Optional[FairCostGapCalculator] = None
_pricing_service: Optional[PricingService] = None
_pdf_generator: Optional[PDFReportGenerator] = None
_cache: Optional[Any] = None


def get_cache():
    """Get or create cache instance."""
    global _cache
    if _cache is None:
        try:
            from .cache import FundingCache
            _cache = FundingCache()
        except Exception as e:
            logger.warning("Cache not available", error=str(e))
            _cache = None
    return _cache


def get_funding_calculator() -> FundingEligibilityCalculator:
    """Get or create FundingEligibilityCalculator instance."""
    global _funding_calculator
    if _funding_calculator is None:
        cache = get_cache()
        _funding_calculator = FundingEligibilityCalculator(cache=cache)
    return _funding_calculator


def get_fair_cost_calculator() -> Optional[FairCostGapCalculator]:
    """Get or create FairCostGapCalculator instance (legacy)."""
    if FairCostGapCalculator is None:
        return None
    global _fair_cost_calculator
    if _fair_cost_calculator is None:
        _fair_cost_calculator = FairCostGapCalculator()
    return _fair_cost_calculator


def get_pricing_service() -> Optional[PricingService]:
    """Get or create PricingService instance."""
    if not PRICING_AVAILABLE:
        return None
    global _pricing_service
    if _pricing_service is None:
        _pricing_service = PricingService()
    return _pricing_service


def get_pdf_generator() -> Optional[PDFReportGenerator]:
    """Get or create PDFReportGenerator instance."""
    if not PDF_GENERATOR_AVAILABLE:
        return None
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = PDFReportGenerator()
    return _pdf_generator


def _convert_legacy_profile_to_new(profile_dict: Dict) -> PatientProfile:
    """
    Convert legacy profile format to new PatientProfile with domain assessments.
    
    This creates basic domain assessments from legacy health condition fields.
    """
    from .constants import Domain, DomainLevel
    
    domain_assessments = {}
    
    # Map legacy fields to domains
    if profile_dict.get("has_dementia"):
        domain_assessments[Domain.COGNITION] = DomainAssessment(
            domain=Domain.COGNITION,
            level=DomainLevel.HIGH,
            description="Dementia diagnosis"
        )
    
    if profile_dict.get("has_parkinsons"):
        domain_assessments[Domain.MOBILITY] = DomainAssessment(
            domain=Domain.MOBILITY,
            level=DomainLevel.MODERATE,
            description="Parkinson's disease"
        )
    
    if profile_dict.get("has_stroke"):
        domain_assessments[Domain.COMMUNICATION] = DomainAssessment(
            domain=Domain.COMMUNICATION,
            level=DomainLevel.MODERATE,
            description="Stroke history"
        )
    
    mobility_level = profile_dict.get("mobility_level", "independent")
    if mobility_level == "bedbound":
        domain_assessments[Domain.MOBILITY] = DomainAssessment(
            domain=Domain.MOBILITY,
            level=DomainLevel.SEVERE,
            description="Bedbound"
        )
    elif mobility_level == "wheelchair":
        domain_assessments[Domain.MOBILITY] = DomainAssessment(
            domain=Domain.MOBILITY,
            level=DomainLevel.HIGH,
            description="Wheelchair user"
        )
    
    if profile_dict.get("requires_nursing_care"):
        domain_assessments[Domain.DRUG_THERAPIES] = DomainAssessment(
            domain=Domain.DRUG_THERAPIES,
            level=DomainLevel.HIGH,
            description="Requires nursing care"
        )
    
    if profile_dict.get("requires_medication_management"):
        if Domain.DRUG_THERAPIES not in domain_assessments:
            domain_assessments[Domain.DRUG_THERAPIES] = DomainAssessment(
                domain=Domain.DRUG_THERAPIES,
                level=DomainLevel.MODERATE,
                description="Requires medication management"
            )
    
    # Handle property
    property_obj = None
    if "property" in profile_dict:
        property_obj = PropertyDetails(**profile_dict["property"])
    
    # Create profile
    profile = PatientProfile(
        age=profile_dict.get("age", 80),
        domain_assessments=domain_assessments,
        has_primary_health_need=profile_dict.get("has_primary_health_need", False),
        requires_nursing_care=profile_dict.get("requires_nursing_care", False),
        has_peg_feeding=profile_dict.get("has_peg_feeding", False),
        has_tracheostomy=profile_dict.get("has_tracheostomy", False),
        requires_injections=profile_dict.get("requires_injections", False),
        requires_ventilator=profile_dict.get("requires_ventilator", False),
        requires_dialysis=profile_dict.get("requires_dialysis", False),
        has_unpredictable_needs=profile_dict.get("has_unpredictable_needs", False),
        has_fluctuating_condition=profile_dict.get("has_fluctuating_condition", False),
        has_high_risk_behaviours=profile_dict.get("has_high_risk_behaviours", False),
        capital_assets=profile_dict.get("capital_assets", 0.0),
        weekly_income=profile_dict.get("weekly_income", 0.0),
        property=property_obj,
        care_type=profile_dict.get("care_type", "residential"),
        is_permanent_care=profile_dict.get("is_permanent_care", True)
    )
    
    return profile


@router.post("/calculate-full")
async def calculate_full_eligibility(
    patient_profile: Dict = Body(..., description="Patient profile dict"),
    postcode: Optional[str] = Body(None, description="Postcode for pricing"),
    care_type: Optional[str] = Body(None, description="Care type for pricing"),
    user_id: str = Body("anonymous", description="User identifier for caching"),
    use_cache: bool = Body(True, description="Whether to use cache"),
    cache_override: bool = Body(False, description="Admin override flag")
):
    """
    Calculate full funding eligibility using new calculator 2025-2026.
    
    Accepts patient profile with domain assessments or legacy format.
    """
    try:
        # Convert to new profile format
        profile = _convert_legacy_profile_to_new(patient_profile)
        
        # Get pricing result if postcode provided
        pricing_result = None
        if postcode and PRICING_AVAILABLE:
            try:
                pricing_service = get_pricing_service()
                if pricing_service and care_type:
                    care_type_enum = CareType(care_type.lower())
                    pricing_result = pricing_service.get_full_pricing(
                        postcode=postcode,
                        care_type=care_type_enum
                    )
            except Exception as e:
                logger.warning("Could not get pricing result", error=str(e))
        
        # Calculate full eligibility
        calculator = get_funding_calculator()
        result = calculator.calculate_full_eligibility(
            patient_profile=patient_profile,
            pricing_result=pricing_result,
            user_id=user_id,
            use_cache=use_cache,
            cache_override=cache_override
        )
        
        return result.as_dict()
        
    except Exception as e:
        logger.error("Error calculating eligibility", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/calculate-savings")
async def calculate_savings(
    postcode: str = Query(..., description="UK postcode"),
    care_type: str = Query(..., description="Care type"),
    age: int = Query(..., ge=0, le=120, description="Patient age"),
    user_id: str = Query("anonymous", description="User identifier for caching"),
    use_cache: bool = Query(True, description="Whether to use cache"),
    has_primary_health_need: bool = Query(False, description="Has primary health need"),
    has_dementia: bool = Query(False, description="Has dementia"),
    has_parkinsons: bool = Query(False, description="Has Parkinson's disease"),
    has_stroke: bool = Query(False, description="Has stroke history"),
    has_diabetes: bool = Query(False, description="Has diabetes"),
    has_heart_condition: bool = Query(False, description="Has heart condition"),
    requires_nursing_care: bool = Query(False, description="Requires nursing care"),
    mobility_level: str = Query("independent", description="Mobility level"),
    requires_personal_care: bool = Query(False, description="Requires personal care"),
    requires_medication_management: bool = Query(False, description="Requires medication management"),
    capital_assets: float = Query(0.0, ge=0, description="Capital assets in GBP"),
    weekly_income: float = Query(0.0, ge=0, description="Weekly income in GBP"),
    care_cost_per_week: Optional[float] = Query(None, ge=0, description="Current care cost per week")
):
    """
    Calculate funding eligibility and potential savings (legacy endpoint).
    
    Returns full eligibility assessment including CHC probability, LA funding, and savings.
    """
    try:
        # Build profile dict
        profile_dict = {
            "age": age,
            "has_primary_health_need": has_primary_health_need,
            "has_dementia": has_dementia,
            "has_parkinsons": has_parkinsons,
            "has_stroke": has_stroke,
            "has_diabetes": has_diabetes,
            "has_heart_condition": has_heart_condition,
            "requires_nursing_care": requires_nursing_care,
            "mobility_level": mobility_level,
            "requires_personal_care": requires_personal_care,
            "requires_medication_management": requires_medication_management,
            "capital_assets": capital_assets,
            "weekly_income": weekly_income,
            "care_type": care_type,
            "is_permanent_care": True
        }
        
        # Get pricing result
        pricing_result = None
        if PRICING_AVAILABLE:
            try:
                pricing_service = get_pricing_service()
                if pricing_service:
                    care_type_enum = CareType(care_type.lower())
                    pricing_result = pricing_service.get_full_pricing(
                        postcode=postcode,
                        care_type=care_type_enum
                    )
            except Exception:
                pass
        
        # Calculate using new calculator
        calculator = get_funding_calculator()
        result = calculator.calculate_full_eligibility(
            patient_profile=profile_dict,
            pricing_result=pricing_result,
            user_id=user_id,
            use_cache=use_cache
        )
        
        # Return in legacy format for backward compatibility
        return {
            "eligibility": {
                "patient_profile": result.patient_profile.model_dump(),
                "chc_eligibility": {
                    "probability_percent": result.chc_eligibility.probability_percent,
                    "is_likely_eligible": result.chc_eligibility.is_likely_eligible,
                    "reasoning": result.chc_eligibility.reasoning,
                    "key_factors": result.chc_eligibility.key_factors
                },
                "la_funding": {
                    "top_up_probability_percent": result.la_support.top_up_probability_percent,
                    "deferred_payment_eligible": result.dpa_eligibility.is_eligible,
                    "deferred_payment_reasoning": result.dpa_eligibility.reasoning,
                    "weekly_contribution": result.la_support.weekly_contribution
                },
                "potential_savings_per_week": result.savings.weekly_savings,
                "potential_savings_per_year": result.savings.annual_gbp,
                "potential_savings_5_years": result.savings.five_year_gbp,
                "recommendations": result.recommendations
            },
            "fair_cost_gap": {
                "weekly_gap": result.savings.weekly_savings,
                "yearly_gap": result.savings.annual_gbp,
                "five_year_gap": result.savings.five_year_gbp
            },
            "pricing_gap": pricing_result.fair_cost_gap_gbp if pricing_result else None
        }
    except Exception as e:
        logger.error("Error calculating savings", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/generate-pdf")
async def generate_pdf_report_post(
    patient_profile: Dict = Body(..., description="Patient profile dict"),
    postcode: Optional[str] = Body(None, description="Postcode for pricing"),
    care_type: Optional[str] = Body(None, description="Care type for pricing")
):
    """
    Generate PDF report for funding eligibility (POST method with full profile).
    
    Returns PDF file for download.
    """
    try:
        # Calculate eligibility first
        calculator = get_funding_calculator()
        
        # Get pricing result if postcode provided
        pricing_result = None
        if postcode and PRICING_AVAILABLE:
            try:
                pricing_service = get_pricing_service()
                if pricing_service and care_type:
                    care_type_enum = CareType(care_type.lower())
                    pricing_result = pricing_service.get_full_pricing(
                        postcode=postcode,
                        care_type=care_type_enum
                    )
            except Exception as e:
                logger.warning("Could not get pricing result", error=str(e))
        
        # Calculate full eligibility
        result = calculator.calculate_full_eligibility(
            patient_profile=patient_profile,
            pricing_result=pricing_result,
            user_id="web_user",
            use_cache=True
        )
        
        # Generate report HTML
        report_html = calculator.generate_report(result, report_type="full")
        
        # Convert to PDF
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=report_html).write_pdf()
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="PDF generation requires weasyprint. Install: pip install weasyprint"
            )
        
        # Return PDF as download
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="funding_report_{postcode.replace(" ", "_") if postcode else "report"}.pdf"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating PDF", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/generate-pdf")
async def generate_pdf_report(
    postcode: str = Query(..., description="UK postcode"),
    care_type: str = Query(..., description="Care type"),
    age: int = Query(..., ge=0, le=120, description="Patient age"),
    has_primary_health_need: bool = Query(False, description="Has primary health need"),
    has_dementia: bool = Query(False, description="Has dementia"),
    has_parkinsons: bool = Query(False, description="Has Parkinson's disease"),
    has_stroke: bool = Query(False, description="Has stroke history"),
    has_diabetes: bool = Query(False, description="Has diabetes"),
    has_heart_condition: bool = Query(False, description="Has heart condition"),
    requires_nursing_care: bool = Query(False, description="Requires nursing care"),
    mobility_level: str = Query("independent", description="Mobility level"),
    requires_personal_care: bool = Query(False, description="Requires personal care"),
    requires_medication_management: bool = Query(False, description="Requires medication management"),
    capital_assets: float = Query(0.0, ge=0, description="Capital assets in GBP"),
    weekly_income: float = Query(0.0, ge=0, description="Weekly income in GBP"),
    care_cost_per_week: Optional[float] = Query(None, ge=0, description="Current care cost per week")
):
    """
    Generate PDF report for funding eligibility and savings.
    
    Returns PDF file for download.
    """
    try:
        # Build profile dict
        profile_dict = {
            "age": age,
            "has_primary_health_need": has_primary_health_need,
            "has_dementia": has_dementia,
            "has_parkinsons": has_parkinsons,
            "has_stroke": has_stroke,
            "has_diabetes": has_diabetes,
            "has_heart_condition": has_heart_condition,
            "requires_nursing_care": requires_nursing_care,
            "mobility_level": mobility_level,
            "requires_personal_care": requires_personal_care,
            "requires_medication_management": requires_medication_management,
            "capital_assets": capital_assets,
            "weekly_income": weekly_income,
            "care_type": care_type,
            "is_permanent_care": True
        }
        
        # Get pricing result
        pricing_result = None
        if PRICING_AVAILABLE:
            try:
                pricing_service = get_pricing_service()
                if pricing_service:
                    care_type_enum = CareType(care_type.lower())
                    pricing_result = pricing_service.get_full_pricing(
                        postcode=postcode,
                        care_type=care_type_enum
                    )
            except Exception:
                pass
        
        # Calculate using new calculator
        calculator = get_funding_calculator()
        result = calculator.calculate_full_eligibility(
            patient_profile=profile_dict,
            pricing_result=pricing_result
        )
        
        # Generate report HTML
        report_html = calculator.generate_report(result, report_type="full")
        
        # Convert to PDF
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=report_html).write_pdf()
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="PDF generation requires weasyprint. Install: pip install weasyprint"
            )
        
        # Return PDF as download
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="funding_report_{postcode.replace(" ", "_")}.pdf"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating PDF", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics (admin endpoint)."""
    cache = get_cache()
    if not cache:
        return {"error": "Cache not available"}
    return cache.get_stats()


@router.delete("/cache/user/{user_id}")
async def clear_user_cache(user_id: str):
    """Clear all cache entries for a user (admin endpoint)."""
    cache = get_cache()
    if not cache:
        raise HTTPException(status_code=503, detail="Cache not available")
    
    count = cache.clear_user_cache(user_id)
    return {"deleted": count, "user_id": user_id}


@router.delete("/cache/entry")
async def delete_cache_entry(
    user_id: str = Query(..., description="User identifier"),
    patient_profile: Dict = Body(..., description="Patient profile dict"),
    override: bool = Query(False, description="Delete override cache")
):
    """Delete specific cache entry (admin endpoint)."""
    cache = get_cache()
    if not cache:
        raise HTTPException(status_code=503, detail="Cache not available")
    
    deleted = cache.delete(user_id, patient_profile, override=override)
    return {"deleted": deleted, "user_id": user_id}
