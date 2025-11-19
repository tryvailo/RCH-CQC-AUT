"""Tests for PDF report generator."""

import pytest
from pathlib import Path
from funding_calculator.pdf_generator import PDFReportGenerator
from funding_calculator.models import (
    PatientProfile,
    FundingEligibilityResult,
    CHCEligibilityResult,
    LAFundingResult,
    FairCostGapResult
)


@pytest.fixture
def generator(tmp_path):
    """Create PDFReportGenerator instance."""
    # Create temporary templates directory
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    
    # Create simple test template
    (templates_dir / "report_template.html").write_text(
        "<html><body><h1>{{ title }}</h1><p>Gap: £{{ weekly_gap }}</p></body></html>"
    )
    
    return PDFReportGenerator(templates_dir=templates_dir)


@pytest.fixture
def sample_eligibility_result():
    """Create sample eligibility result."""
    profile = PatientProfile(
        age=85,
        has_primary_health_need=True,
        capital_assets=100000.0
    )
    
    chc_eligibility = CHCEligibilityResult(
        probability_percent=75,
        is_likely_eligible=True,
        reasoning="High probability",
        key_factors=["Primary health need", "Dementia"]
    )
    
    la_funding = LAFundingResult(
        top_up_probability_percent=60,
        deferred_payment_eligible=True,
        deferred_payment_reasoning="Eligible",
        weekly_contribution=150.0
    )
    
    return FundingEligibilityResult(
        patient_profile=profile,
        chc_eligibility=chc_eligibility,
        la_funding=la_funding,
        potential_savings_per_week=200.0,
        potential_savings_per_year=10400.0,
        potential_savings_5_years=52000.0,
        recommendations=["Apply for CHC", "Consider deferred payment"]
    )


@pytest.fixture
def sample_fair_cost_result():
    """Create sample fair cost gap result."""
    return FairCostGapResult(
        weekly_gap=150.0,
        yearly_gap=7800.0,
        five_year_gap=39000.0,
        emotional_text="Test emotional text",
        report_block_html="<div>Test HTML</div>",
        report_block_markdown="# Test Markdown"
    )


class TestPDFReportGenerator:
    """Test PDFReportGenerator class."""
    
    def test_generate_html_report(self, generator, sample_eligibility_result, sample_fair_cost_result):
        """Test HTML report generation."""
        html = generator.generate_html_report(sample_eligibility_result, sample_fair_cost_result)
        
        assert isinstance(html, str)
        assert len(html) > 0
        assert "150.0" in html or "150" in html
    
    def test_generate_markdown_report(self, generator, sample_eligibility_result, sample_fair_cost_result):
        """Test Markdown report generation."""
        # Create markdown template
        templates_dir = generator.templates_dir
        (templates_dir / "report_template.md").write_text(
            "# Report\n\nGap: £{{ weekly_gap }}\n\nSavings: £{{ potential_savings_per_year }}"
        )
        
        markdown = generator.generate_markdown_report(sample_eligibility_result, sample_fair_cost_result)
        
        assert isinstance(markdown, str)
        assert len(markdown) > 0
        assert "150" in markdown or "150.0" in markdown

