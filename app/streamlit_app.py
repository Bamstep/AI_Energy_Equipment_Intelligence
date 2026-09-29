import os
import sys
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Ensure project root is available for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engineering.pump_engineering import theoretical_pump_head, theoretical_efficiency, Q_BEP
from engineering.pump_intelligence import diagnose_pump_point

# ---------------------------------------------------------------------------
# STREAMLIT PAGE CONFIGURATION
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Centrifugal Pump Intelligence System",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ AI Energy / Equipment Intelligence System")
st.markdown(
    "**Centrifugal Pump Health Monitoring, Energy Degradation & Diagnostic Reasoner**  \n"
    "*Focus: Mechanical Engineering + Fluid Dynamics + Machine Learning*"
)
st.markdown("---")

# ---------------------------------------------------------------------------
# SIDEBAR CONTROLS (OPERATIONAL TELEMETRY)
# ---------------------------------------------------------------------------
st.sidebar.header("🕹️ Pump Operating Inputs")
st.sidebar.markdown("Simulate sensor readings across the equipment envelope:")

flow_rate = st.sidebar.slider(
    "Flow Rate Q (m³/s)",
    min_value=0.010, max_value=0.040, value=0.0270, step=0.0005, format="%.4f"
)
st.sidebar.caption(f"Equivalent: {flow_rate * 3600:.1f} m³/h | BEP: {Q_BEP} m³/s")

rpm = st.sidebar.slider(
    "Shaft Speed N (RPM)",
    min_value=1400.0, max_value=1600.0, value=1500.0, step=1.0
)

head = st.sidebar.slider(
    "Delivered Head H (m)",
    min_value=30.0, max_value=65.0, value=50.3, step=0.1
)

efficiency = st.sidebar.slider(
    "Hydraulic Efficiency (η)",
    min_value=0.25, max_value=0.85, value=0.76, step=0.01
)

input_power = st.sidebar.slider(
    "Input Shaft Power (kW)",
    min_value=10.0, max_value=35.0, value=17.5, step=0.1
)

vibration = st.sidebar.slider(
    "Overall Vibration RMS (mm/s)",
    min_value=1.0, max_value=10.0, value=2.2, step=0.1
)

operating_hours = st.sidebar.slider(
    "Cumulative Service Hours (h)",
    min_value=100.0, max_value=20000.0, value=3500.0, step=100.0
)

# ---------------------------------------------------------------------------
# RUN DIAGNOSTIC REASONER
# ---------------------------------------------------------------------------
diag = diagnose_pump_point(
    flow_rate_m3s=flow_rate,
    rpm=rpm,
    head_m=head,
    efficiency=efficiency,
    input_power_kw=input_power,
    vibration_mm_s=vibration,
    operating_hours=operating_hours
)

# ---------------------------------------------------------------------------
# MAIN DASHBOARD: TOP KPI METRICS
# ---------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    if diag["ml_prediction"] == "Normal":
        st.success("### Status: NORMAL")
    else:
        st.error("### Status: ABNORMAL")
    st.caption(f"Degradation Risk: **{diag['abnormal_probability']*100:.1f}%**")

with col2:
    if diag["vibration_severity"] == "Healthy":
        st.metric("Vibration Health", f"{vibration:.2f} mm/s", delta="ISO Zone A/B", delta_color="normal")
    elif diag["vibration_severity"] == "Warning":
        st.metric("Vibration Health", f"{vibration:.2f} mm/s", delta="ISO Zone C (Warning)", delta_color="inverse")
    else:
        st.metric("Vibration Health", f"{vibration:.2f} mm/s", delta="ISO Zone D (Critical)", delta_color="inverse")

with col3:
    delta_color = "normal" if diag["efficiency_deviation_pct"] >= -5.0 else "inverse"
    st.metric(
        "Efficiency Deviation",
        f"{efficiency*100:.1f}%",
        delta=f"{diag['efficiency_deviation_pct']:+.1f}% vs baseline",
        delta_color=delta_color
    )

with col4:
    cost_str = f"${diag['annual_cost_penalty_usd']:,.0f}/yr"
    st.metric(
        "Energy Penalty",
        f"{diag['excess_power_kw']:.2f} kW",
        delta=cost_str if diag['excess_power_kw'] > 0.5 else "Optimal",
        delta_color="inverse" if diag['excess_power_kw'] > 0.5 else "normal"
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# MIDDLE SECTION: OPERATING MAP & VIBRATION GAUGE
# ---------------------------------------------------------------------------
left_panel, right_panel = st.columns([3, 2])

with left_panel:
    st.subheader("📈 Pump Operating Map vs. Design Curve")
    
    # Generate baseline curve
    q_vals = np.linspace(0.010, 0.040, 100)
    h_vals = [theoretical_pump_head(q, rpm) for q in q_vals]

    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(q_vals, h_vals, color="#1f77b4", linewidth=2.5, label=f"Theoretical Curve @ {rpm:.0f} RPM")
    
    # Mark live operating point
    marker_color = "#2ca02c" if diag["ml_prediction"] == "Normal" else "#d62728"
    ax.scatter([flow_rate], [head], color=marker_color, s=120, zorder=5, label="Live Operating Point")
    ax.axvline(Q_BEP, color="orange", linestyle=":", alpha=0.8, label=f"BEP ({Q_BEP} m³/s)")

    ax.set_xlabel("Flow Rate Q (m³/s)")
    ax.set_ylabel("Head H (m)")
    ax.set_title("Centrifugal Pump H-Q Operating Point", fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="lower left", fontsize=9)
    st.pyplot(fig)

with right_panel:
    st.subheader("🔍 Vibration Standards (ISO 10816-3)")
    st.markdown("""
    * **Zone A/B (< 2.8 mm/s):** Permissible for continuous unrestricted operation.
    * **Zone C (2.8 – 4.5 mm/s):** Unsatisfactory; restricted long-term operation.
    * **Zone D (> 4.5 mm/s):** Unacceptable; trip/damage hazard.
    """)
    st.progress(min(float(vibration) / 10.0, 1.0))
    st.info(f"**Current Classification:** {diag['vibration_zone']}")

st.markdown("---")

# ---------------------------------------------------------------------------
# BOTTOM SECTION: ROOT CAUSE FINDINGS & RECOMMENDATIONS
# ---------------------------------------------------------------------------
st.subheader("📋 Engineering Diagnostic Assessment")

f_col, r_col = st.columns(2)

with f_col:
    st.markdown("#### 🔬 Observed Physical Indicators")
    for item in diag["findings"]:
        st.write(f"- {item}")

with r_col:
    st.markdown("#### 🛠️ Recommended Engineering Actions")
    for item in diag["recommendations"]:
        st.write(f"- {item}")

st.markdown("---")
st.caption(
    "⚠️ **Portfolio Project Disclaimer:** Built on synthetic physics-informed pump models and illustrative parameters. "
    "Not a certified industrial safety system."
)