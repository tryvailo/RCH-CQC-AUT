"""Fair Cost Gap calculator with emotional text generation."""

from typing import Optional
import structlog
from .models import FairCostGapResult

logger = structlog.get_logger(__name__)


class FairCostGapCalculator:
    """Calculate and format Fair Cost Gap for reports."""
    
    def calculate_gap(
        self,
        weekly_gap: float,
        emotional_tone: str = "professional"
    ) -> FairCostGapResult:
        """
        Calculate fair cost gap and generate report blocks.
        
        Args:
            weekly_gap: Weekly gap in GBP
            emotional_tone: Tone for emotional text ("professional", "empathetic", "urgent")
            
        Returns:
            FairCostGapResult
        """
        logger.info("Calculating fair cost gap", weekly_gap=weekly_gap)
        
        yearly_gap = weekly_gap * 52
        five_year_gap = yearly_gap * 5
        
        # Generate emotional text based on tone
        emotional_text = self._generate_emotional_text(weekly_gap, yearly_gap, five_year_gap, emotional_tone)
        
        # Generate HTML block
        html_block = self._generate_html_block(weekly_gap, yearly_gap, five_year_gap)
        
        # Generate Markdown block
        markdown_block = self._generate_markdown_block(weekly_gap, yearly_gap, five_year_gap)
        
        return FairCostGapResult(
            weekly_gap=weekly_gap,
            yearly_gap=yearly_gap,
            five_year_gap=five_year_gap,
            emotional_text=emotional_text,
            report_block_html=html_block,
            report_block_markdown=markdown_block
        )
    
    def _generate_emotional_text(
        self,
        weekly: float,
        yearly: float,
        five_year: float,
        tone: str
    ) -> str:
        """Generate emotional text based on gap size and tone."""
        
        if weekly < 50:
            gap_level = "small"
            impact = "minimal"
        elif weekly < 150:
            gap_level = "moderate"
            impact = "noticeable"
        elif weekly < 300:
            gap_level = "significant"
            impact = "substantial"
        else:
            gap_level = "substantial"
            impact = "considerable"
        
        if tone == "empathetic":
            text = (
                f"Every week, families are paying £{weekly:.2f} more than the fair cost benchmark. "
                f"That's £{yearly:,.0f} per year that could be spent on improving quality of life, "
                f"additional care hours, or family visits. Over five years, this adds up to "
                f"£{five_year:,.0f} - a {impact} amount that represents real financial strain "
                f"on families already navigating the emotional challenges of finding the right care."
            )
        elif tone == "urgent":
            text = (
                f"⚠️ CRITICAL: The current pricing is £{weekly:.2f}/week above fair cost benchmarks. "
                f"This translates to £{yearly:,.0f} annually and £{five_year:,.0f} over 5 years. "
                f"Immediate action is recommended to negotiate fees or explore alternative funding options."
            )
        else:  # professional
            text = (
                f"The calculated weekly fee exceeds the MSIF fair cost lower bound by £{weekly:.2f} per week. "
                f"This represents an annual difference of £{yearly:,.0f} and a cumulative difference "
                f"of £{five_year:,.0f} over a five-year period. This {gap_level} gap may impact "
                f"long-term affordability and should be considered in funding decisions."
            )
        
        return text
    
    def _generate_html_block(self, weekly: float, yearly: float, five_year: float) -> str:
        """Generate HTML block for report insertion."""
        return f"""
<div class="fair-cost-gap-block" style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 20px; margin: 20px 0;">
    <h3 style="color: #856404; margin-top: 0;">Fair Cost Gap Analysis</h3>
    <div style="display: flex; justify-content: space-around; margin: 20px 0;">
        <div style="text-align: center;">
            <div style="font-size: 24px; font-weight: bold; color: #856404;">£{weekly:.2f}</div>
            <div style="color: #666;">per week</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 24px; font-weight: bold; color: #856404;">£{yearly:,.0f}</div>
            <div style="color: #666;">per year</div>
        </div>
        <div style="text-align: center;">
            <div style="font-size: 24px; font-weight: bold; color: #856404;">£{five_year:,.0f}</div>
            <div style="color: #666;">over 5 years</div>
        </div>
    </div>
    <p style="color: #856404; margin-bottom: 0;">
        This represents the difference between the quoted price and the MSIF 2025-2026 fair cost benchmark.
    </p>
</div>
"""
    
    def _generate_markdown_block(self, weekly: float, yearly: float, five_year: float) -> str:
        """Generate Markdown block for report insertion."""
        return f"""
## Fair Cost Gap Analysis

| Period | Amount |
|--------|--------|
| **Per Week** | £{weekly:.2f} |
| **Per Year** | £{yearly:,.0f} |
| **Over 5 Years** | £{five_year:,.0f} |

> This represents the difference between the quoted price and the MSIF 2025-2026 fair cost benchmark.
"""

