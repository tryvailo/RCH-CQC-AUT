"""FastAPI endpoints for pricing core module."""

from typing import Optional
import structlog
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from .service import PricingService
from .models import CareType, PricingResult

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/pricing-core", tags=["pricing-core"])

# Try to import weasyprint for PDF generation
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    HTML = None

# Global service instance
_pricing_service: Optional[PricingService] = None


def get_pricing_service() -> PricingService:
    """Get or create PricingService instance."""
    global _pricing_service
    if _pricing_service is None:
        _pricing_service = PricingService()
    return _pricing_service


@router.get("/calculate", response_model=PricingResult)
async def calculate_pricing(
    postcode: str = Query(..., description="UK postcode"),
    care_type: CareType = Query(..., description="Care type"),
    cqc_rating: Optional[str] = Query(None, description="CQC rating"),
    facilities_score: Optional[int] = Query(None, ge=0, le=20, description="Facilities score (0-20)"),
    bed_count: Optional[int] = Query(None, gt=0, description="Number of beds"),
    is_chain: bool = Query(False, description="Is part of a chain"),
    scraped_price: Optional[float] = Query(None, ge=0, description="Scraped price (overrides calculation)")
):
    """
    Calculate full pricing with Band v5 logic.
    
    Returns complete pricing analysis including affordability band and adjustments.
    """
    try:
        service = get_pricing_service()
        result = service.get_full_pricing(
            postcode=postcode,
            care_type=care_type,
            cqc_rating=cqc_rating,
            facilities_score=facilities_score,
            bed_count=bed_count,
            is_chain=is_chain,
            scraped_price=scraped_price
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/generate-pdf")
async def generate_pdf_report(
    postcode: str = Query(..., description="UK postcode"),
    care_type: CareType = Query(..., description="Care type"),
    cqc_rating: Optional[str] = Query(None, description="CQC rating"),
    facilities_score: Optional[int] = Query(None, ge=0, le=20, description="Facilities score (0-20)"),
    bed_count: Optional[int] = Query(None, gt=0, description="Number of beds"),
    is_chain: bool = Query(False, description="Is part of a chain"),
    scraped_price: Optional[float] = Query(None, ge=0, description="Scraped price (overrides calculation)")
):
    """
    Generate PDF report for pricing calculation.
    
    Returns PDF file for download.
    """
    try:
        if not WEASYPRINT_AVAILABLE:
            raise HTTPException(
                status_code=503,
                detail="PDF generation is not available. Please install weasyprint: pip install weasyprint"
            )
        
        service = get_pricing_service()
        result = service.get_full_pricing(
            postcode=postcode,
            care_type=care_type,
            cqc_rating=cqc_rating,
            facilities_score=facilities_score,
            bed_count=bed_count,
            is_chain=is_chain,
            scraped_price=scraped_price
        )
        
        # Generate HTML for PDF
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Price Report - {postcode}</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                h1 {{ color: #333; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
                h2 {{ color: #555; margin-top: 30px; }}
                .metric {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .band {{ font-size: 48px; font-weight: bold; text-align: center; padding: 20px; }}
                .band-a {{ color: #28a745; }}
                .band-b {{ color: #28a745; }}
                .band-c {{ color: #ffc107; }}
                .band-d {{ color: #fd7e14; }}
                .band-e {{ color: #dc3545; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #667eea; color: white; }}
            </style>
        </head>
        <body>
            <h1>💰 Price Calculator Report</h1>
            
            <h2>Location Information</h2>
            <div class="metric">
                <strong>Postcode:</strong> {result.postcode}<br>
                <strong>Local Authority:</strong> {result.local_authority}<br>
                <strong>Region:</strong> {result.region}<br>
                <strong>Care Type:</strong> {result.care_type.value.replace('_', ' ').title()}
            </div>
            
            <h2>Pricing Summary</h2>
            <table>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Final Price</td>
                    <td>£{result.final_price_gbp:.2f}/week</td>
                </tr>
                <tr>
                    <td>Base Price (Lottie)</td>
                    <td>£{result.base_price_gbp:.2f}/week</td>
                </tr>
                <tr>
                    <td>MSIF Lower Bound</td>
                    <td>{f'£{result.msif_lower_bound_gbp:.2f}/week' if result.msif_lower_bound_gbp else 'N/A'}</td>
                </tr>
                <tr>
                    <td>Expected Range</td>
                    <td>£{result.expected_range_min_gbp:.2f} - £{result.expected_range_max_gbp:.2f}/week</td>
                </tr>
            </table>
            
            <h2>Affordability Band</h2>
            <div class="band band-{result.affordability_band.lower()}">
                Band {result.affordability_band}
            </div>
            <div class="metric">
                <strong>Band Score:</strong> {result.band_score:.3f}<br>
                <strong>Confidence:</strong> {result.band_confidence_percent}%<br>
                <strong>Reasoning:</strong> {result.band_reasoning}
            </div>
            
            <h2>Adjustments Applied</h2>
            <table>
                <tr>
                    <th>Factor</th>
                    <th>Adjustment</th>
                </tr>
                {''.join([f'<tr><td>{name.replace("_", " ").title()}</td><td>{value*100:+.1f}%</td></tr>' for name, value in (result.adjustments or {}).items()])}
            </table>
            
            <h2>Gap Analysis</h2>
            <div class="metric">
                <strong>Fair Cost Gap:</strong> £{result.fair_cost_gap_gbp:.2f} ({result.fair_cost_gap_percent:+.1f}%)
            </div>
            
            <h2>Negotiation Leverage Text</h2>
            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                {result.negotiation_leverage_text.replace(chr(10), '<br>')}
            </div>
            
            <div style="margin-top: 40px; text-align: center; color: #666; font-size: 12px;">
                Generated by RightCareHome Pricing Calculator<br>
                Report Date: {result.model_dump().get('timestamp', 'N/A')}
            </div>
        </body>
        </html>
        """
        
        # Convert HTML to PDF
        try:
            pdf_bytes = HTML(string=html_content).write_pdf()
        except Exception as pdf_error:
            logger.error("WeasyPrint PDF generation failed", error=str(pdf_error), error_type=type(pdf_error).__name__)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate PDF: {str(pdf_error)}. Please check if weasyprint is properly installed."
            )
        
        # Return PDF as download
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="price_report_{postcode.replace(" ", "_")}.pdf"'
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Handle validation errors
        logger.error("PDF generation validation error", error=str(e))
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        # Log full error for debugging
        logger.error("PDF generation error", error=str(e), error_type=type(e).__name__, postcode=postcode, care_type=care_type.value)
        raise HTTPException(status_code=400, detail=f"Failed to generate PDF: {str(e)}")

