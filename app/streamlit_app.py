import streamlit as st
import numpy as np
import pandas as pd
import joblib
import os
import sys
import matplotlib.pyplot as plt

# Ensure root directory is accessible for imports
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from engineering.pump_engineering import (
    theoretical_pump_head,
    calculate_hydraulic_power_kw,
    calculate_input_power_kw,
    Q_BEP,
    ETA_BEP
)
from engineering.pump_intelligence import diagnose_equipment_condition

from engineering.compressor_engineering import (
    theoretical_pressure_ratio,
    calculate_discharge_temperature,
    calculate_polytropic_head_j_kg,
    calculate_gas_power_kw,
    calculate_surge_margin_pct,
    GAMMA,
    R_SPECIFIC,
    Z_AVG,
    ETA_P_DESIGN,
    SURGE_FLOW_KG_S
)
from engineering.compressor_intelligence import diagnose_compressor_condition

# Page Configuration
st.set_page_config(
    page_title="AI Energy & Equipment Intelligence Suite",
    page_icon="⚙️",
    layout="wide"
)

# ---------------------------------------------------------------------------
# MODEL LOADERS (Handles both raw pipelines and dictionary packages)
# ---------------------------------------------------------------------------
@st.cache_resource
def load_pump_pipeline():
    model_path = os.path.join(ROOT_DIR, "models", "pump_condition_model.joblib")
    if os.path.exists(model_path):
        loaded = joblib.load(model_path)
        if isinstance(loaded, dict):
            return loaded.get("pipeline") or loaded.get("model") or loaded
        return loaded
    return None

@st.cache_resource
def load_compressor_pipeline():
    model_path = os.path.join(ROOT_DIR, "models", "compressor_condition_model.joblib")
    if os.path.exists(model_path):
        loaded = joblib.load(model_path)
        if isinstance(loaded, dict):
            return loaded.get("pipeline") or loaded.get("model") or loaded
        return loaded
    return None


# ---------------------------------------------------------------------------
# GLOBAL SIDEBAR NAVIGATION
# ---------------------------------------------------------------------------
st.sidebar.title("🏭 Plant Fleet Monitor")
selected_asset = st.sidebar.radio(
    "Select Industrial Asset:",
    ["Centrifugal Pump (Hydraulics)", "Centrifugal Gas Compressor (Thermodynamics)"],
    index=0
)
st.sidebar.markdown("---")


