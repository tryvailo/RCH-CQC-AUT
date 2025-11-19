"""PDF report generator using Jinja templates."""

from pathlib import Path
from typing import Optional
import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .models import FundingEligibilityResult, FairCostGapResult

logger = structlog.get_logger(__name__)

# Try to import weasyprint for PDF generation
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    HTML = None


class PDFReportGenerator:
    """Generate PDF reports from Jinja templates."""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize PDF report generator.
        
        Args:
            templates_dir: Directory containing Jinja templates
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"
        
        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Add custom filter for number formatting
        self.env.filters['format_number'] = lambda x: f"{x:,}"
    
    def generate_html_report(
        self,
        eligibility_result: FundingEligibilityResult,
        fair_cost_result: FairCostGapResult
    ) -> str:
        """
        Generate HTML report from templates.
        
        Args:
            eligibility_result: Funding eligibility result
            fair_cost_result: Fair cost gap result
            
        Returns:
            HTML content as string
        """
        template = self.env.get_template('report_template.html')
        
        html = template.render(
            # Fair cost gap
            weekly_gap=fair_cost_result.weekly_gap,
            yearly_gap=fair_cost_result.yearly_gap,
            five_year_gap=fair_cost_result.five_year_gap,
            emotional_text=fair_cost_result.emotional_text,
            
            # Savings
            potential_savings_per_week=eligibility_result.potential_savings_per_week,
            potential_savings_per_year=eligibility_result.potential_savings_per_year,
            potential_savings_5_years=eligibility_result.potential_savings_5_years,
            
            # CHC eligibility
            chc_probability=eligibility_result.chc_eligibility.probability_percent,
            chc_likely_eligible=eligibility_result.chc_eligibility.is_likely_eligible,
            chc_reasoning=eligibility_result.chc_eligibility.reasoning,
            chc_key_factors=eligibility_result.chc_eligibility.key_factors,
            
            # LA funding
            top_up_probability=eligibility_result.la_funding.top_up_probability_percent,
            deferred_payment_eligible=eligibility_result.la_funding.deferred_payment_eligible,
            deferred_payment_reasoning=eligibility_result.la_funding.deferred_payment_reasoning,
            weekly_contribution=eligibility_result.la_funding.weekly_contribution,
            
            # Recommendations
            recommendations=eligibility_result.recommendations
        )
        
        logger.info("Generated HTML report")
        return html
    
    def generate_markdown_report(
        self,
        eligibility_result: FundingEligibilityResult,
        fair_cost_result: FairCostGapResult
    ) -> str:
        """
        Generate Markdown report from templates.
        
        Args:
            eligibility_result: Funding eligibility result
            fair_cost_result: Fair cost gap result
            
        Returns:
            Markdown content as string
        """
        template = self.env.get_template('report_template.md')
        
        markdown = template.render(
            # Fair cost gap
            weekly_gap=fair_cost_result.weekly_gap,
            yearly_gap=fair_cost_result.yearly_gap,
            five_year_gap=fair_cost_result.five_year_gap,
            emotional_text=fair_cost_result.emotional_text,
            
            # Savings
            potential_savings_per_week=eligibility_result.potential_savings_per_week,
            potential_savings_per_year=eligibility_result.potential_savings_per_year,
            potential_savings_5_years=eligibility_result.potential_savings_5_years,
            
            # CHC eligibility
            chc_probability=eligibility_result.chc_eligibility.probability_percent,
            chc_likely_eligible=eligibility_result.chc_eligibility.is_likely_eligible,
            chc_reasoning=eligibility_result.chc_eligibility.reasoning,
            chc_key_factors=eligibility_result.chc_eligibility.key_factors,
            
            # LA funding
            top_up_probability=eligibility_result.la_funding.top_up_probability_percent,
            deferred_payment_eligible=eligibility_result.la_funding.deferred_payment_eligible,
            deferred_payment_reasoning=eligibility_result.la_funding.deferred_payment_reasoning,
            weekly_contribution=eligibility_result.la_funding.weekly_contribution,
            
            # Recommendations
            recommendations=eligibility_result.recommendations
        )
        
        logger.info("Generated Markdown report")
        return markdown
    
    def generate_pdf_report(
        self,
        eligibility_result: FundingEligibilityResult,
        fair_cost_result: FairCostGapResult
    ) -> bytes:
        """
        Generate PDF report from HTML template.
        
        Args:
            eligibility_result: Funding eligibility result
            fair_cost_result: Fair cost gap result
            
        Returns:
            PDF content as bytes
            
        Raises:
            ImportError: If weasyprint is not installed
        """
        if not WEASYPRINT_AVAILABLE:
            raise ImportError(
                "weasyprint is required for PDF generation. "
                "Install it with: pip install weasyprint"
            )
        
        # Generate HTML first
        html_content = self.generate_html_report(eligibility_result, fair_cost_result)
        
        # Convert HTML to PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        logger.info("Generated PDF report", size_bytes=len(pdf_bytes))
        return pdf_bytes

