import streamlit as st
import sqlite3
import json
import pandas as pd
import numpy as np

st.set_page_config(page_title="Plant Engineering Analytics", layout="wide")

st.title("Plant Engineering Diagnostics & Characteristic Curves")
st.caption("Deep-Dive Offline Engineering Portal Connected to equipment_telemetry.db")

# Load historical telemetry from SQLite
@st.cache_data(ttl=2)
def load_historical_data():
    conn = sqlite3.connect("equipment_telemetry.db")
    query = "SELECT * FROM fleet_telemetry ORDER BY id DESC LIMIT 200"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

df_history = load_historical_data()

if df_history.empty:
    st.warning("No records found in equipment_telemetry.db yet. Run ai_equipment_suite.py to stream telemetry.")
    st.stop()

# Parse latest raw frame
latest_row = df_history.iloc[0]
latest_raw = json.loads(latest_row["raw_json"])

tab1, tab2, tab3 = st.tabs([
    "Pump Characteristic (H-Q) Curve", 
    "Chiller & Psychrometric Tower Analysis", 
    "Historical Weibull Degradation Tracking"
])

# ------------------------------------------------------------------------------
# TAB 1: PUMP HEAD VS FLOW (H-Q) CHARACTERISTIC CURVE
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("Asset 1: Centrifugal Pump Operating Point vs BEP")
    col1, col2 = st.columns([3, 1])

    with col1:
        # Theoretical Head-Flow Curve: H = H_shutoff - k * Q^2
        q_curve = np.linspace(20, 160, 100)
        h_shutoff = 65.0
        k = 0.0014
        h_curve = h_shutoff - k * (q_curve ** 2)
        
        chart_data = pd.DataFrame({"Flow Rate (m³/h)": q_curve, "Design Head (m)": h_curve}).set_index("Flow Rate (m³/h)")
        st.line_chart(chart_data)

    with col2:
        curr_flow = latest_raw["pump"]["flow_m3h"]
        curr_head = latest_raw["pump"]["head_m"]
        st.metric("Current Operating Flow", f"{curr_flow} m³/h")
        st.metric("Current Operating Head", f"{curr_head} m")
        st.metric("Best Efficiency Point (BEP)", "120.0 m³/h")
        st.metric("Pump Health Index", f"{latest_row['pump_health']}/100")

# ------------------------------------------------------------------------------
# TAB 2: CHILLER & PSYCHROMETRIC TOWER ANALYSIS
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("Asset 4: Cooling Tower Approach & Specific Energy")
    col3, col4 = st.columns(2)
    
    with col3:
        st.write("**Cooling Tower Range vs Approach**")
        cws = latest_raw["chiller_tower"]["cw_supply_temp_c"]
        cwr = latest_raw["chiller_tower"]["cw_return_temp_c"]
        wb = latest_raw["chiller_tower"]["ambient_wet_bulb_c"]
        
        tower_data = pd.DataFrame({
            "Thermal Threshold": ["Tower Hot Supply", "Tower Cold Basin Return", "Ambient Wet-Bulb Limit"],
            "Temperature (°C)": [cws, cwr, wb]
        })
        st.bar_chart(tower_data.set_index("Thermal Threshold"))

    with col4:
        st.write("**Chiller Plant Health & Chemical Metrics**")
        st.metric("Cycles of Concentration (CoC)", round(latest_raw["chiller_tower"]["basin_tds_ppm"] / latest_raw["chiller_tower"]["makeup_tds_ppm"], 2))
        st.metric("Compressor Electrical Draw", f"{latest_raw['chiller_tower']['compressor_kw']} kW")
        st.metric("Chiller Health Score", f"{latest_row['chiller_health']}/100")

# ------------------------------------------------------------------------------
# TAB 3: WEIBULL HISTORICAL DEGRADATION TRENDING
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("Plant Health Trends Across Consecutive Shifts")
    trend_df = df_history[["id", "timestamp", "plant_health", "pump_health", "chiller_health"]].sort_values("id")
    st.line_chart(trend_df.set_index("timestamp")[["plant_health", "pump_health", "chiller_health"]])