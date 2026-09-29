"""
AI Energy & Equipment Intelligence Suite
Unified Industrial Fleet Monitor & Diagnostic Matrix
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import os
import sys

# Ensure root directory is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from diagnostics.heat_exchanger_diagnostics import HeatExchangerDiagnosticEngine
from diagnostics.report_generator import generate_pdf_report

st.set_page_config(
    page_title="AI Energy & Equipment Intelligence Suite",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Clean Industrial Dashboard
st.markdown("""
<style>
    /* Add top/bottom padding to prevent header clipping */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Ensure KPI values stay on one line cleanly */
    [data-testid="stMetricValue"] {
        font-size: 1.55rem !important;
        white-space: nowrap !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.90rem !important;
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
    "Select Industrial View:",
    [
        "Global Fleet Health Matrix",
        "Centrifugal Pump System",
        "Centrifugal Gas Compressor System",
        "Shell & Tube Heat Exchanger"
    ]
)
st.sidebar.markdown("---")

# =========================================================
# VIEW 0: GLOBAL FLEET HEALTH MATRIX
# =========================================================
if selected_asset == "Global Fleet Health Matrix":
    st.title("🏭 Plant Fleet Health & Energy Leakage Matrix")
    st.caption("Central Supervisory Overview: Real-time degradation across all connected plant systems")

    fleet_summary = [
        {"Asset": "Centrifugal Pump P-101A", "Type": "Rotating Hydraulic", "Health Index": 88.5, "Alarm State": "NORMAL", "Energy Penalty (kW)": 2.1, "Loss ($/yr)": 2116.80},
        {"Asset": "Gas Compressor K-201", "Type": "Centrifugal Gas", "Health Index": 72.0, "Alarm State": "WARNING", "Energy Penalty (kW)": 14.8, "Loss ($/yr)": 14918.40},
        {"Asset": "Heat Exchanger E-301", "Type": "Shell & Tube", "Health Index": 92.6, "Alarm State": "NORMAL", "Energy Penalty (kW)": 0.25, "Loss ($/yr)": 250.83}
    ]
    df_fleet = pd.DataFrame(fleet_summary)

    total_loss = df_fleet["Loss ($/yr)"].sum()
    total_waste_kw = df_fleet["Energy Penalty (kW)"].sum()
    avg_health = df_fleet["Health Index"].mean()

    col1, col2, col3 = st.columns(3)
    col1.metric("Average Fleet Health", f"{avg_health:.1f} / 100")
    col2.metric("Total Parasitic Power Waste", f"{total_waste_kw:.2f} kW")
    col3.metric("Annualized Plant Leakage", f"${total_loss:,.2f} USD/yr", delta_color="inverse")

    st.markdown("---")

    st.subheader("Asset Status Summary")
    st.dataframe(
        df_fleet.style.format({
            "Health Index": "{:.1f}%",
            "Energy Penalty (kW)": "{:.2f} kW",
            "Loss ($/yr)": "${:,.2f}"
        }),
        width="stretch"
    )

    fig_matrix = go.Figure()
    colors = ["#00CC96" if s == "NORMAL" else ("#FFA15A" if s == "WARNING" else "#EF553B") for s in df_fleet["Alarm State"]]
    fig_matrix.add_trace(go.Bar(
        x=df_fleet["Asset"],
        y=df_fleet["Health Index"],
        marker_color=colors,
        text=[f"{h:.1f}%" for h in df_fleet["Health Index"]],
        textposition="outside"
    ))
    fig_matrix.update_layout(yaxis_range=[0, 115], yaxis_title="Health Index (%)", height=320, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_matrix, width="stretch")