# ===========================================================================
# ASSET 1: CENTRIFUGAL PUMP INTELLIGENCE
# ===========================================================================
if selected_asset == "Centrifugal Pump (Hydraulics)":
    pump_pipeline = load_pump_pipeline()

    st.title("⚙️️ Centrifugal Pump Intelligence System")
    st.markdown("**Focus:** *Hydraulic Affinity, Energy Degradation & ISO 10816-3 Vibration Health*")

    st.sidebar.subheader("🎮 Pump Operating Inputs")
    flow_rate = st.sidebar.slider("Flow Rate Q (m³/s)", 0.0100, 0.0400, 0.0270, 0.0005, format="%.4f")
    st.sidebar.caption(f"Equivalent: {flow_rate * 3600:.1f} m³/h | BEP: {Q_BEP:.3f} m³/s")
    shaft_speed = st.sidebar.slider("Shaft Speed N (RPM)", 1200.0, 1800.0, 1500.0, 50.0)
    baseline_h = theoretical_pump_head(flow_rate, shaft_speed)
    delivered_head = st.sidebar.slider("Delivered Head H (m)", 20.0, 70.0, float(round(baseline_h, 2)), 0.1)
    hydraulic_eff = st.sidebar.slider("Hydraulic Efficiency (η)", 0.40, 0.85, 0.76, 0.01)

    p_hyd_kw = calculate_hydraulic_power_kw(flow_rate, delivered_head)
    expected_power = calculate_input_power_kw(p_hyd_kw, hydraulic_eff)
    input_power = st.sidebar.slider("Input Shaft Power (kW)", 5.0, 45.0, float(round(expected_power, 2)), 0.1)
    vibration_rms = st.sidebar.slider("Vibration RMS (mm/s)", 0.5, 9.0, 2.2, 0.1)

    # ML Inference - dynamically adapt column names to match model fit time
    feature_mapping = {
        "flow_rate_m3_s": flow_rate,
        "flow_rate_m3s": flow_rate,
        "shaft_speed_rpm": shaft_speed,
        "rpm": shaft_speed,
        "delivered_head_m": delivered_head,
        "head_m": delivered_head,
        "hydraulic_efficiency": hydraulic_eff,
        "efficiency": hydraulic_eff,
        "input_power_kw": input_power,
        "power_kw": input_power,
        "vibration_rms_mm_s": vibration_rms,
        "vibration_rms": vibration_rms,
        "operating_hours": 1200.0
    }

    if pump_pipeline is not None and hasattr(pump_pipeline, "predict"):
        if hasattr(pump_pipeline, "feature_names_in_"):
            expected_cols = list(pump_pipeline.feature_names_in_)
            row = {col: feature_mapping.get(col, 0.0) for col in expected_cols}
            input_df = pd.DataFrame([row], columns=expected_cols)
        else:
            input_df = pd.DataFrame([{
                "flow_rate_m3s": flow_rate,
                "head_m": delivered_head,
                "rpm": shaft_speed,
                "efficiency": hydraulic_eff,
                "power_kw": input_power,
                "vibration_rms": vibration_rms,
                "operating_hours": 1200.0
            }])

        prediction = pump_pipeline.predict(input_df)[0]
        if hasattr(pump_pipeline, "predict_proba"):
            prob_abnormal = pump_pipeline.predict_proba(input_df)[0][1]
        else:
            prob_abnormal = 1.0 if prediction == 1 else 0.0
    else:
        prediction = 0
        prob_abnormal = 0.0

    diag = diagnose_equipment_condition(
        flow_rate, delivered_head, hydraulic_eff, input_power, vibration_rms, shaft_speed
    )

    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if prediction == 0:
            st.success("### Status: NORMAL")
        else:
            st.error("### Status: FAULT DETECTED")
        st.caption(f"Degradation Risk: {prob_abnormal * 100:.1f}%")
    with col2:
        st.metric("Vibration Health", f"{vibration_rms:.2f} mm/s", diag["vibration_zone"])
    with col3:
        st.metric("Efficiency Deviation", f"{hydraulic_eff * 100:.1f}%", f"{diag['eff_deviation_pct']:.1f}% vs baseline")
    with col4:
        st.metric("Energy Penalty", f"{diag['excess_power_kw']:.2f} kW", f"${diag['annual_cost_penalty_usd']:,.0f}/yr")

    st.markdown("---")
    c_left, c_right = st.columns([3, 2])
    with c_left:
        st.subheader("📈 Pump Operating Map vs. Design Curve")
        q_vals = np.linspace(0.010, 0.040, 100)
        h_vals = [theoretical_pump_head(q, shaft_speed) for q in q_vals]
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(q_vals, h_vals, label=f"Theoretical Curve @ {shaft_speed:.0f} RPM", color="#1f77b4", lw=2)
        ax.scatter([flow_rate], [delivered_head], color="green" if prediction == 0 else "red", s=120, zorder=5, label="Live Operating Point")
        ax.axvline(Q_BEP, color="orange", linestyle=":", label=f"BEP ({Q_BEP} m³/s)")
        ax.set_xlabel("Flow Rate Q (m³/s)")
        ax.set_ylabel("Head H (m)")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend()
        st.pyplot(fig)
    with c_right:
        st.subheader("🔍 ISO 10816-3 Vibration Severity")
        st.markdown("- **Zone A/B (< 2.8 mm/s):** Good / Unrestricted continuous operation.")
        st.markdown("- **Zone C (2.8 – 4.5 mm/s):** Unsatisfactory; restricted long-term operation.")
        st.markdown("- **Zone D (> 4.5 mm/s):** Critical; trip / shutdown hazard.")
        vib_progress = min(vibration_rms / 8.0, 1.0)
        st.progress(vib_progress)
        st.info(f"**Classification:** {diag['vibration_desc']}")

    st.markdown("---")
    st.subheader("📋 Engineering Diagnostic Assessment")
    r1, r2 = st.columns(2)
    with r1:
        st.markdown("#### 🔬 Observed Physical Indicators")
        for item in diag["indicators"]:
            st.markdown(f"- {item}")
    with r2:
        st.markdown("#### 🛠️ Recommended Engineering Actions")
        for item in diag["actions"]:
            st.markdown(f"- {item}")


