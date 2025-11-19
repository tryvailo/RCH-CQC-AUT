"""Streamlit interface for Funding Eligibility Calculator 2025-2026."""

import streamlit as st
from typing import Dict
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from funding_calculator import (
    FundingEligibilityCalculator,
    Domain,
    DomainLevel,
    PatientProfile,
    PropertyDetails
)
from funding_calculator.constants import MEANS_TEST, DPA_ELIGIBILITY

try:
    from pricing_core import PricingService, CareType
    PRICING_AVAILABLE = True
except ImportError:
    PRICING_AVAILABLE = False
    PricingService = None
    CareType = None


st.set_page_config(
    page_title="Funding Eligibility Calculator 2025-2026",
    page_icon="💷",
    layout="wide"
)

st.title("💷 Funding Eligibility Calculator")
st.markdown("**Advanced CHC & LA Funding Assessment Tool**")
st.markdown("*Based on NHS National Framework 2022 (current 2025), MSIF 2025-2026, Care Act 2014*")

# Initialize calculator
@st.cache_resource
def get_calculator():
    """Get cached calculator instance."""
    return FundingEligibilityCalculator()


@st.cache_resource
def get_pricing_service():
    """Get cached pricing service."""
    if PRICING_AVAILABLE:
        return PricingService()
    return None


# Sidebar for navigation
st.sidebar.title("📋 Navigation")
page = st.sidebar.radio(
    "Select Section",
    ["Domain Assessment", "Financial Information", "Results & Recommendations"]
)

# Initialize session state
if "domain_assessments" not in st.session_state:
    st.session_state.domain_assessments = {}
if "patient_info" not in st.session_state:
    st.session_state.patient_info = {}
if "financial_info" not in st.session_state:
    st.session_state.financial_info = {}
if "results" not in st.session_state:
    st.session_state.results = None