# =========================================================
# ASSET 1: CENTRIFUGAL PUMP SYSTEM
# =========================================================
elif selected_asset == "Centrifugal Pump System":
    st.title("🌊 Centrifugal Pump: Hydraulic & Mechanical Fleet Monitor")
    st.caption("Physics: Euler Droop, Affinity Laws, ISO 10816-3 Vibration Severity")

    st.sidebar.subheader("Hydraulic Operating Point")
    flow_m3h = st.sidebar.slider("Flow Rate Q (m³/h)", 20.0, 180.0, 95.0, 1.0)
    speed_rpm = st.sidebar.slider("Shaft Speed N (RPM)", 1200, 3600, 2950, 50)
    fluid_density = st.sidebar.slider("Fluid Density ρ (kg/m³)", 700.0, 1200.0, 1000.0, 10.0)

    st.sidebar.subheader("Mechanical Degradation")
    wear_ring_slip = st.sidebar.slider("Wear-Ring Slip (%)", 0.0, 30.0, 0.0, 1.0)
    vibration_rms = st.sidebar.slider("Vibration (mm/s RMS)", 0.5, 12.0, 1.8, 0.1)

    speed_ratio = speed_rpm / 2950.0
    q_ref = flow_m3h / speed_ratio
    h_nominal = (85.0 - 0.0022 * (q_ref ** 2)) * (speed_ratio ** 2)
    head_actual = max(5.0, h_nominal * (1.0 - (wear_ring_slip / 100.0)))

    q_m3s = flow_m3h / 3600.0
    hydraulic_power_kw = (fluid_density * 9.81 * q_m3s * head_actual) / 1000.0
    eta_nominal = max(0.35, 0.82 - 0.45 * (((flow_m3h - 100.0 * speed_ratio) / (100.0 * speed_ratio)) ** 2))
    eta_actual = max(0.20, eta_nominal * (1.0 - (wear_ring_slip / 120.0)))
    shaft_power_kw = hydraulic_power_kw / eta_actual

    excess_power_kw = max(0.0, shaft_power_kw - (hydraulic_power_kw / eta_nominal))
    annual_elec_loss = excess_power_kw * 0.12 * 8400

    if vibration_rms <= 2.3:
        iso_zone, vib_severity = "Zone A", "NORMAL"
    elif vibration_rms <= 4.5:
        iso_zone, vib_severity = "Zone B", "NORMAL"
    elif vibration_rms <= 7.1:
        iso_zone, vib_severity = "Zone C", "WARNING"
    else:
        iso_zone, vib_severity = "Zone D", "CRITICAL"

    pump_findings = []
    pump_actions = []
    if wear_ring_slip > 15.0:
        pump_findings.append(f"Internal recirculation slip detected ({wear_ring_slip}%). Head output dropped by {h_nominal - head_actual:.1f} m.")
        pump_actions.append("Inspect impeller wear-ring clearances. Replace worn rings.")
    if vib_severity in ["WARNING", "CRITICAL"]:
        pump_findings.append(f"Vibration ({vibration_rms} mm/s) violates ISO 10816-3 {iso_zone} limits.")
        pump_actions.append("Perform dynamic rotor balancing and alignment audit.")
    if not pump_findings:
        pump_findings.append("Hydraulic and mechanical conditions are within baseline tolerances.")
        pump_actions.append("Continue routine scheduled lubrication intervals.")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Head (H)", f"{head_actual:.1f} m")
    col2.metric("Hydraulic Power", f"{hydraulic_power_kw:.1f} kW")
    col3.metric("Shaft Power", f"{shaft_power_kw:.1f} kW")
    col4.metric("Efficiency (η)", f"{eta_actual * 100:.1f} %")
    col5.metric("Power Waste", f"{excess_power_kw:.2f} kW", delta=f"-${annual_elec_loss:,.0f}/yr", delta_color="inverse")

    st.markdown("---")

    kpis_pump = {
        "Flow Rate": f"{flow_m3h:.1f} m3/h",
        "Developed Head": f"{head_actual:.1f} m",
        "Shaft Speed": f"{speed_rpm} RPM",
        "Hydraulic Power": f"{hydraulic_power_kw:.1f} kW",
        "Shaft Power": f"{shaft_power_kw:.1f} kW",
        "Pump Efficiency": f"{eta_actual*100:.1f} %",
        "ISO Vibration RMS": f"{vibration_rms:.2f} mm/s ({iso_zone})"
    }
    pdf_bytes = generate_pdf_report(
        "Centrifugal Pump System P-101A",
        vib_severity,
        round(max(10.0, 100.0 - wear_ring_slip - vibration_rms * 4), 1),
        annual_elec_loss,
        kpis_pump,
        pump_findings,
        pump_actions
    )
    st.sidebar.download_button(
        label="📄 Export Diagnostic Work Order (PDF)",
        data=pdf_bytes,
        file_name="pump_diagnostic_report.pdf",
        mime="application/pdf"
    )

    vcol1, vcol2 = st.columns([1.2, 1.0])
    with vcol1:
        st.subheader("Hydraulic Droop Curve")
        q_curve = np.linspace(10.0, 160.0, 50)
        h_clean = (85.0 - 0.0022 * ((q_curve / speed_ratio) ** 2)) * (speed_ratio ** 2)
        fig_pump = go.Figure()
        fig_pump.add_trace(go.Scatter(x=q_curve, y=h_clean, mode="lines", name="Design Curve", line=dict(color="#00CC96", dash="dash")))
        fig_pump.add_trace(go.Scatter(x=[flow_m3h], y=[head_actual], mode="markers", marker=dict(color="#EF553B", size=14), name="Operating Point"))
        fig_pump.update_layout(xaxis_title="Flow Q (m³/h)", yaxis_title="Head H (m)", height=320, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_pump, width="stretch")

    with vcol2:
        st.subheader("ISO 10816-3 Vibration Severity")
        fig_vib = go.Figure(go.Indicator(
            mode="gauge+number",
            value=vibration_rms,
            number={"suffix": " mm/s"},
            gauge={
                'axis': {'range': [0, 12.0]},
                'bar': {'color': "#636EFA"},
                'steps': [
                    {'range': [0, 2.3], 'color': "rgba(0, 204, 150, 0.3)"},
                    {'range': [2.3, 4.5], 'color': "rgba(0, 204, 150, 0.15)"},
                    {'range': [4.5, 7.1], 'color': "rgba(255, 161, 90, 0.35)"},
                    {'range': [7.1, 12.0], 'color': "rgba(239, 85, 59, 0.45)"}
                ]
            }
        ))
        fig_vib.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_vib, width="stretch")