# ===========================================================================
# ASSET 2: CENTRIFUGAL GAS COMPRESSOR INTELLIGENCE
# ===========================================================================
else:
    comp_pipeline = load_compressor_pipeline()

    st.title("🌪️ Centrifugal Gas Compressor Intelligence System")
    st.markdown("**Focus:** *Thermodynamic Polytropic Compression, Surge Proximity & Impeller Fouling*")

    st.sidebar.subheader("🎮 Compressor Telemetry Inputs")
    mass_flow = st.sidebar.slider("Mass Flow Rate ṁ (kg/s)", 6.0, 15.0, 12.0, 0.1)
    st.sidebar.caption(f"Surge Limit: {SURGE_FLOW_KG_S} kg/s | Design Flow: 12.0 kg/s")
    comp_speed = st.sidebar.slider("Rotor Speed N (RPM)", 9000.0, 10000.0, 9500.0, 50.0)

    suction_p = st.sidebar.slider("Suction Pressure P₁ (bar)", 18.0, 22.0, 20.0, 0.2)
    suction_t_c = st.sidebar.slider("Suction Temp T₁ (°C)", 10.0, 30.0, 20.0, 0.5)
    suction_t_k = suction_t_c + 273.15

    base_rp = theoretical_pressure_ratio(mass_flow, comp_speed)
    p_ratio = st.sidebar.slider("Pressure Ratio (P₂/P₁)", 1.20, 2.40, float(round(base_rp, 3)), 0.01)
    discharge_p = suction_p * p_ratio

    poly_eff = st.sidebar.slider("Polytropic Efficiency (η_p)", 0.60, 0.86, 0.82, 0.01)

    t2_calc = calculate_discharge_temperature(suction_t_k, p_ratio, poly_eff, GAMMA)
    t2_calc_c = t2_calc - 273.15
    discharge_t_c = st.sidebar.slider("Discharge Temp T₂ (°C)", 40.0, 130.0, float(round(t2_calc_c, 1)), 0.5)

    comp_vibration = st.sidebar.slider("Vibration RMS (mm/s)", 0.5, 10.0, 1.8, 0.1)

    # Derived Physics Calculations
    head_j_kg = calculate_polytropic_head_j_kg(suction_t_k, p_ratio, poly_eff, R_SPECIFIC, Z_AVG, GAMMA)
    head_kj_kg = head_j_kg / 1000.0
    gas_power_kw = calculate_gas_power_kw(mass_flow, head_j_kg, poly_eff)
    surge_margin_pct = calculate_surge_margin_pct(mass_flow, SURGE_FLOW_KG_S)

    # Baseline power for energy penalty
    healthy_head = calculate_polytropic_head_j_kg(suction_t_k, base_rp, ETA_P_DESIGN, R_SPECIFIC, Z_AVG, GAMMA)
    healthy_power = calculate_gas_power_kw(mass_flow, healthy_head, ETA_P_DESIGN)
    excess_kw = max(0.0, gas_power_kw - healthy_power)

    # ML Inference
    if comp_pipeline is not None and hasattr(comp_pipeline, "predict"):
        input_data = pd.DataFrame([{
            "mass_flow_kg_s": mass_flow,
            "speed_rpm": comp_speed,
            "suction_p_bar": suction_p,
            "discharge_p_bar": discharge_p,
            "pressure_ratio": p_ratio,
            "suction_t_c": suction_t_c,
            "discharge_t_c": discharge_t_c,
            "polytropic_efficiency": poly_eff,
            "polytropic_head_kj_kg": head_kj_kg,
            "surge_margin_pct": surge_margin_pct,
            "vibration_rms_mm_s": comp_vibration
        }])
        pred = comp_pipeline.predict(input_data)[0]
        prob = comp_pipeline.predict_proba(input_data)[0][1]
    else:
        pred = 0
        prob = 0.0

    comp_diag = diagnose_compressor_condition(
        mass_flow, p_ratio, poly_eff, discharge_t_c, comp_vibration, surge_margin_pct, excess_kw
    )

    # KPI Header Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if pred == 0:
            st.success("### Status: NORMAL")
        else:
            st.error("### Status: FAULT / ALERT")
        st.caption(f"Degradation Probability: {prob * 100:.1f}%")
    with col2:
        sm_color = "normal" if surge_margin_pct >= 15 else "inverse"
        st.metric("Surge Safety Margin", f"{surge_margin_pct:.1f}%", comp_diag["surge_severity"], delta_color=sm_color)
    with col3:
        st.metric("Polytropic Efficiency", f"{poly_eff * 100:.1f}%", f"{comp_diag['eff_deviation_pct']:.1f}% vs design")
    with col4:
        st.metric("Excess Gas Power", f"{excess_kw:.1f} kW", f"${comp_diag['annual_cost_penalty_usd']:,.0f}/yr")

    st.markdown("---")
    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader("📈 Compressor Characteristic Map & Surge Envelope")
        m_vals = np.linspace(6.0, 15.0, 100)
        rp_vals = [theoretical_pressure_ratio(m, comp_speed) for m in m_vals]

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(m_vals, rp_vals, label=f"Pressure Ratio Curve @ {comp_speed:.0f} RPM", color="#1f77b4", lw=2)
        ax.axvline(SURGE_FLOW_KG_S, color="crimson", linestyle="--", lw=2, label=f"Surge Limit ({SURGE_FLOW_KG_S} kg/s)")
        ax.axvspan(6.0, SURGE_FLOW_KG_S, color="crimson", alpha=0.15, label="Surge Danger Zone")
        ax.scatter([mass_flow], [p_ratio], color="green" if pred == 0 else "red", s=130, zorder=5, label="Live Operating Point")
        ax.set_xlabel("Mass Flow Rate ṁ (kg/s)")
        ax.set_ylabel("Pressure Ratio (P₂ / P₁)")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend()
        st.pyplot(fig)
    with c2:
        st.subheader("🔬 Mechanical & Aerodynamic Gauges")
        st.markdown(f"**Discharge Temperature (T₂):** `{discharge_t_c:.1f} °C` (Suction: `{suction_t_c:.1f} °C`)")
        st.markdown(f"**Polytropic Head (H_p):** `{head_kj_kg:.1f} kJ/kg`")
        st.markdown(f"**Total Gas Power Required:** `{gas_power_kw:,.1f} kW`")
        st.markdown("---")
        st.markdown(f"**Vibration Status:** {comp_diag['vibration_status']}")
        st.progress(min(comp_vibration / 10.0, 1.0))
        st.markdown(f"**Surge Proximity:** {comp_diag['surge_status']}")
        st.progress(max(0.0, min(surge_margin_pct / 50.0, 1.0)))

    st.markdown("---")
    st.subheader("📋 Engineering Root-Cause & Field Action Report")
    r1, r2 = st.columns(2)
    with r1:
        st.markdown("#### 🔍 Observed Physical Anomalies")
        for item in comp_diag["indicators"]:
            st.markdown(f"- {item}")
    with r2:
        st.markdown("#### 🛠️ Recommended Corrective Interventions")
        for item in comp_diag["actions"]:
            st.markdown(f"- {item}")