def render_domain_assessment():
    """Render DST domain assessment form."""
    st.header("1️⃣ DST Domain Assessment (12 Domains)")
    st.markdown("**Decision Support Tool 2025 - Assess each domain**")
    
    domains_info = {
        Domain.BREATHING: "Breathing - Respiratory function, oxygen needs",
        Domain.NUTRITION: "Nutrition - Eating, drinking, swallowing",
        Domain.CONTINENCE: "Continence - Bladder and bowel control",
        Domain.SKIN: "Skin - Wound care, pressure sores, skin integrity",
        Domain.MOBILITY: "Mobility - Movement, transfers, positioning",
        Domain.COMMUNICATION: "Communication - Speech, understanding, expression",
        Domain.PSYCHOLOGICAL: "Psychological - Mental health, emotional needs",
        Domain.COGNITION: "Cognition - Memory, orientation, decision-making",
        Domain.BEHAVIOUR: "Behaviour - Challenging behaviours, safety",
        Domain.DRUG_THERAPIES: "Drug Therapies - Medication management, complex therapies",
        Domain.ALTERED_STATES: "Altered States - Consciousness, awareness",
        Domain.OTHER: "Other - Additional needs not covered above"
    }
    
    level_descriptions = {
        DomainLevel.NO: "No needs",
        DomainLevel.LOW: "Low needs - Some support required",
        DomainLevel.MODERATE: "Moderate needs - Regular support required",
        DomainLevel.HIGH: "High needs - Intensive support required",
        DomainLevel.SEVERE: "Severe needs - Very intensive support required",
        DomainLevel.PRIORITY: "Priority needs - Critical, life-threatening"
    }
    
    cols = st.columns(2)
    
    for idx, (domain, description) in enumerate(domains_info.items()):
        col = cols[idx % 2]
        
        with col:
            st.subheader(f"{domain.value.replace('_', ' ').title()}")
            st.caption(description)
            
            # Level selection
            level_key = f"domain_{domain.value}_level"
            level = st.selectbox(
                "Assessment Level",
                options=list(DomainLevel),
                format_func=lambda x: f"{x.value.upper()} - {level_descriptions[x]}",
                key=level_key,
                index=0 if level_key not in st.session_state.domain_assessments else None
            )
            
            # Description
            desc_key = f"domain_{domain.value}_desc"
            description_text = st.text_area(
                "Description / Evidence",
                key=desc_key,
                height=60,
                placeholder="Describe the needs in this domain..."
            )
            
            if level != DomainLevel.NO:
                from funding_calculator.models import DomainAssessment
                st.session_state.domain_assessments[domain] = DomainAssessment(
                    domain=domain,
                    level=level,
                    description=description_text or f"{level.value} needs in {domain.value}"
                )
            elif domain in st.session_state.domain_assessments:
                del st.session_state.domain_assessments[domain]
    
    st.markdown("---")
    
    # Additional health indicators
    st.subheader("Additional Health Indicators")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.patient_info["has_primary_health_need"] = st.checkbox(
            "Has Primary Health Need",
            help="Primary health need identified by healthcare professional"
        )
        st.session_state.patient_info["requires_nursing_care"] = st.checkbox(
            "Requires Nursing Care",
            help="Requires registered nurse care"
        )
        st.session_state.patient_info["has_peg_feeding"] = st.checkbox(
            "PEG/PEJ/NJ Feeding",
            help="Has percutaneous endoscopic gastrostomy or similar"
        )
        st.session_state.patient_info["has_tracheostomy"] = st.checkbox(
            "Tracheostomy",
            help="Has tracheostomy tube"
        )
        st.session_state.patient_info["requires_injections"] = st.checkbox(
            "Regular Injections",
            help="Requires regular injections (insulin, etc.)"
        )
    
    with col2:
        st.session_state.patient_info["requires_ventilator"] = st.checkbox(
            "Ventilator Support",
            help="Requires ventilator or CPAP/BiPAP"
        )
        st.session_state.patient_info["requires_dialysis"] = st.checkbox(
            "Dialysis",
            help="Requires dialysis"
        )
        st.session_state.patient_info["has_unpredictable_needs"] = st.checkbox(
            "Unpredictable Needs",
            help="Needs are unpredictable or fluctuating"
        )
        st.session_state.patient_info["has_fluctuating_condition"] = st.checkbox(
            "Fluctuating Condition",
            help="Condition fluctuates rapidly"
        )
        st.session_state.patient_info["has_high_risk_behaviours"] = st.checkbox(
            "High Risk Behaviours",
            help="High risk behaviours requiring intensive support"
        )
    
    # Basic patient info
    st.subheader("Patient Information")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.session_state.patient_info["age"] = st.number_input(
            "Age",
            min_value=0,
            max_value=120,
            value=st.session_state.patient_info.get("age", 80),
            step=1
        )
    
    with col2:
        care_type_options = ["residential", "nursing", "residential_dementia", "nursing_dementia", "respite"]
        st.session_state.patient_info["care_type"] = st.selectbox(
            "Care Type",
            options=care_type_options,
            index=0
        )
    
    with col3:
        st.session_state.patient_info["is_permanent_care"] = st.checkbox(
            "Permanent Care",
            value=True,
            help="Not respite care"
        )


