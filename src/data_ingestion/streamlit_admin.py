"""Streamlit admin interface for data ingestion."""

import streamlit as st
import pandas as pd
from datetime import datetime
from .service import DataIngestionService
from .database import init_database

# Initialize
if 'service' not in st.session_state:
    st.session_state.service = DataIngestionService()

service = st.session_state.service

# Page config
st.set_page_config(
    page_title="Data Admin - RightCareHome",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Data Ingestion Admin")
st.markdown("Manage MSIF and Lottie data updates")

# Initialize database
if st.button("Initialize Database Tables"):
    try:
        init_database()
        st.success("✅ Database tables initialized successfully")
    except Exception as e:
        st.error(f"❌ Error initializing database: {e}")

st.divider()

# MSIF Data Refresh
st.subheader("MSIF Data Refresh")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Refresh MSIF 2025-2026", type="primary", use_container_width=True):
        with st.spinner("Refreshing MSIF 2025-2026 data..."):
            result = service.refresh_msif_data(year=2025)
            if result["status"] == "success":
                st.success(f"✅ {result['data_source']} updated successfully! Records: {result['records_updated']}")
            else:
                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")

with col2:
    if st.button("🔄 Refresh MSIF 2024-2025", use_container_width=True):
        with st.spinner("Refreshing MSIF 2024-2025 data..."):
            result = service.refresh_msif_data(year=2024)
            if result["status"] == "success":
                st.success(f"✅ {result['data_source']} updated successfully! Records: {result['records_updated']}")
            else:
                st.error(f"❌ Error: {result.get('error', 'Unknown error')}")

st.divider()

# Lottie Data Refresh
st.subheader("Lottie Regional Averages")

if st.button("🔄 Refresh Lottie Data", type="primary", use_container_width=True):
    with st.spinner("Refreshing Lottie regional averages..."):
        result = service.refresh_lottie_data()
        if result["status"] == "success":
            st.success(f"✅ {result['data_source']} updated successfully! Records: {result['records_updated']}")
        else:
            st.error(f"❌ Error: {result.get('error', 'Unknown error')}")

st.divider()

# Update Status Table
st.subheader("📈 Update Status")

if st.button("🔄 Refresh Status", use_container_width=True):
    st.rerun()

try:
    updates = service.get_update_status()
    
    if updates:
        # Prepare data for display
        df_data = []
        for update in updates:
            status_emoji = "✅" if update["status"] == "success" else "❌"
            df_data.append({
                "ID": update["id"],
                "Data Source": update["data_source"],
                "Status": f"{status_emoji} {update['status']}",
                "Records": update["records_updated"] or 0,
                "Started": update["started_at"].strftime("%Y-%m-%d %H:%M:%S") if update["started_at"] else "",
                "Completed": update["completed_at"].strftime("%Y-%m-%d %H:%M:%S") if update["completed_at"] else "",
                "Duration (s)": update["duration_seconds"] or "",
                "Error": update["error_message"] or ""
            })
        
        df = pd.DataFrame(df_data)
        
        # Display with styling
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        # Summary stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Updates", len(updates))
        with col2:
            success_count = sum(1 for u in updates if u["status"] == "success")
            st.metric("Successful", success_count, delta=f"{success_count}/{len(updates)}")
        with col3:
            failed_count = sum(1 for u in updates if u["status"] == "failed")
            st.metric("Failed", failed_count, delta=f"-{failed_count}" if failed_count > 0 else None)
    else:
        st.info("No update logs found. Run a refresh to see status.")
        
except Exception as e:
    st.error(f"❌ Error loading update status: {e}")

