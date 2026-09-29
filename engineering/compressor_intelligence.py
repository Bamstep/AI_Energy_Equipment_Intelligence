"""
Centrifugal Compressor Diagnostic Intelligence & Energy Reasoner Module
Evaluates mechanical vibration severity, aerodynamic surge proximity,
thermodynamic efficiency penalties, and generates actionable maintenance advisories.
"""

def evaluate_vibration_iso10816(vibration_rms_mm_s):
    """
    Evaluates vibration severity against ISO 10816-3 for large industrial rotating machines.
    """
    if vibration_rms_mm_s < 2.8:
        return "Zone A/B: Good / Acceptable", "Normal"
    elif vibration_rms_mm_s <= 4.5:
        return "Zone C: Unsatisfactory (Trending Required)", "Warning"
    else:
        return "Zone D: Critical / Unacceptable (Immediate Action Required)", "Critical"


def evaluate_surge_proximity(surge_margin_pct):
    """
    Evaluates aerodynamic safety margin away from compressor surge line.
    """
    if surge_margin_pct < 10.0:
        return "CRITICAL: Imminent Surge Risk (< 10% Margin)", "Critical"
    elif surge_margin_pct <= 15.0:
        return "WARNING: Approaching Surge Limit (10% - 15% Margin)", "Warning"
    else:
        return "NORMAL: Safe Aerodynamic Margin (> 15%)", "Normal"


def diagnose_compressor_condition(
    mass_flow_kg_s,
    pressure_ratio,
    polytropic_eff,
    discharge_t_c,
    vibration_rms_mm_s,
    surge_margin_pct,
    excess_power_kw,
    cost_per_kwh=0.12,
    operating_hours_per_year=8000
):
    """
    Conducts root-cause diagnostics across aerodynamic, thermodynamic,
    and mechanical domains and computes financial/energy degradation costs.
    """
    indicators = []
    actions = []

    # 1. Aerodynamic Surge Assessment
    surge_status, surge_severity = evaluate_surge_proximity(surge_margin_pct)
    if surge_severity == "Critical":
        indicators.append(
            f"Aerodynamic Surge Danger: Surge margin is critically low at {surge_margin_pct:.1f}%."
        )
        actions.append(
            "Immediately modulate anti-surge recycle valve (ASV) to increase suction flow and prevent flow reversal."
        )
    elif surge_severity == "Warning":
        indicators.append(
            f"Surge Buffer Warning: Operating within restricted margin zone ({surge_margin_pct:.1f}%)."
        )
        actions.append(
            "Monitor suction pressure throttle and check variable inlet guide vanes (IGVs) positioning."
        )

    # 2. Thermodynamic & Impeller Fouling Assessment
    design_eff = 0.82
    eff_deviation_pct = ((polytropic_eff - design_eff) / design_eff) * 100.0

    if eff_deviation_pct < -6.0:
        indicators.append(
            f"Thermodynamic Degradation: Polytropic efficiency dropped to {polytropic_eff*100:.1f}% "
            f"({eff_deviation_pct:.1f}% vs. design baseline), driving discharge temp to {discharge_t_c:.1f} °C."
        )
        actions.append(
            "Schedule online/offline wash cycle to remove polymer/particulate fouling from impellers and diffusers."
        )

    # 3. Mechanical Vibration Assessment
    vib_desc, vib_severity = evaluate_vibration_iso10816(vibration_rms_mm_s)
    if vib_severity == "Critical":
        indicators.append(
            f"Severe Mechanical Vibration: Reading at {vibration_rms_mm_s:.2f} mm/s RMS (ISO Zone D)."
        )
        actions.append(
            "Perform immediate FFT vibration spectral analysis to isolate 1X unbalance, 2X misalignment, or sub-synchronous surge buffeting."
        )
    elif vib_severity == "Warning":
        indicators.append(
            f"Elevated Mechanical Vibration: Reading at {vibration_rms_mm_s:.2f} mm/s RMS (ISO Zone C)."
        )
        actions.append(
            "Inspect hydrodynamic journal bearing lube oil temperature, viscosity, and seal gas supply pressure."
        )

    # If all parameters healthy
    if not indicators:
        indicators.append("All mechanical, aerodynamic, and thermodynamic metrics are within design envelope.")
        actions.append("Maintain routine predictive monitoring and oil analysis intervals.")

    # 4. Energy Penalty & Financial Cost Calculation
    annual_cost_penalty = excess_power_kw * cost_per_kwh * operating_hours_per_year

    return {
        "surge_status": surge_status,
        "surge_severity": surge_severity,
        "vibration_status": vib_desc,
        "vibration_severity": vib_severity,
        "eff_deviation_pct": eff_deviation_pct,
        "excess_power_kw": excess_power_kw,
        "annual_cost_penalty_usd": annual_cost_penalty,
        "indicators": indicators,
        "actions": actions
    }


if __name__ == "__main__":
    print("=" * 65)
    print("COMPRESSOR DIAGNOSTIC REASONER: TEST RUN")
    print("=" * 65)

    # Simulate an abnormal condition: low surge margin + efficiency loss
    test_diag = diagnose_compressor_condition(
        mass_flow_kg_s=6.8,
        pressure_ratio=1.85,
        polytropic_eff=0.71,
        discharge_t_c=98.5,
        vibration_rms_mm_s=5.2,
        surge_margin_pct=4.4,
        excess_power_kw=142.5
    )

    print(f"Surge Assessment:       {test_diag['surge_status']}")
    print(f"Vibration Assessment:   {test_diag['vibration_status']}")
    print(f"Efficiency Deviation:   {test_diag['eff_deviation_pct']:.1f}%")
    print(f"Wasted Energy Penalty:  {test_diag['excess_power_kw']:.1f} kW")
    print(f"Annualized Cost Impact: ${test_diag['annual_cost_penalty_usd']:,.2f} / year\n")
    print("Physical Indicators:")
    for ind in test_diag["indicators"]:
        print(f"  • {ind}")
    print("\nRecommended Interventions:")
    for act in test_diag["actions"]:
        print(f"  • {act}")
    print("=" * 65)