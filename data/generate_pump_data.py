import os
import sys
import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engineering.pump_engineering import (
    RHO_WATER,
    G,
    N_REF,
    calculate_pressure_from_head,
    calculate_hydraulic_power_kw,
    calculate_input_power_kw,
    theoretical_pump_head,
    theoretical_efficiency
)

RANDOM_SEED = 42
N_SAMPLES = 1000

def generate_pump_dataset(n_samples=N_SAMPLES, random_state=RANDOM_SEED):
    np.random.seed(random_state)

    # 1. Operating points
    flow_rate = np.random.uniform(0.010, 0.040, n_samples)
    rpm = np.random.normal(N_REF, 8.0, n_samples)
    operating_hours = np.random.uniform(100.0, 20000.0, n_samples)

    # 2. Failure assignment (~25% Abnormal)
    prob_failure = 0.08 + 0.32 * (operating_hours / 20000.0)
    is_abnormal = np.random.rand(n_samples) < prob_failure
    condition = np.where(is_abnormal, "Abnormal", "Normal")

    # 3. Base Curves
    head_ideal = np.array([theoretical_pump_head(q, n) for q, n in zip(flow_rate, rpm)])
    head = head_ideal + np.random.normal(0, 0.4, n_samples)

    eta_ideal = np.array([theoretical_efficiency(q) for q in flow_rate])
    efficiency = eta_ideal + np.random.normal(0, 0.012, n_samples)

    # Baseline Vibration with realistic spread (1.5 to 3.8 mm/s)
    vibration = np.random.normal(2.4, 0.45, n_samples)

    # 4. Realistic Fault Modes (Hydraulic vs Mechanical vs Combined)
    for i in range(n_samples):
        if condition[i] == "Abnormal":
            fault_type = np.random.choice(["hydraulic_wear", "mechanical_unbalance", "combined"])
            
            if fault_type == "hydraulic_wear":
                # Severe efficiency drop, mild vibration change
                efficiency[i] -= np.random.uniform(0.10, 0.20)
                head[i] -= np.random.uniform(1.5, 4.0)
                vibration[i] += np.random.uniform(0.4, 1.2)  # slight roughness only
                
            elif fault_type == "mechanical_unbalance":
                # Bearing/alignment degradation: elevated vibration, efficiency unchanged
                vibration[i] += np.random.uniform(2.0, 4.5)
                
            elif fault_type == "combined":
                # Both hydraulic wear and mechanical degradation
                efficiency[i] -= np.random.uniform(0.08, 0.16)
                head[i] -= np.random.uniform(1.0, 3.0)
                vibration[i] += np.random.uniform(1.8, 4.0)

    # Ensure physical limits
    efficiency = np.clip(efficiency, 0.25, 0.82)
    vibration = np.clip(vibration, 1.2, 10.0)

    # 5. Dependent physical quantities
    pressure_diff = calculate_pressure_from_head(head) + np.random.normal(0, 2500, n_samples)
    hydraulic_power = calculate_hydraulic_power_kw(flow_rate, head)
    input_power = np.array([
        calculate_input_power_kw(ph, eta) for ph, eta in zip(hydraulic_power, efficiency)
    ])

    # 6. DataFrame
    df = pd.DataFrame({
        "flow_rate_m3s": np.round(flow_rate, 4),
        "rpm": np.round(rpm, 1),
        "head_m": np.round(head, 2),
        "pressure_difference_pa": np.round(pressure_diff, 0),
        "efficiency": np.round(efficiency, 4),
        "hydraulic_power_kw": np.round(hydraulic_power, 2),
        "input_power_kw": np.round(input_power, 2),
        "vibration_mm_s": np.round(vibration, 2),
        "operating_hours": np.round(operating_hours, 1),
        "condition": condition
    })
    return df

if __name__ == "__main__":
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "pump_dataset.csv")

    df_pump = generate_pump_dataset()
    df_pump.to_csv(output_path, index=False)

    print("=" * 65)
    print("REALISTIC MULTI-FAULT DATASET GENERATION COMPLETE")
    print("=" * 65)
    print(f"Total records: {len(df_pump)}")
    print(df_pump["condition"].value_counts(normalize=True).mul(100).round(1).astype(str) + "%")
    print("\nMean Values by Condition:")
    print(df_pump.groupby("condition")[["efficiency", "input_power_kw", "vibration_mm_s", "operating_hours"]].mean().round(2))
    print("=" * 65)