# =========================================================
# ASSET 2: CENTRIFUGAL GAS COMPRESSOR SYSTEM
# =========================================================
elif selected_asset == "Centrifugal Gas Compressor System":
    st.title("🌀 Centrifugal Gas Compressor: Aerodynamic & Thermodynamic Monitor")
    st.caption("Physics: ASME PTC 10 Schultz Head, Surge Margin, Real-Gas Thermodynamics")

    st.sidebar.subheader("Compressor Suction Conditions")
    p1_bar = st.sidebar.slider("Suction Pressure P1 (bar)", 1.0, 25.0, 8.5, 0.5)
    t1_c = st.sidebar.slider("Suction Temp T1 (°C)", 10.0, 50.0, 32.0, 1.0)
    mass_flow = st.sidebar.slider("Mass Flow Rate ṁ (kg/s)", 5.0, 45.0, 22.0, 0.5)
    p2_bar = st.sidebar.slider("Discharge Pressure P2 (bar)", p1_bar + 2.0, p1_bar * 4.5, p1_bar * 2.8, 0.5)
    eta_p = st.sidebar.slider("Polytropic Efficiency η_p", 0.60, 0.88, 0.81, 0.01)

    t1_k = t1_c + 273.15
    rp = p2_bar / p1_bar
    k_gas = 1.31
    n_exp = 1.0 / (1.0 - ((k_gas - 1.0) / (k_gas * eta_p)))
    exp_f = (n_exp - 1.0) / n_exp
    t2_c = (t1_k * (rp ** exp_f)) - 273.15
    head_poly = 0.96 * (8.314 / 18.2) * t1_k * (n_exp / (n_exp - 1.0)) * ((rp ** exp_f) - 1.0)
    gas_power_kw = (mass_flow * head_poly) / eta_p

    m_dot_surge = 9.5 * np.sqrt(rp)
    surge_margin = ((mass_flow - m_dot_surge) / m_dot_surge) * 100.0

    surge_state = "CRITICAL" if surge_margin < 10.0 else ("WARNING" if surge_margin < 18.0 else "NORMAL")
    surge_color = "#EF553B" if surge_margin < 10.0 else ("#FFA15A" if surge_margin < 18.0 else "#00CC96")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Pressure Ratio", f"{rp:.2f}")
    col2.metric("Discharge Temp T2", f"{t2_c:.1f} °C")
    col3.metric("Polytropic Head", f"{head_poly:.1f} kJ/kg")
    col4.metric("Gas Power", f"{gas_power_kw:,.0f} kW")
    col5.metric("Surge Margin", f"{surge_margin:.1f} %", delta=f"{'SURGE RISK' if surge_margin < 10 else 'OK'}", delta_color="inverse")

    st.markdown("---")

    kpis_comp = {
        "Suction Pressure P1": f"{p1_bar:.2f} bar",
        "Discharge Pressure P2": f"{p2_bar:.2f} bar",
        "Pressure Ratio rp": f"{rp:.2f}",
        "Suction Temp T1": f"{t1_c:.1f} °C",
        "Discharge Temp T2": f"{t2_c:.1f} °C",
        "Polytropic Head": f"{head_poly:.1f} kJ/kg",
        "Gas Power": f"{gas_power_kw:,.0f} kW",
        "Surge Margin": f"{surge_margin:.1f} %"
    }
    pdf_comp_bytes = generate_pdf_report(
        "Centrifugal Gas Compressor K-201",
        surge_state,
        round(max(5.0, min(100.0, surge_margin * 2.5)), 1),
        14918.40 if surge_state != "NORMAL" else 0.0,
        kpis_comp,
        [f"Surge Margin is {surge_margin:.1f}% against critical 10% trip boundary.", f"Discharge temperature reaches {t2_c:.1f} °C."],
        ["Modulate anti-surge recycle valve (ASV).", "Audit IGV actuator position."]
    )
    st.sidebar.download_button(
        label="📄 Export Diagnostic Work Order (PDF)",
        data=pdf_comp_bytes,
        file_name="compressor_diagnostic_report.pdf",
        mime="application/pdf"
    )

    ccol1, ccol2 = st.columns([1.2, 1.0])
    with ccol1:
        st.subheader("Aerodynamic Compressor Map")
        m_range = np.linspace(8.0, 45.0, 50)
        head_curve = [head_poly * (1.15 - 0.003 * (m ** 1.8)) for m in m_range]
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Scatter(x=m_range, y=head_curve, mode="lines", name="Speed Line", line=dict(color="#636EFA", width=2.5)))
        fig_comp.add_trace(go.Scatter(x=[mass_flow], y=[head_poly], mode="markers", marker=dict(color=surge_color, size=14), name="Operating Point"))
        fig_comp.update_layout(xaxis_title="Mass Flow ṁ (kg/s)", yaxis_title="Polytropic Head (kJ/kg)", height=320, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_comp, width="stretch")

    with ccol2:
        st.subheader("Surge Stability Margin")
        fig_sm = go.Figure(go.Indicator(
            mode="gauge+number",
            value=max(0.0, surge_margin),
            number={"suffix": "%"},
            gauge={
                'axis': {'range': [0, 45]},
                'bar': {'color': surge_color},
                'steps': [
                    {'range': [0, 10], 'color': "rgba(239, 85, 59, 0.45)"},
                    {'range': [10, 18], 'color': "rgba(255, 161, 90, 0.35)"},
                    {'range': [18, 45], 'color': "rgba(0, 204, 150, 0.25)"}
                ]
            }
        ))
        fig_sm.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_sm, width="stretch")

