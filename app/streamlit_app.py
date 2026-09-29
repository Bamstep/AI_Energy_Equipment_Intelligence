"""
AI Energy & Equipment Intelligence Suite
Unified Industrial Fleet Monitor
Assets:
  1. Centrifugal Pump System (Hydraulics & Mechanics - ISO 10816-3)
  2. Centrifugal Gas Compressor System (Thermodynamics & Aerodynamics - Schultz/ASME PTC 10)
  3. Shell & Tube Heat Exchanger System (Thermal & Hydraulics - TEMA Standards)
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import os
import sys

# Ensure root directory is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from diagnostics.heat_exchanger_diagnostics import (
        HeatExchangerDiagnosticEngine,
        TEMA_RF_CLEAN_LIMIT,
        TEMA_RF_ALERT_LIMIT,
        TEMA_RF_CRITICAL_LIMIT
    )
except ImportError:
    HeatExchangerDiagnosticEngine = None

st.set_page_config(
    page_title="AI Energy & Equipment Intelligence Suite",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background-color: #0E1117;
        border: 1px solid #262730;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .status-normal { color: #00CC96; font-weight: bold; }
    .status-warning { color: #FFA15A; font-weight: bold; }
    .status-critical { color: #EF553B; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.sidebar.title("⚡ Equipment Fleet")
selected_asset = st.sidebar.radio(
    "Select Industrial Asset:",
    [
        "Centrifugal Pump System",
        "Centrifugal Gas Compressor System",
        "Shell & Tube Heat Exchanger"
    ]
)
st.sidebar.markdown("---")

# =========================================================
# ASSET 1: CENTRIFUGAL PUMP SYSTEM
# =========================================================
if selected_asset == "Centrifugal Pump System":
    st.title("🌊 Centrifugal Pump: Hydraulic & Mechanical Fleet Monitor")
    st.caption("Physics: Euler Turbomachinery Droop, Affinity Scaling Laws, ISO 10816-3 Vibration Severity")

    st.sidebar.subheader("Hydraulic Operating Point")
    flow_m3h = st.sidebar.slider("Flow Rate Q (m³/h)", 20.0, 180.0, 95.0, 1.0)
    speed_rpm = st.sidebar.slider("Shaft Speed N (RPM)", 1200, 3600, 2950, 50)
    fluid_density = st.sidebar.slider("Fluid Density ρ (kg/m³)", 700.0, 1200.0, 1000.0, 10.0)

    st.sidebar.subheader("Mechanical Degradation Injections")
    wear_ring_slip = st.sidebar.slider("Impeller Wear / Recirculation Slip (%)", 0.0, 30.0, 0.0, 1.0)
    vibration_rms = st.sidebar.slider("Overall Bearing Vibration (mm/s RMS)", 0.5, 12.0, 1.8, 0.1)

    # First-Principles Pump Physics
    n_ref = 2950.0
    speed_ratio = speed_rpm / n_ref
    q_ref = flow_m3h / speed_ratio
    
    # Quadratic Droop Curve: H = (H0 - k*Q^2) * (N/N_ref)^2
    h0 = 85.0
    k_droop = 0.0022
    h_nominal = (h0 - k_droop * (q_ref ** 2)) * (speed_ratio ** 2)
    # Head degradation due to internal wear ring clearance slip
    head_actual = max(5.0, h_nominal * (1.0 - (wear_ring_slip / 100.0)))

    # Power & Efficiency
    q_m3s = flow_m3h / 3600.0
    g = 9.81
    hydraulic_power_kw = (fluid_density * g * q_m3s * head_actual) / 1000.0
    
    # Peak efficiency envelope model
    bep_flow = 100.0 * speed_ratio
    flow_dev = abs(flow_m3h - bep_flow) / bep_flow
    eta_nominal = max(0.35, 0.82 - 0.45 * (flow_dev ** 2))
    eta_actual = max(0.20, eta_nominal * (1.0 - (wear_ring_slip / 120.0)))
    shaft_power_kw = hydraulic_power_kw / eta_actual

    # Baseline design shaft power (healthy pump)
    ideal_shaft_power_kw = hydraulic_power_kw / eta_nominal
    excess_power_kw = max(0.0, shaft_power_kw - ideal_shaft_power_kw)
    annual_elec_loss = excess_power_kw * 0.12 * 8400

    # ISO 10816-3 Zone Logic (Class II - Medium Industrial Machinery 15kW - 300kW)
    if vibration_rms <= 2.3:
        iso_zone = "Zone A (Newly Commissioned / Excellent)"
        vib_severity = "NORMAL"
    elif vibration_rms <= 4.5:
        iso_zone = "Zone B (Unrestricted Long-Term Operation)"
        vib_severity = "NORMAL"
    elif vibration_rms <= 7.1:
        iso_zone = "Zone C (Restricted Operation / Warning)"
        vib_severity = "WARNING"
    else:
        iso_zone = "Zone D (Critical Vibration / Immediate Trip Risk)"
        vib_severity = "CRITICAL"

    # Overall Diagnostic State
    pump_findings = []
    pump_actions = []
    
    if wear_ring_slip > 15.0:
        pump_findings.append(f"Significant internal recirculatory slip detected ({wear_ring_slip}%). Head output collapsed by {h_nominal - head_actual:.1f} m.")
        pump_actions.append("Inspect impeller front/back wear-ring clearances. Replace worn wear rings.")
    if vib_severity in ["WARNING", "CRITICAL"]:
        pump_findings.append(f"Vibration levels ({vibration_rms} mm/s) exceed ISO 10816-3 acceptable limits: {iso_zone}.")
        pump_actions.append("Conduct dynamic rotor balancing and verify pump-to-motor flexible coupling alignment.")
    if not pump_findings:
        pump_findings.append("Hydraulic and mechanical indicators operate within optimum design envelopes.")
        pump_actions.append("Maintain routine oil sampling and scheduled preventative lubrication intervals.")

    # Top KPI Row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Developed Head (H)", f"{head_actual:.1f} m")
    col2.metric("Hydraulic Duty", f"{hydraulic_power_kw:.1f} kW")
    col3.metric("Shaft Power", f"{shaft_power_kw:.1f} kW")
    col4.metric("Pump Efficiency (η)", f"{eta_actual * 100:.1f} %", delta=f"-{(eta_nominal - eta_actual)*100:.1f}%" if wear_ring_slip > 0 else "0%", delta_color="inverse")
    col5.metric("Electrical Waste", f"{excess_power_kw:.2f} kW", delta=f"-${annual_elec_loss:,.0f}/yr", delta_color="inverse")

    st.markdown("---")

    # Banner
    status_class = "status-normal" if (vib_severity == "NORMAL" and wear_ring_slip < 10) else ("status-warning" if (vib_severity == "WARNING" or wear_ring_slip < 20) else "status-critical")
    status_text = "NORMAL OPERATION" if status_class == "status-normal" else ("MAINTENANCE WARNING" if status_class == "status-warning" else "CRITICAL DEFECT DETECTED")

    st.markdown(f"""
    <div style="background-color: #1A1C24; border-left: 6px solid {'#00CC96' if status_class == 'status-normal' else ('#FFA15A' if status_class == 'status-warning' else '#EF553B')}; padding: 15px 20px; border-radius: 4px; margin-bottom: 20px;">
        <h3 style="margin: 0; padding-bottom: 5px;">Machine Status: <span class="{status_class}">{status_text}</span></h3>
        <p style="margin: 0; font-size: 15px; color: #A6A9B6;">
            <strong>ISO 10816-3 Zone:</strong> {iso_zone} &nbsp;|&nbsp;
            <strong>Annual Energy Loss:</strong> ${annual_elec_loss:,.2f} USD/year
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Characteristic Head-Flow Curve & Vibration Chart
    vcol1, vcol2 = st.columns([1.2, 1.0])
    with vcol1:
        st.subheader("Hydraulic Droop Curve & Affinity Scaling")
        q_curve = np.linspace(10.0, 160.0, 60)
        h_curve_nom = (h0 - k_droop * ((q_curve / speed_ratio) ** 2)) * (speed_ratio ** 2)
        h_curve_act = h_curve_nom * (1.0 - (wear_ring_slip / 100.0))

        fig_pump = go.Figure()
        fig_pump.add_trace(go.Scatter(x=q_curve, y=h_curve_nom, mode="lines", name="Design Curve (Clean)", line=dict(color="#00CC96", dash="dash")))
        fig_pump.add_trace(go.Scatter(x=q_curve, y=h_curve_act, mode="lines", name="Actual Degraded Curve", line=dict(color="#636EFA", width=2.5)))
        fig_pump.add_trace(go.Scatter(x=[flow_m3h], y=[head_actual], mode="markers", marker=dict(color="#EF553B", size=12), name="Live Operating Point"))
        fig_pump.update_layout(xaxis_title="Flow Rate Q (m³/h)", yaxis_title="Total Head H (m)", margin=dict(l=20, r=20, t=30, b=20), height=340)
        st.plotly_chart(fig_pump, use_container_width=True)

    with vcol2:
        st.subheader("ISO 10816-3 Vibration Severity Gauge")
        fig_vib = go.Figure(go.Indicator(
            mode="gauge+number",
            value=vibration_rms,
            number={"suffix": " mm/s"},
            title={'text': "Velocity RMS [10Hz - 1000Hz]"},
            gauge={
                'axis': {'range': [0, 12.0]},
                'bar': {'color': "#636EFA"},
                'steps': [
                    {'range': [0, 2.3], 'color': "rgba(0, 204, 150, 0.35)"},
                    {'range': [2.3, 4.5], 'color': "rgba(0, 204, 150, 0.15)"},
                    {'range': [4.5, 7.1], 'color': "rgba(255, 161, 90, 0.35)"},
                    {'range': [7.1, 12.0], 'color': "rgba(239, 85, 59, 0.45)"}
                ],
                'threshold': {'line': {'color': "red", 'width': 3}, 'thickness': 0.8, 'value': 7.1}
            }
        ))
        fig_vib.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=340)
        st.plotly_chart(fig_vib, use_container_width=True)

    rcol1, rcol2 = st.columns(2)
    with rcol1:
        st.subheader("🔍 Mechanical & Hydraulic Diagnostics")
        for f in pump_findings:
            st.markdown(f"- {f}")
    with rcol2:
        st.subheader("🛠️ Prescriptive Corrective Actions")
        for a in pump_actions:
            st.markdown(f"✔ **{a}**")


