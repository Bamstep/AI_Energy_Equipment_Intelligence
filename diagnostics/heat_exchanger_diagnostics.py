"""
AI Energy & Equipment Intelligence Suite
Module: Heat Exchanger Diagnostic Reasoning Engine
Couples: TEMA Fouling Standards, Hydraulic Pumping Penalties, Financial Leakage
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List

# TEMA fouling thresholds (m^2*K/W)
TEMA_RF_CLEAN_LIMIT = 0.00015
TEMA_RF_ALERT_LIMIT = 0.00035
TEMA_RF_CRITICAL_LIMIT = 0.00075

class HeatExchangerDiagnosticEngine:
    def __init__(self, model_path: str = "models/heat_exchanger_model.joblib"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model bundle not found at {model_path}. Train the model first."
            )
        
        bundle = joblib.load(model_path)
        self.model = bundle["model"]
        self.scaler = bundle["scaler"]
        self.features = bundle["features"]
        self.class_mapping = bundle["class_mapping"]
        self.use_scaled = bundle.get("use_scaled", False)

        # Baseline clean design constants
        self.u_clean_design = 680.0  # W/(m^2*K)
        self.hot_dp_clean_ref = 0.85  # bar at 18.5 kg/s
        self.cold_dp_clean_ref = 0.55  # bar at 32.0 kg/s
        self.electricity_cost_per_kwh = 0.12  # $ / kWh
        self.operating_hours_per_year = 8400  # industrial runtime

    def diagnose_packet(self, telemetry: Dict[str, float]) -> Dict[str, Any]:
        """
        Takes raw telemetry dict, extracts features, performs inference,
        and computes thermo-hydraulic penalties and maintenance advisories.
        """
        # Format input dataframe
        input_df = pd.DataFrame([telemetry])[self.features]

        # ML inference
        if self.use_scaled:
            x_scaled = self.scaler.transform(input_df)
            pred_class = int(self.model.predict(x_scaled)[0])
            pred_proba = self.model.predict_proba(x_scaled)[0]
        else:
            pred_class = int(self.model.predict(input_df)[0])
            pred_proba = self.model.predict_proba(input_df)[0]

        condition_label = self.class_mapping[pred_class]
        confidence = float(np.max(pred_proba)) * 100.0

        # Physical extractions
        u_actual = telemetry["u_actual_w_m2k"]
        rf = telemetry["fouling_factor_rf_m2k_w"]
        hot_dp = telemetry["hot_dp_bar"]
        cold_dp = telemetry["cold_dp_bar"]
        m_dot_hot = telemetry["hot_mass_flow_kg_s"]
        m_dot_cold = telemetry["cold_mass_flow_kg_s"]

        # Expected clean dP at current flow rates
        expected_hot_dp = self.hot_dp_clean_ref * ((m_dot_hot / 18.5) ** 1.85)
        expected_cold_dp = self.cold_dp_clean_ref * ((m_dot_cold / 32.0) ** 1.85)

        excess_hot_dp_bar = max(0.0, hot_dp - expected_hot_dp)
        excess_cold_dp_bar = max(0.0, cold_dp - expected_cold_dp)

        # Excess Hydraulic Pumping Power Penalty (kW)
        # P_excess = (delta_P_excess * 1e5 Pa * Flow_m3_s) / (pump_efficiency * 1000)
        # Using hot oil ~ 820 kg/m^3 and cooling water ~ 995 kg/m^3, eta_pump ~ 0.75
        rho_hot = 820.0
        rho_cold = 995.0
        eta_pump = 0.75

        q_vol_hot = (m_dot_hot / rho_hot)  # m^3/s
        q_vol_cold = (m_dot_cold / rho_cold)  # m^3/s

        pumping_penalty_hot_kw = (excess_hot_dp_bar * 1e5 * q_vol_hot) / (eta_pump * 1000.0)
        pumping_penalty_cold_kw = (excess_cold_dp_bar * 1e5 * q_vol_cold) / (eta_pump * 1000.0)
        total_pumping_penalty_kw = pumping_penalty_hot_kw + pumping_penalty_cold_kw

        # Thermal Degradation Penalty (% loss in overall U)
        u_degradation_pct = max(0.0, ((self.u_clean_design - u_actual) / self.u_clean_design) * 100.0)

        # Annual Financial Energy Leakage ($/year)
        annual_financial_leakage = (
            total_pumping_penalty_kw * self.electricity_cost_per_kwh * self.operating_hours_per_year
        )

        # Health Scoring (0 - 100%)
        # Deduct for fouling factor and excessive pressure drop
        rf_penalty = min(50.0, (rf / TEMA_RF_CRITICAL_LIMIT) * 50.0)
        dp_penalty = min(50.0, ((excess_hot_dp_bar + excess_cold_dp_bar) / 1.5) * 50.0)
        health_index = max(5.0, 100.0 - (rf_penalty + dp_penalty))

        # Root Cause Analysis and Prescriptive Maintenance Plan
        findings: List[str] = []
        recommendations: List[str] = []
        severity = "NORMAL"

        if pred_class == 0:  # Clean
            findings.append("Heat transfer coefficient and hydraulic pressure drops operate within clean design bounds.")
            recommendations.append("Maintain baseline cooling water biocide treatment and routine monitoring.")
        
        elif pred_class == 1:  # Tube-Side Fouled
            severity = "WARNING" if rf < TEMA_RF_CRITICAL_LIMIT else "CRITICAL"
            findings.append(f"Tube-side constriction detected. Excess tube dP: +{excess_hot_dp_bar:.2f} bar.")
            findings.append(f"TEMA fouling resistance ({rf:.6f} m²·K/W) exceeds acceptable operational threshold.")
            recommendations.append("Schedule high-pressure hydro-jetting or chemical descaling of tube bundle inner bore.")
            recommendations.append("Inspect upstream strainers for particulate coking / scale carryover.")

        elif pred_class == 2:  # Shell-Side Fouled
            severity = "WARNING" if rf < TEMA_RF_CRITICAL_LIMIT else "CRITICAL"
            findings.append(f"Shell-side bundle silt/algae accumulation. Excess shell dP: +{excess_cold_dp_bar:.2f} bar.")
            findings.append(f"Overall heat transfer coefficient suppressed by {u_degradation_pct:.1f}%.")
            recommendations.append("Perform shell-side back-flushing or chemical circulation cleaning.")
            recommendations.append("Audit cooling tower basin water chemistry and increase biocide dosing.")

        elif pred_class == 3:  # Severe Dual Fouling
            severity = "CRITICAL"
            findings.append(f"Severe dual-side thermal constriction. Overall U reduced by {u_degradation_pct:.1f}%.")
            findings.append(f"Total hydraulic pumping penalty adds {total_pumping_penalty_kw:.2f} kW continuous power draw.")
            recommendations.append("Immediate turnaround required: pull tube bundle for ultrasonic bath immersion and mechanical re-tubing assessment.")
            recommendations.append("Bypass unit if standby exchanger bank is available to prevent upstream thermal runaways.")

        elif pred_class == 4:  # Tube Bypass / Leak
            severity = "CRITICAL"
            findings.append("Abnormal pressure drop dropoff on tube side indicates internal tube-to-shell leak or baffle pass bypass.")
            recommendations.append("Execute acoustic leak detection / tracer gas helium leak test.")
            recommendations.append("Perform tube bundle eddy current testing (ECT) to isolate ruptured tubes for mechanical plugging.")

        return {
            "condition": condition_label,
            "severity": severity,
            "confidence_pct": round(confidence, 1),
            "health_index": round(health_index, 1),
            "u_actual_w_m2k": round(u_actual, 1),
            "u_degradation_pct": round(u_degradation_pct, 1),
            "fouling_factor_rf": round(rf, 6),
            "excess_hot_dp_bar": round(excess_hot_dp_bar, 3),
            "excess_cold_dp_bar": round(excess_cold_dp_bar, 3),
            "total_pumping_penalty_kw": round(total_pumping_penalty_kw, 2),
            "annual_financial_loss_usd": round(annual_financial_leakage, 2),
            "findings": findings,
            "recommendations": recommendations
        }

if __name__ == "__main__":
    engine = HeatExchangerDiagnosticEngine()
    
    # Test sample: High tube-side fouling
    sample_packet = {
        "hot_mass_flow_kg_s": 18.5,
        "cold_mass_flow_kg_s": 32.0,
        "hot_temp_in_c": 145.0,
        "hot_temp_out_c": 92.5,
        "cold_temp_in_c": 28.0,
        "cold_temp_out_c": 45.2,
        "hot_dp_bar": 1.48,        # clean is ~0.85
        "cold_dp_bar": 0.58,       # clean is ~0.55
        "heat_duty_kw": 2380.0,
        "lmtd_c": 56.4,
        "u_actual_w_m2k": 337.5,   # clean is ~680
        "fouling_factor_rf_m2k_w": 0.00062, # well above 0.00035 limit
        "thermal_effectiveness": 0.58
    }
    
    diagnosis = engine.diagnose_packet(sample_packet)
    print("\n--- TEST RUN DIAGNOSTIC RESULT ---")
    for k, v in diagnosis.items():
        print(f"{k}: {v}")