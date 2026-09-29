import os
import sys
import joblib
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engineering.pump_engineering import (
    theoretical_pump_head,
    theoretical_efficiency,
    calculate_hydraulic_power_kw,
    calculate_input_power_kw,
    Q_BEP
)

# ---------------------------------------------------------------------------
# LOAD TRAINED MODEL
# ---------------------------------------------------------------------------
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "pump_condition_model.joblib")

def load_intelligence_system():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Run train_pump_classifier.py first.")
    artifact = joblib.load(MODEL_PATH)
    return artifact["model"], artifact["feature_names"]


# ---------------------------------------------------------------------------
# INTELLIGENT DIAGNOSTIC REASONER
# ---------------------------------------------------------------------------
def diagnose_pump_point(flow_rate_m3s, rpm, head_m, efficiency, input_power_kw, vibration_mm_s, operating_hours):
    """
    Combines ML classification with physics-based deviations to provide
    actionable engineering intelligence on centrifugal pump health.
    """
    model, feature_names = load_intelligence_system()

    # 1. Prepare input vector for ML inference
    input_df = pd.DataFrame([{
        "flow_rate_m3s": flow_rate_m3s,
        "rpm": rpm,
        "head_m": head_m,
        "efficiency": efficiency,
        "input_power_kw": input_power_kw,
        "vibration_mm_s": vibration_mm_s,
        "operating_hours": operating_hours
    }])[feature_names]

    ml_prediction = model.predict(input_df)[0]
    ml_probabilities = model.predict_proba(input_df)[0]
    prob_abnormal = ml_probabilities[0] if model.classes_[0] == "Abnormal" else ml_probabilities[1]

    # 2. Physics-Based Deviations
    expected_head = theoretical_pump_head(flow_rate_m3s, rpm)
    head_deviation_m = head_m - expected_head

    expected_eta = theoretical_efficiency(flow_rate_m3s)
    efficiency_deviation_pct = (efficiency - expected_eta) * 100.0

    expected_ph = calculate_hydraulic_power_kw(flow_rate_m3s, expected_head)
    expected_pin = calculate_input_power_kw(expected_ph, expected_eta)
    excess_power_kw = max(0.0, input_power_kw - expected_pin)

    # Annualized energy waste estimation (assuming 8,000 operating hours/year @ $0.12/kWh)
    annual_cost_penalty_usd = excess_power_kw * 8000.0 * 0.12

    # 3. ISO 10816-3 Vibration Severity Classification
    if vibration_mm_s < 2.8:
        vibration_zone = "Zone A/B (Normal / Acceptable)"
        vibration_severity = "Healthy"
    elif 2.8 <= vibration_mm_s <= 4.5:
        vibration_zone = "Zone C (Unsatisfactory / Monitor Trend)"
        vibration_severity = "Warning"
    else:
        vibration_zone = "Zone D (Unacceptable / Trip Risk)"
        vibration_severity = "Critical"

    # 4. Root-Cause Engineering Indicators (Diagnostic Reasoning)
    findings = []
    recommendations = []

    # Vibration checks
    if vibration_severity == "Critical":
        findings.append(f"Severe vibration ({vibration_mm_s:.2f} mm/s) in ISO {vibration_zone}.")
        recommendations.append("Perform FFT vibration spectrum analysis to check for unbalance, misalignment, or bearing defect frequencies (BPFO/BPFI).")
    elif vibration_severity == "Warning":
        findings.append(f"Elevated vibration ({vibration_mm_s:.2f} mm/s) approaching ISO Zone C boundary.")
        recommendations.append("Increase vibration monitoring frequency and check lube oil condition.")

    # Efficiency & Head degradation checks
    if efficiency_deviation_pct < -5.0:
        findings.append(f"Thermal/hydraulic efficiency is degraded by {abs(efficiency_deviation_pct):.1f}% below baseline curve.")
        recommendations.append("Inspect impeller wear-ring clearances and check for internal recirculation or cavitation pitting.")

    if head_deviation_m < -2.0:
        findings.append(f"Delivered head is {abs(head_deviation_m):.2f} m lower than design point at {flow_rate_m3s:.4f} m³/s.")
        recommendations.append("Verify suction strainer is clear and confirm NPSH margin.")

    # Excess energy check
    if excess_power_kw > 1.5:
        findings.append(f"Excess power draw of {excess_power_kw:.2f} kW above theoretical requirement.")
        recommendations.append(f"Degraded operation incurs approx. ${annual_cost_penalty_usd:,.0f}/year in wasted electrical power.")

    # Operating range check
    bep_offset_pct = ((flow_rate_m3s - Q_BEP) / Q_BEP) * 100.0
    if abs(bep_offset_pct) > 30.0:
        findings.append(f"Operating at {flow_rate_m3s:.4f} m³/s ({bep_offset_pct:+.1f}% from BEP of {Q_BEP} m³/s). Off-design operation accelerates wear.")

    if not findings:
        findings.append("All mechanical and hydraulic parameters are operating within baseline tolerances.")
        recommendations.append("Maintain routine predictive maintenance intervals.")

    return {
        "ml_prediction": ml_prediction,
        "abnormal_probability": prob_abnormal,
        "vibration_zone": vibration_zone,
        "vibration_severity": vibration_severity,
        "head_deviation_m": head_deviation_m,
        "efficiency_deviation_pct": efficiency_deviation_pct,
        "excess_power_kw": excess_power_kw,
        "annual_cost_penalty_usd": annual_cost_penalty_usd,
        "findings": findings,
        "recommendations": recommendations
    }


