"""
AI Energy & Equipment Intelligence Suite
Module: Heat Exchanger Synthetic Telemetry Generator
Physics: Counter-current Shell & Tube, LMTD, TEMA Fouling (Rf), Hydraulic Delta-P
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_heat_exchanger_telemetry(
    n_samples_per_class: int = 1200,
    random_state: int = 42
) -> pd.DataFrame:
    """
    Generates synthetic operational telemetry across 5 operating classes:
      0: Normal / Clean Operation
      1: Tube-Side Fouling (mineral scaling/coking: Rf_tube high, dP_tube up, U down)
      2: Shell-Side Fouling (sedimentation/waxing: Rf_shell high, dP_shell up, U down)
      3: Severe Dual Fouling (critical maintenance needed: massive U drop, both dP spikes)
      4: Tube-to-Shell Leak / Bypass (thermal short-circuit, abnormal mixing signatures)
    """
    np.random.seed(random_state)
    
    # Exchanger Physical Parameters
    area = 125.0  # Heat transfer surface area, m^2
    cp_hot = 2.45  # kJ/(kg*K) - e.g., light hydrocarbon / gas oil
    cp_cold = 4.184  # kJ/(kg*K) - cooling water
    u_clean_base = 680.0  # Clean overall heat transfer coeff, W/(m^2*K)
    
    classes = [
        "Normal Clean",
        "Tube-Side Fouled",
        "Shell-Side Fouled",
        "Severe Dual Fouling",
        "Tube Bypass / Leak"
    ]
    
    records = []
    base_timestamp = datetime(2026, 1, 1, 0, 0, 0)
    step_minutes = 15

    for label_idx, label_name in enumerate(classes):
        for i in range(n_samples_per_class):
            timestamp = base_timestamp + timedelta(minutes=step_minutes * (label_idx * n_samples_per_class + i))
            
            # Base Operating Conditions with ambient/process drift
            # Hot fluid on tube side, cooling water on shell side
            m_dot_hot = np.random.normal(18.5, 1.2)  # kg/s
            m_dot_cold = np.random.normal(32.0, 1.8)  # kg/s
            
            t_hot_in = np.random.normal(145.0, 2.5)   # °C
            t_cold_in = np.random.normal(28.0, 1.5)   # °C
            
            # Nominal Pressure baselines (bar)
            p_hot_in = np.random.normal(12.0, 0.2)
            p_cold_in = np.random.normal(4.5, 0.1)

            # Fault Injection & Thermal Degradation Multipliers
            if label_idx == 0:  # Normal Clean
                rf_tube = np.random.uniform(0.00002, 0.00010)
                rf_shell = np.random.uniform(0.00002, 0.00008)
                dp_tube_mult = 1.0 + np.random.normal(0.0, 0.02)
                dp_shell_mult = 1.0 + np.random.normal(0.0, 0.02)
                bypass_fraction = 0.0
                
            elif label_idx == 1:  # Tube-Side Fouled
                rf_tube = np.random.uniform(0.00045, 0.00085)
                rf_shell = np.random.uniform(0.00005, 0.00012)
                dp_tube_mult = np.random.uniform(1.35, 1.80)
                dp_shell_mult = np.random.uniform(1.02, 1.08)
                bypass_fraction = 0.0

            elif label_idx == 2:  # Shell-Side Fouled
                rf_tube = np.random.uniform(0.00005, 0.00012)
                rf_shell = np.random.uniform(0.00042, 0.00078)
                dp_tube_mult = np.random.uniform(1.01, 1.07)
                dp_shell_mult = np.random.uniform(1.40, 1.95)
                bypass_fraction = 0.0

            elif label_idx == 3:  # Severe Dual Fouling
                rf_tube = np.random.uniform(0.00075, 0.00130)
                rf_shell = np.random.uniform(0.00065, 0.00110)
                dp_tube_mult = np.random.uniform(1.85, 2.40)
                dp_shell_mult = np.random.uniform(1.75, 2.25)
                bypass_fraction = 0.0

            elif label_idx == 4:  # Tube Bypass / Leakage
                rf_tube = np.random.uniform(0.00005, 0.00015)
                rf_shell = np.random.uniform(0.00005, 0.00015)
                dp_tube_mult = np.random.uniform(0.70, 0.88)   # Flow bypass reduces main dP
                dp_shell_mult = np.random.uniform(1.05, 1.20)
                bypass_fraction = np.random.uniform(0.08, 0.18)

            # Combined Fouling Factor and Effective Heat Transfer Coeff
            rf_total = rf_tube + rf_shell
            # U_actual = 1 / (1/U_clean + Rf_total)
            u_actual = 1.0 / ((1.0 / u_clean_base) + rf_total) * np.random.normal(1.0, 0.015)

            # Iterative or E-NTU thermal convergence for outlet temperatures
            # C_min, C_max calculations
            c_h = (m_dot_hot * (1.0 - bypass_fraction)) * (cp_hot * 1000.0)  # W/K
            c_c = m_dot_cold * (cp_cold * 1000.0)  # W/K
            c_min = min(c_h, c_c)
            c_max = max(c_h, c_c)
            c_ratio = c_min / c_max

            ntu = (u_actual * area) / c_min
            
            # Counter-flow effectiveness
            if c_ratio < 0.999:
                effectiveness = (1.0 - np.exp(-ntu * (1.0 - c_ratio))) / (
                    1.0 - c_ratio * np.exp(-ntu * (1.0 - c_ratio))
                )
            else:
                effectiveness = ntu / (1.0 + ntu)

            q_actual_watts = effectiveness * c_min * (t_hot_in - t_cold_in)
            q_actual_kw = q_actual_watts / 1000.0

            # Calculate outlet temperatures
            t_hot_out = t_hot_in - (q_actual_watts / (m_dot_hot * cp_hot * 1000.0))
            t_cold_out = t_cold_in + (q_actual_watts / (m_dot_cold * cp_cold * 1000.0))

            # Counter-current LMTD check
            dt1 = t_hot_in - t_cold_out
            dt2 = t_hot_out - t_cold_in
            dt1 = max(dt1, 0.1)
            dt2 = max(dt2, 0.1)
            
            if abs(dt1 - dt2) < 1e-4:
                lmtd = dt1
            else:
                lmtd = (dt1 - dt2) / np.log(dt1 / dt2)

            # Baseline clean hydraulic pressure drops (bar)
            # Darcy-Weisbach: dP proportional to m_dot^1.85
            dp_hot_clean = 0.85 * ((m_dot_hot / 18.5) ** 1.85)
            dp_cold_clean = 0.55 * ((m_dot_cold / 32.0) ** 1.85)

            dp_hot_actual = dp_hot_clean * dp_tube_mult + np.random.normal(0, 0.01)
            dp_cold_actual = dp_cold_clean * dp_shell_mult + np.random.normal(0, 0.01)

            p_hot_out = p_hot_in - dp_hot_actual
            p_cold_out = p_cold_in - dp_cold_actual

            # Thermal Effectiveness (actual Q / max theoretical Q)
            thermal_effectiveness = q_actual_watts / (c_min * (t_hot_in - t_cold_in))

            records.append({
                "timestamp": timestamp,
                "hot_mass_flow_kg_s": round(m_dot_hot, 3),
                "cold_mass_flow_kg_s": round(m_dot_cold, 3),
                "hot_temp_in_c": round(t_hot_in, 2),
                "hot_temp_out_c": round(t_hot_out, 2),
                "cold_temp_in_c": round(t_cold_in, 2),
                "cold_temp_out_c": round(t_cold_out, 2),
                "hot_press_in_bar": round(p_hot_in, 3),
                "hot_press_out_bar": round(p_hot_out, 3),
                "cold_press_in_bar": round(p_cold_in, 3),
                "cold_press_out_bar": round(p_cold_out, 3),
                "hot_dp_bar": round(dp_hot_actual, 4),
                "cold_dp_bar": round(dp_cold_actual, 4),
                "heat_duty_kw": round(q_actual_kw, 2),
                "lmtd_c": round(lmtd, 2),
                "u_actual_w_m2k": round(u_actual, 2),
                "fouling_factor_rf_m2k_w": round(rf_total, 6),
                "thermal_effectiveness": round(thermal_effectiveness, 4),
                "fault_class": label_idx,
                "fault_description": label_name
            })

    df = pd.DataFrame(records)
    return df

if __name__ == "__main__":
    df_hx = generate_heat_exchanger_telemetry()
    output_path = "data/heat_exchanger_telemetry.csv"
    df_hx.to_csv(output_path, index=False)
    print(f"Generated {len(df_hx)} records across {df_hx['fault_description'].nunique()} states.")
    print(f"Dataset saved to: {output_path}")