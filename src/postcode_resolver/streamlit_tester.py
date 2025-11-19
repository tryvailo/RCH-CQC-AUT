"""Streamlit interface for postcode testing with map visualization."""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from .resolver import PostcodeResolver
from .batch_resolver import BatchPostcodeResolver
from .validator import validate_postcode, is_valid_postcode
from .models import PostcodeInfo

# Initialize
if 'resolver' not in st.session_state:
    st.session_state.resolver = PostcodeResolver()

if 'batch_resolver' not in st.session_state:
    st.session_state.batch_resolver = BatchPostcodeResolver()

resolver = st.session_state.resolver
batch_resolver = st.session_state.batch_resolver

# Page config
st.set_page_config(
    page_title="Postcode Tester - RightCareHome",
    page_icon="📍",
    layout="wide"
)

st.title("📍 Postcode Resolver Tester")
st.markdown("Resolve UK postcodes to Local Authority and Region")

# Single postcode resolver
st.subheader("Single Postcode Resolver")

col1, col2 = st.columns([2, 1])

with col1:
    postcode_input = st.text_input(
        "Enter UK Postcode",
        value="B15 2HQ",
        placeholder="e.g., B15 2HQ, SW1A 1AA, M1 1AA",
        help="Enter a valid UK postcode"
    )

with col2:
    use_cache = st.checkbox("Use Cache", value=True)

if st.button("Resolve Postcode", type="primary"):
    if not postcode_input:
        st.error("Please enter a postcode")
    else:
        # Validate format
        if not is_valid_postcode(postcode_input):
            st.error(f"❌ Invalid postcode format: {postcode_input}")
        else:
            try:
                with st.spinner("Resolving postcode..."):
                    result = resolver.resolve(postcode_input, use_cache=use_cache)
                
                # Display result
                st.success(f"✅ Postcode resolved: {result.postcode}")
                
                # Create columns for result display
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Local Authority", result.local_authority)
                    st.metric("Region", result.region)
                
                with col2:
                    st.metric("Latitude", f"{result.lat:.6f}")
                    st.metric("Longitude", f"{result.lon:.6f}")
                
                with col3:
                    if result.country:
                        st.metric("Country", result.country)
                    if result.county:
                        st.metric("County", result.county)
                
                # Display full details
                with st.expander("Full Details"):
                    st.json(result.model_dump())
                
                # Create map
                if result.lat and result.lon:
                    st.subheader("📍 Map Location")
                    m = folium.Map(
                        location=[result.lat, result.lon],
                        zoom_start=13,
                        tiles='OpenStreetMap'
                    )
                    
                    # Add marker
                    folium.Marker(
                        [result.lat, result.lon],
                        popup=f"""
                        <b>Postcode:</b> {result.postcode}<br>
                        <b>Local Authority:</b> {result.local_authority}<br>
                        <b>Region:</b> {result.region}<br>
                        <b>Country:</b> {result.country or 'N/A'}
                        """,
                        tooltip=result.postcode,
                        icon=folium.Icon(color='blue', icon='map-marker')
                    ).add_to(m)
                    
                    folium_static(m, width=700, height=500)
            
            except Exception as e:
                st.error(f"❌ Error resolving postcode: {e}")

st.divider()

# Batch resolver
st.subheader("Batch Postcode Resolver")

batch_input = st.text_area(
    "Enter Postcodes (one per line)",
    value="B15 2HQ\nSW1A 1AA\nM1 1AA\nEH1 1YZ\nCF10 3AT\nBT1 5GS",
    height=150,
    help="Enter multiple postcodes, one per line"
)

col1, col2 = st.columns(2)
with col1:
    batch_use_cache = st.checkbox("Use Cache (Batch)", value=True)
with col2:
    batch_validate = st.checkbox("Validate Format", value=True)

if st.button("Resolve Batch", type="primary"):
    if not batch_input:
        st.error("Please enter at least one postcode")
    else:
        postcodes = [p.strip() for p in batch_input.split('\n') if p.strip()]
        
        if len(postcodes) > 100:
            st.error("Maximum 100 postcodes per batch")
        else:
            try:
                with st.spinner(f"Resolving {len(postcodes)} postcodes..."):
                    result = batch_resolver.resolve_batch(
                        postcodes,
                        use_cache=batch_use_cache,
                        validate=batch_validate
                    )
                
                # Display summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total", result.total)
                with col2:
                    st.metric("Found", result.found, delta=f"{result.found}/{result.total}")
                with col3:
                    st.metric("Not Found", result.not_found, delta=f"-{result.not_found}")
                
                # Create results table
                results_data = []
                for i, (postcode, info) in enumerate(zip(postcodes, result.results)):
                    if info:
                        results_data.append({
                            "Postcode": postcode,
                            "Local Authority": info.local_authority,
                            "Region": info.region,
                            "Country": info.country or "",
                            "Lat": f"{info.lat:.6f}",
                            "Lon": f"{info.lon:.6f}",
                            "Status": "✅ Found"
                        })
                    else:
                        results_data.append({
                            "Postcode": postcode,
                            "Local Authority": "",
                            "Region": "",
                            "Country": "",
                            "Lat": "",
                            "Lon": "",
                            "Status": "❌ Not Found"
                        })
                
                df = pd.DataFrame(results_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Create map with all found postcodes
                found_results = [r for r in result.results if r is not None]
                if found_results:
                    st.subheader("📍 Map (All Locations)")
                    
                    # Center map on first result
                    center_lat = found_results[0].lat
                    center_lon = found_results[0].lon
                    
                    m = folium.Map(
                        location=[center_lat, center_lon],
                        zoom_start=6,
                        tiles='OpenStreetMap'
                    )
                    
                    # Add markers for all results
                    for info in found_results:
                        folium.Marker(
                            [info.lat, info.lon],
                            popup=f"""
                            <b>Postcode:</b> {info.postcode}<br>
                            <b>Local Authority:</b> {info.local_authority}<br>
                            <b>Region:</b> {info.region}
                            """,
                            tooltip=info.postcode,
                            icon=folium.Icon(color='blue', icon='map-marker')
                        ).add_to(m)
                    
                    folium_static(m, width=700, height=500)
            
            except Exception as e:
                st.error(f"❌ Error resolving batch: {e}")

st.divider()

# Postcode validator
st.subheader("Postcode Validator")

validator_input = st.text_input(
    "Test Postcode Format",
    placeholder="e.g., B15 2HQ",
    help="Check if postcode format is valid"
)

if validator_input:
    is_valid = is_valid_postcode(validator_input)
    if is_valid:
        st.success(f"✅ Valid postcode format: {validator_input}")
        try:
            normalized = resolver.resolve(validator_input, use_cache=False)
            st.info(f"Normalized: {normalized.postcode}")
        except Exception:
            pass
    else:
        st.error(f"❌ Invalid postcode format: {validator_input}")

