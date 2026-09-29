import numpy as np
import pandas as pd
import os
import sys

# Ensure root directory is in sys.path to import engineering modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from engineering.compressor_engineering import (
    R_SPECIFIC, GAMMA, T1_SUCTION_K, P1_SUCTION_BAR, Z_AVG,
    N_REF_RPM, ETA_P_DESIGN, M_DOT_DESIGN, SURGE_FLOW_KG_S,
    calculate_discharge_temperature, calculate_polytropic_head_j_kg,
    calculate_gas_power_kw, calculate_surge_margin_pct, theoretical_pressure_ratio
)

def generate_compressor_dataset(num_samples=1200, random_seed=42):
    """
    Generates a physics-informed synthetic telemetry dataset for a single-stage
    centrifugal natural gas compressor under normal and degraded operational regimes.
    """
    np.random.seed(random_seed)
    records = []

    # Operating Envelope
    # Mass flow: 6.0 kg/s (near surge) to 15.0 kg/s (choke/high throughput)
    # Rotor speed: 9000 to 10000 RPM (around design 9500 RPM)

    for i in range(num_samples):
        # 1. Operational Setpoints
        speed_rpm = np.random.uniform(9200.0, 9800.0)
        suction_p_bar = np.random.normal(P1_SUCTION_BAR, 0.25)
        suction_t_c = np.random.normal(20.0, 1.5)
        suction_t_k = suction_t_c + 273.15

        # 2. Determine Operational Health State
        # 0: Normal, 1: Surge Risk, 2: Impeller Fouling, 3: Bearing/Vibration Fault, 4: Combined
        state_draw = np.random.rand()
        if state_draw < 0.70:
            health_label = 0  # Normal (~70%)
            fault_mode = "Normal"
        elif state_draw < 0.78:
            health_label = 1  # Surge Proximity (~8%)
            fault_mode = "Surge_Risk"
        elif state_draw < 0.88:
            health_label = 2  # Impeller Fouling (~10%)
            fault_mode = "Impeller_Fouling"
        elif state_draw < 0.96:
            health_label = 3  # Mechanical Unbalance (~8%)
            fault_mode = "Mechanical_Vibration"
        else:
            health_label = 4  # Combined Deterioration (~4%)
            fault_mode = "Combined_Fault"

        # 3. Inject Operating Conditions based on State
        if fault_mode == "Surge_Risk":
            # Flow forced dangerously low near the surge limit
            mass_flow_kg_s = np.random.uniform(6.0, 7.3)
        else:
            mass_flow_kg_s = np.random.uniform(7.8, 14.8)

        # Baseline theoretical pressure ratio for current flow & speed
        base_rp = theoretical_pressure_ratio(mass_flow_kg_s, speed_rpm)

        # Inject Fault Degradation Factors
        if fault_mode == "Normal":
            eta_p = np.random.uniform(0.80, 0.84)
            rp = base_rp + np.random.normal(0.0, 0.01)
            vibration_rms = np.random.uniform(1.0, 2.4)
        elif fault_mode == "Surge_Risk":
            eta_p = np.random.uniform(0.74, 0.79)
            rp = base_rp * np.random.uniform(0.95, 0.98)
            # Pressure oscillations and flow instability cause vibration spikes
            vibration_rms = np.random.uniform(3.5, 6.0)
        elif fault_mode == "Impeller_Fouling":
            # Aerodynamic degradation: lower efficiency, lower pressure ratio
            eta_p = np.random.uniform(0.68, 0.75)
            rp = base_rp * np.random.uniform(0.90, 0.95)
            vibration_rms = np.random.uniform(1.8, 3.2)
        elif fault_mode == "Mechanical_Vibration":
            # Pure mechanical unbalance / bearing flaw: thermodynamics nominal
            eta_p = np.random.uniform(0.80, 0.83)
            rp = base_rp + np.random.normal(0.0, 0.01)
            vibration_rms = np.random.uniform(4.8, 8.5)
        else: # Combined_Fault
            eta_p = np.random.uniform(0.65, 0.73)
            rp = base_rp * np.random.uniform(0.88, 0.94)
            vibration_rms = np.random.uniform(5.0, 9.0)

        # 4. Compute Derived Thermodynamic Properties
        discharge_p_bar = suction_p_bar * rp
        discharge_t_k = calculate_discharge_temperature(suction_t_k, rp, eta_p, GAMMA)
        discharge_t_c = discharge_t_k - 273.15
        polytropic_head_j_kg = calculate_polytropic_head_j_kg(suction_t_k, rp, eta_p, R_SPECIFIC, Z_AVG, GAMMA)
        gas_power_kw = calculate_gas_power_kw(mass_flow_kg_s, polytropic_head_j_kg, eta_p)
        surge_margin_pct = calculate_surge_margin_pct(mass_flow_kg_s, SURGE_FLOW_KG_S)

        # Baseline healthy power for energy penalty quantification
        healthy_head = calculate_polytropic_head_j_kg(suction_t_k, base_rp, ETA_P_DESIGN, R_SPECIFIC, Z_AVG, GAMMA)
        healthy_power_kw = calculate_gas_power_kw(mass_flow_kg_s, healthy_head, ETA_P_DESIGN)
        excess_power_kw = max(0.0, gas_power_kw - healthy_power_kw)

        # Binary label for initial classification (0: Normal, 1: Abnormal/Fault)
        binary_condition = 0 if health_label == 0 else 1

        records.append({
            "mass_flow_kg_s": round(mass_flow_kg_s, 3),
            "speed_rpm": round(speed_rpm, 1),
            "suction_p_bar": round(suction_p_bar, 2),
            "discharge_p_bar": round(discharge_p_bar, 2),
            "pressure_ratio": round(rp, 3),
            "suction_t_c": round(suction_t_c, 2),
            "discharge_t_c": round(discharge_t_c, 2),
            "polytropic_efficiency": round(eta_p, 4),
            "polytropic_head_kj_kg": round(polytropic_head_j_kg / 1000.0, 2),
            "gas_power_kw": round(gas_power_kw, 2),
            "excess_power_kw": round(excess_power_kw, 2),
            "surge_margin_pct": round(surge_margin_pct, 2),
            "vibration_rms_mm_s": round(vibration_rms, 2),
            "fault_mode": fault_mode,
            "condition_label": binary_condition
        })

    df = pd.DataFrame(records)
    return df

if __name__ == "__main__":
    output_path = os.path.join(os.path.dirname(__file__), "compressor_dataset.csv")
    df = generate_compressor_dataset(num_samples=1200)
    df.to_csv(output_path, index=False)
    
    print("=" * 65)
    print("COMPRESSOR DATASET GENERATION COMPLETE")
    print("=" * 65)
    print(f"File Saved: {output_path}")
    print(f"Total Records Generated: {len(df)}")
    print("\nClass Breakdown (condition_label):")
    print(df["condition_label"].value_counts(normalize=True).mul(100).round(1).astype(str) + " %")
    print("\nFault Mode Distribution:")
    print(df["fault_mode"].value_counts())
    print("=" * 65)