# ---------------------------------------------------------------------------
# SCRIPT VERIFICATION (TEST CASES)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 68)
    print("PUMP EQUIPMENT INTELLIGENCE SYSTEM — TEST DIAGNOSTICS")
    print("=" * 68)

    # Test Case 1: Healthy pump operating near BEP
    print("\n--- TEST CASE 1: HEALTHY PUMP AT DESIGN FLOW ---")
    diag_1 = diagnose_pump_point(
        flow_rate_m3s=0.0270,
        rpm=1500.0,
        head_m=50.3,
        efficiency=0.77,
        input_power_kw=17.2,
        vibration_mm_s=2.1,
        operating_hours=3200.0
    )
    print(f"ML Status:             {diag_1['ml_prediction']} (Degradation Risk: {diag_1['abnormal_probability']*100:.1f}%)")
    print(f"ISO Vibration Status:  {diag_1['vibration_zone']}")
    print(f"Efficiency Deviation:  {diag_1['efficiency_deviation_pct']:+.1f}%")
    print("Findings:")
    for f in diag_1["findings"]:
        print(f"  * {f}")
    print("Recommendations:")
    for r in diag_1["recommendations"]:
        print(f"  -> {r}")

    # Test Case 2: Worn pump with severe vibration & high power penalty
    print("\n--- TEST CASE 2: DEGRADED PUMP (COMBINED FAULT) ---")
    diag_2 = diagnose_pump_point(
        flow_rate_m3s=0.0280,
        rpm=1498.0,
        head_m=46.5,
        efficiency=0.58,
        input_power_kw=22.5,
        vibration_mm_s=5.8,
        operating_hours=14500.0
    )
    print(f"ML Status:             {diag_2['ml_prediction']} (Degradation Risk: {diag_2['abnormal_probability']*100:.1f}%)")
    print(f"ISO Vibration Status:  {diag_2['vibration_zone']}")
    print(f"Efficiency Deviation:  {diag_2['efficiency_deviation_pct']:+.1f}%")
    print(f"Wasted Power Penalty:  {diag_2['excess_power_kw']:.2f} kW (${diag_2['annual_cost_penalty_usd']:,.0f}/year)")
    print("Findings:")
    for f in diag_2["findings"]:
        print(f"  * {f}")
    print("Recommendations:")
    for r in diag_2["recommendations"]:
        print(f"  -> {r}")
    print("=" * 68)