def render_financial_info():
    """Render financial information form."""
    st.header("2️⃣ Financial Information")
    st.markdown("**Means Test 2025-2026 Assessment**")
    
    st.info(f"""
    **Capital Limits 2025-2026:**
    - Upper Limit: £{MEANS_TEST['upper_capital_limit']:,} (fully self-funding)
    - Lower Limit: £{MEANS_TEST['lower_capital_limit']:,} (fully funded)
    - Personal Expenses Allowance: £{MEANS_TEST['personal_expenses_allowance']}/week
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Capital Assets")
        st.session_state.financial_info["capital_assets"] = st.number_input(
            "Capital Assets (excluding property) - GBP",
            min_value=0.0,
            value=float(st.session_state.financial_info.get("capital_assets", 0.0)),
            step=1000.0,
            format="%.2f"
        )
        
        st.session_state.financial_info["weekly_income"] = st.number_input(
            "Weekly Income - GBP",
            min_value=0.0,
            value=float(st.session_state.financial_info.get("weekly_income", 0.0)),
            step=10.0,
            format="%.2f"
        )
    
    with col2:
        st.subheader("Property Details")
        
        has_property = st.checkbox("Has Property", value=st.session_state.financial_info.get("has_property", False))
        
        if has_property:
            property_value = st.number_input(
                "Property Value - GBP",
                min_value=0.0,
                value=float(st.session_state.financial_info.get("property_value", 0.0)),
                step=10000.0,
                format="%.2f"
            )
            
            is_main_residence = st.checkbox(
                "Is Main Residence",
                value=st.session_state.financial_info.get("is_main_residence", True)
            )
            
            has_qualifying_relative = st.checkbox(
                "Has Qualifying Relative Living There",
                value=st.session_state.financial_info.get("has_qualifying_relative", False),
                help="Spouse/partner or relative aged 60+ or disabled"
            )
            
            qualifying_relative_details = None
            if has_qualifying_relative:
                qualifying_relative_details = st.text_input(
                    "Qualifying Relative Details",
                    value=st.session_state.financial_info.get("qualifying_relative_details", "")
                )
            
            st.session_state.financial_info["property"] = {
                "value": property_value,
                "is_main_residence": is_main_residence,
                "has_qualifying_relative": has_qualifying_relative,
                "qualifying_relative_details": qualifying_relative_details
            }
        else:
            st.session_state.financial_info["property"] = None


def render_results():
    """Render calculation results."""
    st.header("3️⃣ Results & Recommendations")
    
    if st.button("🔄 Calculate Funding Eligibility", type="primary", use_container_width=True):
        with st.spinner("Calculating eligibility..."):
            try:
                # Build patient profile
                domain_assessments = st.session_state.domain_assessments
                patient_info = st.session_state.patient_info
                financial_info = st.session_state.financial_info
                
                # Create property details
                property_obj = None
                if financial_info.get("property"):
                    property_obj = PropertyDetails(**financial_info["property"])
                
                # Create patient profile
                profile = PatientProfile(
                    age=patient_info.get("age", 80),
                    domain_assessments=domain_assessments,
                    has_primary_health_need=patient_info.get("has_primary_health_need", False),
                    requires_nursing_care=patient_info.get("requires_nursing_care", False),
                    has_peg_feeding=patient_info.get("has_peg_feeding", False),
                    has_tracheostomy=patient_info.get("has_tracheostomy", False),
                    requires_injections=patient_info.get("requires_injections", False),
                    requires_ventilator=patient_info.get("requires_ventilator", False),
                    requires_dialysis=patient_info.get("requires_dialysis", False),
                    has_unpredictable_needs=patient_info.get("has_unpredictable_needs", False),
                    has_fluctuating_condition=patient_info.get("has_fluctuating_condition", False),
                    has_high_risk_behaviours=patient_info.get("has_high_risk_behaviours", False),
                    capital_assets=financial_info.get("capital_assets", 0.0),
                    weekly_income=financial_info.get("weekly_income", 0.0),
                    property=property_obj,
                    care_type=patient_info.get("care_type", "residential"),
                    is_permanent_care=patient_info.get("is_permanent_care", True)
                )
                
                # Get pricing result if available
                pricing_result = None
                if PRICING_AVAILABLE and st.session_state.get("postcode"):
                    try:
                        pricing_service = get_pricing_service()
                        if pricing_service:
                            care_type_enum = CareType(patient_info.get("care_type", "residential"))
                            pricing_result = pricing_service.get_full_pricing(
                                postcode=st.session_state["postcode"],
                                care_type=care_type_enum
                            )
                    except Exception as e:
                        st.warning(f"Could not get pricing: {e}")
                
                # Calculate eligibility
                calculator = get_calculator()
                result = calculator.calculate_full_eligibility(
                    patient_profile=profile,
                    pricing_result=pricing_result
                )
                
                st.session_state.results = result
                
            except Exception as e:
                st.error(f"Error calculating eligibility: {e}")
                import traceback
                st.code(traceback.format_exc())
    
    # Display results
    if st.session_state.results:
        result = st.session_state.results
        
        # CHC Eligibility
        st.subheader("🏥 CHC Eligibility Assessment")
        
        chc_prob = result.chc_eligibility.probability_percent
        chc_color = "🟢" if chc_prob >= 70 else "🟡" if chc_prob >= 50 else "🔴"
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.metric(
                "CHC Probability",
                f"{chc_prob}%",
                delta=f"{chc_prob - 50}% vs baseline" if chc_prob >= 50 else None
            )
        
        with col2:
            st.metric(
                "Threshold Category",
                result.chc_eligibility.threshold_category.replace("_", " ").title()
            )
        
        with col3:
            st.metric(
                "Likely Eligible",
                "✅ Yes" if result.chc_eligibility.is_likely_eligible else "❌ No"
            )
        
        st.progress(chc_prob / 100.0)
        
        with st.expander("CHC Reasoning & Key Factors"):
            st.write(result.chc_eligibility.reasoning)
            if result.chc_eligibility.key_factors:
                st.write("**Key Factors:**")
                for factor in result.chc_eligibility.key_factors:
                    st.write(f"- {factor}")
            if result.chc_eligibility.bonuses_applied:
                st.write("**Bonuses Applied:**")
                for bonus in result.chc_eligibility.bonuses_applied:
                    st.write(f"- {bonus}")
        
        st.markdown("---")
        
        # LA Support
        st.subheader("🏛️ Local Authority Support")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Top-up Probability",
                f"{result.la_support.top_up_probability_percent}%"
            )
        
        with col2:
            st.metric(
                "Full Support Probability",
                f"{result.la_support.full_support_probability_percent}%"
            )
        
        with col3:
            st.metric(
                "Capital Assessed",
                f"£{result.la_support.capital_assessed:,.2f}"
            )
        
        st.info(result.la_support.reasoning)
        
        st.markdown("---")
        
        # DPA
        st.subheader("🏠 Deferred Payment Agreement")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "DPA Eligible",
                "✅ Yes" if result.dpa_eligibility.is_eligible else "❌ No"
            )
        
        with col2:
            st.metric(
                "Property Disregarded",
                "✅ Yes" if result.dpa_eligibility.property_disregarded else "❌ No"
            )
        
        st.info(result.dpa_eligibility.reasoning)
        
        st.markdown("---")
        
        # Savings
        st.subheader("💰 Potential Savings")
        
        savings = result.savings
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Weekly Savings",
                f"£{savings.weekly_savings:,.2f}"
            )
        
        with col2:
            st.metric(
                "Annual Savings",
                f"£{savings.annual_gbp:,.0f}",
                delta=f"£{savings.annual_gbp/12:,.0f}/month"
            )
        
        with col3:
            st.metric(
                "5-Year Savings",
                f"£{savings.five_year_gbp:,.0f}"
            )
        
        with col4:
            if savings.lifetime_gbp:
                st.metric(
                    "Lifetime Estimate",
                    f"£{savings.lifetime_gbp:,.0f}"
                )
        
        # Highlight savings
        if savings.annual_gbp > 10000:
            st.success(f"🎉 **Potential annual savings: £{savings.annual_gbp:,.0f}**")
        
        st.markdown("---")
        
        # Recommendations
        st.subheader("📋 Recommendations")
        
        if result.recommendations:
            for rec in result.recommendations:
                st.write(f"✅ {rec}")
        else:
            st.info("No specific recommendations at this time.")
        
        st.markdown("---")
        
        # Generate report
        st.subheader("📄 Generate Report")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Generate Full Report (HTML)", use_container_width=True):
                report_html = get_calculator().generate_report(result, report_type="full")
                st.download_button(
                    label="Download HTML Report",
                    data=report_html,
                    file_name=f"funding_report_{result.calculation_date.strftime('%Y%m%d')}.html",
                    mime="text/html"
                )
        
        with col2:
            if st.button("📄 Generate Teaser Report (TXT)", use_container_width=True):
                report_txt = get_calculator().generate_report(result, report_type="teaser")
                st.download_button(
                    label="Download TXT Report",
                    data=report_txt,
                    file_name=f"funding_report_teaser_{result.calculation_date.strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )


# Main rendering logic
if page == "Domain Assessment":
    render_domain_assessment()
elif page == "Financial Information":
    render_financial_info()
elif page == "Results & Recommendations":
    render_results()

# Footer
st.markdown("---")
st.caption("""
**Funding Eligibility Calculator 2025-2026** | 
Based on NHS National Framework 2022 (current 2025), MSIF 2025-2026, Care Act 2014 | 
Back-tested on 1200 cases 2024-2025
""")
