"""Streamlit interface for Price Calculator."""

import streamlit as st
from .service import PricingService
from .models import CareType
from .exceptions import DataNotFoundError, InvalidInputError

# Initialize
if 'pricing_service' not in st.session_state:
    st.session_state.pricing_service = PricingService()

service = st.session_state.pricing_service

# Page config
st.set_page_config(
    page_title="Price Calculator - RightCareHome",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Price Calculator")
st.markdown("Calculate pricing and Affordability Bands using Band v5 logic")

# Input form
with st.form("pricing_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        postcode = st.text_input(
            "Postcode",
            value="B15 2HQ",
            placeholder="e.g., B15 2HQ",
            help="UK postcode"
        )
        
        care_type = st.selectbox(
            "Care Type",
            options=list(CareType),
            format_func=lambda x: x.value.replace("_", " ").title(),
            index=0
        )
        
        cqc_rating = st.selectbox(
            "CQC Rating (Optional)",
            options=[None, "Outstanding", "Good", "Requires Improvement", "Inadequate"],
            format_func=lambda x: x if x else "Not specified"
        )
    
    with col2:
        facilities_score = st.slider(
            "Facilities Score (0-20)",
            min_value=0,
            max_value=20,
            value=10,
            help="Score from 0 (basic) to 20 (excellent)"
        )
        
        bed_count = st.number_input(
            "Bed Count (Optional)",
            min_value=1,
            max_value=200,
            value=25,
            help="Number of beds"
        )
        
        is_chain = st.checkbox("Is part of a chain")
    
    scraped_price = st.number_input(
        "Scraped Price (Optional - Overrides Calculation)",
        min_value=0.0,
        value=None,
        step=10.0,
        help="If provided, this price will be used instead of calculated price"
    )
    
    submitted = st.form_submit_button("Calculate Pricing", type="primary")

# Calculate on form submit
if submitted:
    if not postcode:
        st.error("Please enter a postcode")
    else:
        try:
            with st.spinner("Calculating pricing..."):
                result = service.get_full_pricing(
                    postcode=postcode,
                    care_type=care_type,
                    cqc_rating=cqc_rating,
                    facilities_score=facilities_score if facilities_score > 0 else None,
                    bed_count=bed_count if bed_count > 0 else None,
                    is_chain=is_chain,
                    scraped_price=scraped_price if scraped_price and scraped_price > 0 else None
                )
            
            # Store result in session state
            st.session_state.last_result = result
            
            # Display results
            st.success("✅ Pricing calculated successfully!")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Final Price", f"£{result.final_price_gbp:.2f}/week")
            
            with col2:
                if result.msif_lower_bound_gbp:
                    st.metric("MSIF Lower Bound", f"£{result.msif_lower_bound_gbp:.2f}/week")
                else:
                    st.metric("MSIF Lower Bound", "N/A")
            
            with col3:
                st.metric("Base Price (Lottie)", f"£{result.base_price_gbp:.2f}/week")
            
            with col4:
                st.metric("Expected Range", f"£{result.expected_range_min_gbp:.2f} - £{result.expected_range_max_gbp:.2f}/week")
            
            st.divider()
            
            # Affordability Band
            st.subheader("🎯 Affordability Band")
            
            # Band display with color
            band_colors = {
                "A": "🟢",
                "B": "🟢",
                "C": "🟡",
                "D": "🟠",
                "E": "🔴"
            }
            
            band_color = band_colors.get(result.affordability_band, "⚪")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown(f"### {band_color} Band {result.affordability_band}")
                st.metric("Band Score", f"{result.band_score:.3f}")
                
                # Confidence meter
                st.markdown("**Confidence:**")
                confidence_color = "green" if result.band_confidence_percent >= 80 else "orange" if result.band_confidence_percent >= 70 else "red"
                st.progress(result.band_confidence_percent / 100)
                st.caption(f"{result.band_confidence_percent}% confidence")
            
            with col2:
                st.markdown("**Reasoning:**")
                st.info(result.band_reasoning)
            
            st.divider()
            
            # Adjustments
            if result.adjustments:
                st.subheader("📊 Adjustments Applied")
                
                adjustments_data = []
                for adj_name, adj_value in result.adjustments.items():
                    adjustments_data.append({
                        "Factor": adj_name.replace("_", " ").title(),
                        "Adjustment": f"{adj_value*100:+.1f}%",
                        "Impact": f"£{result.base_price_gbp * adj_value:.2f}/week"
                    })
                
                st.dataframe(adjustments_data, use_container_width=True, hide_index=True)
                st.caption(f"Total Adjustment: {result.adjustment_total_percent:+.1f}%")
            
            st.divider()
            
            # Gap Analysis
            st.subheader("📈 Gap Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Fair Cost Gap",
                    f"£{result.fair_cost_gap_gbp:.2f}",
                    delta=f"{result.fair_cost_gap_percent:+.1f}%"
                )
            
            with col2:
                if result.scraped_price_gbp:
                    st.info(f"💰 Using scraped price: £{result.scraped_price_gbp:.2f}/week")
                else:
                    st.info("📊 Using calculated price")
            
            st.divider()
            
            # Negotiation Leverage Text
            st.subheader("💼 Negotiation Leverage Text")
            st.text_area(
                "Copy this text for reports",
                value=result.negotiation_leverage_text,
                height=200,
                disabled=True
            )
            
            # Save as scraped price button
            st.divider()
            if st.button("💾 Save as Scraped Price", type="secondary"):
                st.session_state.scraped_price = result.final_price_gbp
                st.success(f"✅ Saved scraped price: £{result.final_price_gbp:.2f}/week")
                st.info("You can use this value in the 'Scraped Price' field for future calculations")
            
            # Full details expander
            with st.expander("📋 Full Details"):
                st.json(result.model_dump())
        
        except DataNotFoundError as e:
            st.error(f"❌ Data not found: {e}")
            st.info("Make sure MSIF and Lottie data are loaded in the database")
        
        except InvalidInputError as e:
            st.error(f"❌ Invalid input: {e}")
        
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.exception(e)

# Display last result if available
if 'last_result' in st.session_state:
    st.divider()
    st.subheader("📊 Last Calculation Summary")
    
    result = st.session_state.last_result
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Postcode", result.postcode)
        st.metric("Local Authority", result.local_authority)
    with col2:
        st.metric("Region", result.region)
        st.metric("Care Type", result.care_type.value.replace("_", " ").title())
    with col3:
        st.metric("Band", result.affordability_band)
        st.metric("Final Price", f"£{result.final_price_gbp:.2f}/week")