# =========================================================
# ASSET 2: CENTRIFUGAL GAS COMPRESSOR SYSTEM
# =========================================================
elif selected_asset == "Centrifugal Gas Compressor System":
    st.title("🌀 Centrifugal Gas Compressor: Aerodynamic & Thermodynamic Monitor")
    st.caption("Physics: ASME PTC 10 / Schultz Polytropic Head, Surge Stability Margin, Real-Gas Compression")

    st.sidebar.subheader("Compressor Suction Conditions")
    p1_bar = st.sidebar.slider("Suction Pressure P1 (bar)", 1.0, 25.0, 8.5, 0.5)
    t1_c = st.sidebar.slider("Suction Temp T1 (°C)", 10.0, 50.0, 32.0, 1.0)
    mass_flow = st.sidebar.slider("Mass Flow Rate ṁ (kg/s)", 5.0, 45.0, 22.0, 0.5)
    p2_bar = st.sidebar.slider("Discharge Pressure P2 (bar)", p1_bar + 2.0, p1_bar * 4.5, p1_bar * 2.8, 0.5)

    st.sidebar.subheader("Aerodynamic Degradation")
    eta_polytropic = st.sidebar.slider("Polytropic Efficiency η_p", 0.60, 0.88, 0.81, 0.01)

    # Schultz Polytropic Compression Physics
    t1_k = t1_c + 273.15
    pressure_ratio = p2_bar / p1_bar
    k_gas = 1.31  # Specific heat ratio (gamma) for natural gas mix
    r_univ = 8.314  # kJ/(kmol*K)
    mw = 18.2  # kg/kmol (methane rich mix)
    r_gas = r_univ / mw  # kJ/(kg*K)
    z_avg = 0.96  # Real-gas compressibility factor

    # Polytropic exponent n: n / (n - 1) = (gamma / (gamma - 1)) * eta_p
    n_exponent = 1.0 / (1.0 - ((k_gas - 1.0) / (k_gas * eta_polytropic)))
    exp_factor = (n_exponent - 1.0) / n_exponent
    
    # Discharge Temperature (ASME PTC 10)
    t2_k = t1_k * (pressure_ratio ** exp_factor)
    t2_c = t2_k - 273.15

    # Polytropic Head (kJ/kg)
    head_polytropic = z_avg * r_gas * t1_k * (n_exponent / (n_exponent - 1.0)) * ((pressure_ratio ** exp_factor) - 1.0)
    
    # Gas Power (kW)
    gas_power_kw = (mass_flow * head_polytropic) / eta_polytropic

    # Surge Stability Line Modeling
    # Empirical surge line: m_dot_surge = a * sqrt(P2/P1)
    m_dot_surge = 9.5 * np.sqrt(pressure_ratio)
    surge_margin_pct = ((mass_flow - m_dot_surge) / m_dot_surge) * 100.0

    if surge_margin_pct < 10.0:
        surge_state = "CRITICAL: Imminent Aerodynamic Surge"
        surge_color = "#EF553B"
    elif surge_margin_pct < 18.0:
        surge_state = "WARNING: Approaching Surge Control Line (SCL)"
        surge_color = "#FFA15A"
    else:
        surge_state = "STABLE: Healthy Aerodynamic Operation"
        surge_color = "#00CC96"

    # KPI Row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Pressure Ratio (rp)", f"{pressure_ratio:.2f}")
    col2.metric("Discharge Temp T2", f"{t2_c:.1f} °C")
    col3.metric("Polytropic Head", f"{head_polytropic:.1f} kJ/kg")
    col4.metric("Gas Power Duty", f"{gas_power_kw:,.0f} kW")
    col5.metric("Surge Margin", f"{surge_margin_pct:.1f} %", delta=f"{'SURGE RISK' if surge_margin_pct < 10 else 'OK'}", delta_color="inverse")

    st.markdown("---")

    # Banner
    st.markdown(f"""
    <div style="background-color: #1A1C24; border-left: 6px solid {surge_color}; padding: 15px 20px; border-radius: 4px; margin-bottom: 20px;">
        <h3 style="margin: 0; padding-bottom: 5px;">Aerodynamic Stability: <span style="color: {surge_color};">{surge_state}</span></h3>
        <p style="margin: 0; font-size: 15px; color: #A6A9B6;">
            <strong>Surge Limit Flow:</strong> {m_dot_surge:.2f} kg/s &nbsp;|&nbsp;
            <strong>Operating Mass Flow:</strong> {mass_flow:.2f} kg/s &nbsp;|&nbsp;
            <strong>Compression Exponent (n):</strong> {n_exponent:.3f}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Compressor Map with Surge Limit Line
    ccol1, ccol2 = st.columns([1.2, 1.0])
    with ccol1:
        st.subheader("Aerodynamic Compressor Map (Head vs Flow)")
        flow_range = np.linspace(8.0, 45.0, 50)
        surge_curve_head = [head_polytropic * (1.15 - 0.003 * (m ** 1.8)) for m in flow_range]
        surge_limit_pts = np.linspace(8.0, 22.0, 30)
        surge_line_y = np.linspace(head_polytropic * 0.7, head_polytropic * 1.25, 30)

        fig_comp = go.Figure()
        fig_comp.add_trace(go.Scatter(x=surge_limit_pts, y=surge_line_y, mode="lines", name="Surge Limit Line (SLL)", line=dict(color="#EF553B", width=3, dash="dash")))
        fig_comp.add_trace(go.Scatter(x=flow_range, y=surge_curve_head, mode="lines", name="Speed Performance Characteristic", line=dict(color="#636EFA", width=2.5)))
        fig_comp.add_trace(go.Scatter(x=[mass_flow], y=[head_polytropic], mode="markers", marker=dict(color="#00CC96" if surge_margin_pct >= 18 else "#FFA15A", size=14), name="Operating Point"))
        fig_comp.update_layout(xaxis_title="Mass Flow ṁ (kg/s)", yaxis_title="Polytropic Head Hp (kJ/kg)", margin=dict(l=20, r=20, t=30, b=20), height=340)
        st.plotly_chart(fig_comp, use_container_width=True)

    with ccol2:
        st.subheader("Surge Proximity Gauge")
        fig_sgauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=max(0.0, surge_margin_pct),
            number={"suffix": "%"},
            title={'text': "Surge Margin Proximity"},
            gauge={
                'axis': {'range': [0, 45]},
                'bar': {'color': surge_color},
                'steps': [
                    {'range': [0, 10], 'color': "rgba(239, 85, 59, 0.45)"},
                    {'range': [10, 18], 'color': "rgba(255, 161, 90, 0.35)"},
                    {'range': [18, 45], 'color': "rgba(0, 204, 150, 0.25)"}
                ],
                'threshold': {'line': {'color': "red", 'width': 3}, 'thickness': 0.8, 'value': 10}
            }
        ))
        fig_sgauge.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=340)
        st.plotly_chart(fig_sgauge, use_container_width=True)

    rcol1, rcol2 = st.columns(2)
    with rcol1:
        st.subheader("🔍 Thermodynamic & Aerodynamic Findings")
        if surge_margin_pct < 10.0:
            st.markdown("- **CRITICAL:** Operating point has crossed the Surge Control Margin. Violates dynamic stability threshold.")
            st.markdown(f"- Immediate reversal of flow and high-frequency destructive acoustic cycling imminent.")
        elif surge_margin_pct < 18.0:
            st.markdown("- **WARNING:** Approaching Surge Control Line. Anti-surge valve must throttle open.")
        else:
            st.markdown("- Mass flow maintains safe aerodynamic cushion from Schultz surge limit.")
        if eta_polytropic < 0.72:
            st.markdown(f"- Polytropic efficiency degraded ({eta_polytropic*100:.1f}%). High discharge temperature excess.")
    with rcol2:
        st.subheader("🛠️ Prescriptive Engineering Actions")
        if surge_margin_pct < 18.0:
            st.markdown("✔ **Modulate Anti-Surge Recycle Valve (ASV) to recycle discharge gas back to suction cooler.**")
            st.markdown("✔ **Verify IGV (Inlet Guide Vane) actuator positioning calibration.**")
        else:
            st.markdown("✔ **Operating envelope is aerodynamically stable. Continue continuous flow telemetry tracking.**")


# =========================================================
# ASSET 3: SHELL & TUBE HEAT EXCHANGER SYSTEM
# =========================================================
elif selected_asset == "Shell & Tube Heat Exchanger":
    st.title("🔥 Shell & Tube Heat Exchanger: Thermal & Hydraulic Intelligence")
    st.caption("Physics: TEMA Standards, Counter-flow LMTD, Overall U-factor, Hydraulic Pumping Penalties")

    @st.cache_resource
    def load_hx_engine():
        if HeatExchangerDiagnosticEngine is not None:
            return HeatExchangerDiagnosticEngine()
        return None

    hx_engine = load_hx_engine()

    st.sidebar.subheader("Process Boundary Conditions")
    m_dot_hot = st.sidebar.slider("Hot Fluid Flow (kg/s)", 10.0, 30.0, 18.5, 0.5)
    m_dot_cold = st.sidebar.slider("Cold Fluid Flow (kg/s)", 15.0, 50.0, 32.0, 0.5)
    t_hot_in = st.sidebar.slider("Hot Inlet Temp (°C)", 100.0, 180.0, 145.0, 1.0)
    t_cold_in = st.sidebar.slider("Cold Inlet Temp (°C)", 15.0, 45.0, 28.0, 0.5)

    st.sidebar.subheader("Degradation & Pressure Adjustments")
    scenario = st.sidebar.selectbox(
        "Inject Operating State Preset:",
        ["Custom Sliders", "Normal Clean", "Tube-Side Fouling", "Shell-Side Fouling", "Severe Dual Fouling", "Tube Bypass"]
    )

    if scenario == "Normal Clean":
        rf_val = 0.00008
        hot_dp_val = 0.86
        cold_dp_val = 0.56
    elif scenario == "Tube-Side Fouling":
        rf_val = 0.00065
        hot_dp_val = 1.55
        cold_dp_val = 0.58
    elif scenario == "Shell-Side Fouling":
        rf_val = 0.00062
        hot_dp_val = 0.88
        cold_dp_val = 1.15
    elif scenario == "Severe Dual Fouling":
        rf_val = 0.00105
        hot_dp_val = 1.95
        cold_dp_val = 1.35
    elif scenario == "Tube Bypass":
        rf_val = 0.00010
        hot_dp_val = 0.62
        cold_dp_val = 0.59
    else:
        rf_val = st.sidebar.slider("Fouling Factor Rf (m²·K/W)", 0.00002, 0.00150, 0.00008, 0.00002, format="%.5f")
        hot_dp_val = st.sidebar.slider("Hot Side dP (bar)", 0.40, 2.50, 0.85, 0.05)
        cold_dp_val = st.sidebar.slider("Cold Side dP (bar)", 0.30, 2.00, 0.55, 0.05)

    # First-Principles Thermodynamics
    area = 125.0
    cp_hot = 2.45
    cp_cold = 4.184
    u_clean_base = 680.0

    u_actual = 1.0 / ((1.0 / u_clean_base) + rf_val)
    c_h = m_dot_hot * cp_hot * 1000.0
    c_c = m_dot_cold * cp_cold * 1000.0
    c_min = min(c_h, c_c)
    c_max = max(c_h, c_c)
    c_ratio = c_min / c_max

    ntu = (u_actual * area) / c_min
    effectiveness = (1.0 - np.exp(-ntu * (1.0 - c_ratio))) / (1.0 - c_ratio * np.exp(-ntu * (1.0 - c_ratio))) if c_ratio < 0.999 else ntu / (1.0 + ntu)

    q_watts = effectiveness * c_min * (t_hot_in - t_cold_in)
    q_kw = q_watts / 1000.0

    t_hot_out = t_hot_in - (q_watts / c_h)
    t_cold_out = t_cold_in + (q_watts / c_c)

    dt1 = max(t_hot_in - t_cold_out, 0.1)
    dt2 = max(t_hot_out - t_cold_in, 0.1)
    lmtd = (dt1 - dt2) / np.log(dt1 / dt2) if abs(dt1 - dt2) > 1e-4 else dt1

    telemetry_packet = {
        "hot_mass_flow_kg_s": m_dot_hot,
        "cold_mass_flow_kg_s": m_dot_cold,
        "hot_temp_in_c": t_hot_in,
        "hot_temp_out_c": t_hot_out,
        "cold_temp_in_c": t_cold_in,
        "cold_temp_out_c": t_cold_out,
        "hot_dp_bar": hot_dp_val,
        "cold_dp_bar": cold_dp_val,
        "heat_duty_kw": q_kw,
        "lmtd_c": lmtd,
        "u_actual_w_m2k": u_actual,
        "fouling_factor_rf_m2k_w": rf_val,
        "thermal_effectiveness": effectiveness
    }

    if hx_engine:
        diag = hx_engine.diagnose_packet(telemetry_packet)
    else:
        diag = {
            "condition": "NORMAL CLEAN",
            "severity": "NORMAL",
            "confidence_pct": 95.0,
            "health_index": 92.0,
            "u_degradation_pct": round(max(0.0, (1 - u_actual/680.0)*100), 1),
            "total_pumping_penalty_kw": 0.25,
            "annual_financial_loss_usd": 250.0,
            "findings": ["Clean operation within baseline parameters."],
            "recommendations": ["Maintain continuous water treatment."]
        }

    # Top KPI Row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Heat Duty (Q)", f"{q_kw:.1f} kW")
    col2.metric("LMTD", f"{lmtd:.1f} °C")
    col3.metric("U-Coeff", f"{u_actual:.1f} W/m²·K", delta=f"-{diag['u_degradation_pct']}%", delta_color="inverse")
    col4.metric("TEMA Fouling (Rf)", f"{rf_val:.5f}", delta=f"{'ALERT' if rf_val > 0.00035 else 'OK'}", delta_color="inverse")
    col5.metric("Pumping Waste", f"{diag['total_pumping_penalty_kw']:.2f} kW", delta=f"-${diag['annual_financial_loss_usd']:,.0f}/yr", delta_color="inverse")

    st.markdown("---")

    # Banner
    status_class = "status-normal" if diag["severity"] == "NORMAL" else ("status-warning" if diag["severity"] == "WARNING" else "status-critical")
    st.markdown(f"""
    <div style="background-color: #1A1C24; border-left: 6px solid {'#00CC96' if diag['severity'] == 'NORMAL' else ('#FFA15A' if diag['severity'] == 'WARNING' else '#EF553B')}; padding: 15px 20px; border-radius: 4px; margin-bottom: 20px;">
        <h3 style="margin: 0; padding-bottom: 5px;">Equipment Status: <span class="{status_class}">{diag['condition'].upper()}</span> ({diag['confidence_pct']}% Model Confidence)</h3>
        <p style="margin: 0; font-size: 15px; color: #A6A9B6;">
            <strong>Asset Health Index:</strong> {diag['health_index']}/100 &nbsp;|&nbsp;
            <strong>Annual Financial Leakage:</strong> ${diag['annual_financial_loss_usd']:,.2f} USD/year
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Plots
    vis_col1, vis_col2 = st.columns([1.2, 1.0])
    with vis_col1:
        st.subheader("Counter-Current Temperature Profiles")
        pos = np.linspace(0, 100, 50)
        t_hot_profile = t_hot_in - (t_hot_in - t_hot_out) * (pos / 100.0)
        t_cold_profile = t_cold_out - (t_cold_out - t_cold_in) * (pos / 100.0)

        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(x=pos, y=t_hot_profile, mode="lines", name="Hot Stream (Tube)", line=dict(color="#EF553B", width=3.5)))
        fig_temp.add_trace(go.Scatter(x=pos, y=t_cold_profile, mode="lines", name="Cold Stream (Shell)", line=dict(color="#00CC96", width=3.5)))
        fig_temp.update_layout(xaxis_title="Normalized Tube Length (%)", yaxis_title="Temperature (°C)", margin=dict(l=20, r=20, t=30, b=20), height=340)
        st.plotly_chart(fig_temp, use_container_width=True)

    with vis_col2:
        st.subheader("TEMA Fouling Resistance Margin")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=rf_val,
            number={"valueformat": ".5f"},
            title={'text': "Fouling Factor Rf [m²·K/W]"},
            gauge={
                'axis': {'range': [0, 0.0014], 'tickformat': ".4f"},
                'bar': {'color': "#636EFA"},
                'steps': [
                    {'range': [0, 0.00035], 'color': "rgba(0, 204, 150, 0.25)"},
                    {'range': [0.00035, 0.00075], 'color': "rgba(255, 161, 90, 0.35)"},
                    {'range': [0.00075, 0.0014], 'color': "rgba(239, 85, 59, 0.45)"}
                ],
                'threshold': {'line': {'color': "red", 'width': 3}, 'thickness': 0.8, 'value': 0.00035}
            }
        ))
        fig_gauge.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=340)
        st.plotly_chart(fig_gauge, use_container_width=True)

    rec_col1, rec_col2 = st.columns(2)
    with rec_col1:
        st.subheader("🔍 Physics-Informed Diagnostic Observations")
        for finding in diag["findings"]:
            st.markdown(f"- {finding}")
    with rec_col2:
        st.subheader("🛠️ Prescriptive Engineering Actions")
        for rec in diag["recommendations"]:
            st.markdown(f"✔ **{rec}**")