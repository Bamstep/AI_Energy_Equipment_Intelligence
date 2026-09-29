"""
Centrifugal Pump Diagnostic Intelligence & Energy Reasoner Module
Evaluates mechanical vibration severity, hydraulic degradation,
power penalties, and generates actionable maintenance advisories.
"""
import numpy as np
from engineering.pump_engineering import (
    theoretical_pump_head,
    theoretical_efficiency,
    calculate_hydraulic_power_kw,
    calculate_input_power_kw,
    Q_BEP,
    ETA_BEP
)

def evaluate_vibration_iso10816(vibration_rms_mm_s):
    """
    Classifies vibration velocity RMS according to ISO 10816-3.
    """
    if vibration_rms_mm_s < 2.8:
        return "Zone A/B: Good / Acceptable", "Normal"
    elif vibration_rms_mm_s <= 4.5:
        return "Zone C: Unsatisfactory (Trending Required)", "Warning"
    else:
        return "Zone D: Critical / Unacceptable (Immediate Action Required)", "Critical"


def diagnose_equipment_condition(
    flow_rate_m3_s,
    delivered_head_m,
    hydraulic_eff,
    input_power_kw,
    vibration_rms_mm_s,
    shaft_speed_rpm=1500.0,
    cost_per_kwh=0.12,
    operating_hours_per_year=8000
):
    """
    Generates root-cause diagnosis, physical degradation metrics, and financial penalties.
    """
    indicators = []
    actions = []

    # 1. Baseline Calculations
    base_head = theoretical_pump_head(flow_rate_m3_s, shaft_speed_rpm)
    base_eff = theoretical_efficiency(flow_rate_m3_s)

    head_deviation_pct = ((delivered_head_m - base_head) / base_head) * 100.0
    eff_deviation_pct = ((hydraulic_eff - base_eff) / base_eff) * 100.0

    p_hyd_kw = calculate_hydraulic_power_kw(flow_rate_m3_s, delivered_head_m)
    expected_power_kw = calculate_input_power_kw(p_hyd_kw, base_eff)
    excess_power_kw = max(0.0, input_power_kw - expected_power_kw)
    annual_cost_penalty = excess_power_kw * cost_per_kwh * operating_hours_per_year

    # 2. Vibration Severity
    vib_desc, vib_zone = evaluate_vibration_iso10816(vibration_rms_mm_s)

    # 3. Diagnostic Reasoning
    if eff_deviation_pct < -8.0:
        indicators.append(
            f"Hydraulic Wear: Efficiency dropped to {hydraulic_eff*100:.1f}% "
            f"({eff_deviation_pct:.1f}% vs baseline), indicating internal recirculation or wear-ring clearance expansion."
        )
        actions.append(
            "Inspect impeller wear rings, volute cutwater, and check internal clearances against OEM limits."
        )

    if head_deviation_pct < -6.0:
        indicators.append(
            f"Head Loss: Delivered head is {delivered_head_m:.1f} m vs expected {base_head:.1f} m "
            f"({head_deviation_pct:.1f}% droop)."
        )
        actions.append("Check suction strainer for clogging and verify impeller vane condition for erosion.")

    if vib_zone == "Critical":
        indicators.append(
            f"Mechanical Alert: Vibration at {vibration_rms_mm_s:.2f} mm/s RMS exceeds ISO Zone D trip threshold."
        )
        actions.append(
            "Perform immediate spectral vibration analysis (FFT) to diagnose 1X unbalance, 2X misalignment, or bearing defect frequencies."
        )
    elif vib_zone == "Warning":
        indicators.append(
            f"Vibration Warning: Vibration at {vibration_rms_mm_s:.2f} mm/s RMS (ISO Zone C)."
        )
        actions.append("Schedule re-lubrication and check dynamic shaft alignment at next maintenance window.")

    if not indicators:
        indicators.append("All hydraulic, thermal, and mechanical parameters are within standard operating tolerance.")
        actions.append("Continue standard condition-based monitoring.")

    return {
        "vibration_desc": vib_desc,
        "vibration_zone": vib_zone,
        "head_deviation_pct": head_deviation_pct,
        "eff_deviation_pct": eff_deviation_pct,
        "excess_power_kw": excess_power_kw,
        "annual_cost_penalty_usd": annual_cost_penalty,
        "indicators": indicators,
        "actions": actions
    }