# =========================================================
# ASSET 3: SHELL & TUBE HEAT EXCHANGER SYSTEM
# =========================================================
elif selected_asset == "Shell & Tube Heat Exchanger":
    st.title("🔥 Shell & Tube Heat Exchanger: Thermal & Hydraulic Monitor")
    st.caption("Physics: TEMA Standards, Counter-flow LMTD, Overall U-factor, Hydraulic Pumping Penalties")

    @st.cache_resource
    def load_hx_engine():
        return HeatExchangerDiagnosticEngine()

    hx_engine = load_hx_engine()

    st.sidebar.subheader("Process Boundary Conditions")
    m_dot_hot = st.sidebar.slider("Hot Flow (kg/s)", 10.0, 30.0, 18.5, 0.5)
    m_dot_cold = st.sidebar.slider("Cold Flow (kg/s)", 15.0, 50.0, 32.0, 0.5)
    t_hot_in = st.sidebar.slider("Hot Inlet Temp (°C)", 100.0, 180.0, 145.0, 1.0)
    t_cold_in = st.sidebar.slider("Cold Inlet Temp (°C)", 15.0, 45.0, 28.0, 0.5)

    st.sidebar.subheader("Degradation Presets")
    scenario = st.sidebar.selectbox(
        "Operating State Preset:",
        ["Normal Clean", "Tube-Side Fouling", "Shell-Side Fouling", "Severe Dual Fouling", "Tube Bypass"]
    )

    if scenario == "Normal Clean":
        rf_val, hot_dp_val, cold_dp_val = 0.00008, 0.86, 0.56
    elif scenario == "Tube-Side Fouling":
        rf_val, hot_dp_val, cold_dp_val = 0.00065, 1.55, 0.58
    elif scenario == "Shell-Side Fouling":
        rf_val, hot_dp_val, cold_dp_val = 0.00062, 0.88, 1.15
    elif scenario == "Severe Dual Fouling":
        rf_val, hot_dp_val, cold_dp_val = 0.00105, 1.95, 1.35
    elif scenario == "Tube Bypass":
        rf_val, hot_dp_val, cold_dp_val = 0.00010, 0.62, 0.59

    u_actual = 1.0 / ((1.0 / 680.0) + rf_val)
    c_h = m_dot_hot * 2.45 * 1000.0
    c_c = m_dot_cold * 4.184 * 1000.0
    c_min = min(c_h, c_c)
    c_max = max(c_h, c_c)
    cr = c_min / c_max

    ntu = (u_actual * 125.0) / c_min
    eff = (1.0 - np.exp(-ntu * (1.0 - cr))) / (1.0 - cr * np.exp(-ntu * (1.0 - cr))) if cr < 0.999 else ntu / (1.0 + ntu)

    q_watts = eff * c_min * (t_hot_in - t_cold_in)
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
        "thermal_effectiveness": eff
    }

    diag = hx_engine.diagnose_packet(telemetry_packet)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Heat Duty", f"{q_kw:.1f} kW")
    col2.metric("LMTD", f"{lmtd:.1f} °C")
    col3.metric("U-Coeff", f"{u_actual:.1f} W/m²·K", delta=f"-{diag['u_degradation_pct']}%", delta_color="inverse")
    col4.metric("TEMA Fouling (Rf)", f"{rf_val:.5f}", delta=f"{'ALERT' if rf_val > 0.00035 else 'OK'}", delta_color="inverse")
    col5.metric("Pumping Waste", f"{diag['total_pumping_penalty_kw']:.2f} kW", delta=f"-${diag['annual_financial_loss_usd']:,.0f}/yr", delta_color="inverse")

    st.markdown("---")

    kpis_hx = {
        "Heat Duty (Q)": f"{q_kw:.1f} kW",
        "LMTD": f"{lmtd:.1f} °C",
        "Heat Transfer Coeff (U)": f"{u_actual:.1f} W/(m2*K)",
        "TEMA Fouling Factor (Rf)": f"{rf_val:.6f} m2*K/W",
        "Hot Stream Pressure Drop": f"{hot_dp_val:.2f} bar",
        "Cold Stream Pressure Drop": f"{cold_dp_val:.2f} bar",
        "Hydraulic Energy Penalty": f"{diag['total_pumping_penalty_kw']:.2f} kW"
    }
    pdf_hx_bytes = generate_pdf_report(
        "Shell & Tube Exchanger E-301",
        diag["condition"],
        diag["health_index"],
        diag["annual_financial_loss_usd"],
        kpis_hx,
        diag["findings"],
        diag["recommendations"]
    )
    st.sidebar.download_button(
        label="📄 Export Diagnostic Work Order (PDF)",
        data=pdf_hx_bytes,
        file_name="exchanger_diagnostic_report.pdf",
        mime="application/pdf"
    )

    vis_col1, vis_col2 = st.columns([1.2, 1.0])
    with vis_col1:
        st.subheader("Counter-Current Temperature Profiles")
        pos = np.linspace(0, 100, 50)
        th_p = t_hot_in - (t_hot_in - t_hot_out) * (pos / 100.0)
        tc_p = t_cold_out - (t_cold_out - t_cold_in) * (pos / 100.0)
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(x=pos, y=th_p, mode="lines", name="Hot Stream (Tube)", line=dict(color="#EF553B", width=3.5)))
        fig_temp.add_trace(go.Scatter(x=pos, y=tc_p, mode="lines", name="Cold Stream (Shell)", line=dict(color="#00CC96", width=3.5)))
        fig_temp.update_layout(xaxis_title="Normalized Tube Length (%)", yaxis_title="Temperature (°C)", height=320, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_temp, width="stretch")

    with vis_col2:
        st.subheader("TEMA Fouling Resistance Margin")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=rf_val,
            number={"valueformat": ".5f"},
            gauge={
                'axis': {'range': [0, 0.0014]},
                'bar': {'color': "#636EFA"},
                'steps': [
                    {'range': [0, 0.00035], 'color': "rgba(0, 204, 150, 0.25)"},
                    {'range': [0.00035, 0.00075], 'color': "rgba(255, 161, 90, 0.35)"},
                    {'range': [0.00075, 0.0014], 'color': "rgba(239, 85, 59, 0.45)"}
                ]
            }
        ))
        fig_gauge.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_gauge, width="stretch")

    rcol1, rcol2 = st.columns(2)
    with rcol1:
        st.subheader("🔍 Physics-Informed Diagnostic Observations")
        for finding in diag["findings"]:
            st.markdown(f"- {finding}")
    with rcol2:
        st.subheader("🛠️ Prescriptive Engineering Actions")
        for rec in diag["recommendations"]:
            st.markdown(f"✔ **{rec}**")