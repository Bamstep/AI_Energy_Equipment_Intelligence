import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# CONSTANTS & BASELINE ASSUMPTIONS
# ---------------------------------------------------------------------------
RHO_WATER = 1000.0   # kg/m3 (Clean industrial water density at ~20 deg C)
G = 9.81             # m/s2 (Standard gravitational acceleration)

# Illustrative pump parameters (Synthetic baseline model)
H0_REF = 62.0        # Shutoff head (m) at reference speed
K_CURVE = 16000.0    # Quadratic resistance coefficient
N_REF = 1500.0       # Reference rotational speed (RPM)

# Best Efficiency Point (BEP) reference values
Q_BEP = 0.027        # Flow rate at BEP (m3/s)
ETA_MAX = 0.78       # Peak hydraulic efficiency (78%)
ETA_WIDTH = 0.018    # Width parameter for parabolic efficiency curve


# ---------------------------------------------------------------------------
# CORE FLUID MECHANICS & PUMP FORMULAS
# ---------------------------------------------------------------------------
def calculate_head_from_pressure(delta_p_pa, rho=RHO_WATER, g=G):
    """
    Converts differential pressure (Delta P) across pump flanges to Head (H).
    Formula: H = Delta P / (rho * g)
    """
    return delta_p_pa / (rho * g)


def calculate_pressure_from_head(head_m, rho=RHO_WATER, g=G):
    """
    Converts pump Head (H) to differential pressure (Delta P).
    Formula: Delta P = rho * g * H
    """
    return rho * g * head_m


def theoretical_pump_head(flow_rate_m3s, rpm=N_REF, h0=H0_REF, k=K_CURVE, n_ref=N_REF):
    """
    Calculates illustrative theoretical head for a given flow rate and RPM.
    Applies simplified pump curve H = H0 - k*Q^2 scaled by affinity law (N / N_ref)^2.
    """
    speed_ratio = rpm / n_ref
    head = (h0 - k * (flow_rate_m3s ** 2)) * (speed_ratio ** 2)
    return max(head, 0.0)


def theoretical_efficiency(flow_rate_m3s, q_bep=Q_BEP, eta_max=ETA_MAX, width=ETA_WIDTH):
    """
    Calculates baseline theoretical efficiency using a smooth parabolic drop
    symmetrical about the Best Efficiency Point (BEP).
    """
    c_factor = (eta_max - 0.45) / (width ** 2)
    eta = eta_max - c_factor * ((flow_rate_m3s - q_bep) ** 2)
    return float(np.clip(eta, 0.25, eta_max))


def calculate_hydraulic_power_kw(flow_rate_m3s, head_m, rho=RHO_WATER, g=G):
    """
    Calculates hydraulic power delivered to the fluid in kilowatts (kW).
    Formula: P_h = (rho * g * Q * H) / 1000
    """
    return (rho * g * flow_rate_m3s * head_m) / 1000.0


def calculate_input_power_kw(hydraulic_power_kw, efficiency):
    """
    Calculates required mechanical shaft power in kilowatts (kW).
    Formula: P_input = P_h / eta
    """
    if efficiency <= 0:
        raise ValueError("Efficiency must be strictly positive.")
    return hydraulic_power_kw / efficiency


# ---------------------------------------------------------------------------
# SCRIPT VERIFICATION & BASELINE PLOTS
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("PUMP ENGINEERING MODULE: VERIFICATION RUN")
    print("=" * 60)

    # 1. Test a single operating point
    test_dp = 490500.0  # Pa (approx 4.9 bar)
    test_head = calculate_head_from_pressure(test_dp)
    test_flow = 0.0278  # m3/s (near BEP)
    test_eta = theoretical_efficiency(test_flow)
    test_p_hyd = calculate_hydraulic_power_kw(test_flow, test_head)
    test_p_in = calculate_input_power_kw(test_p_hyd, test_eta)

    print(f"Sample Differential Pressure: {test_dp:,.0f} Pa")
    print(f"Calculated Head:             {test_head:.2f} m")
    print(f"Operating Flow Rate:         {test_flow:.4f} m3/s")
    print(f"Theoretical Efficiency:      {test_eta * 100:.2f} %")
    print(f"Hydraulic Power (P_hyd):     {test_p_hyd:.2f} kW")
    print(f"Shaft Input Power (P_in):    {test_p_in:.2f} kW")
    print("=" * 60)

    # 2. Generate Characteristic Curve Plots
    q_range = np.linspace(0.010, 0.040, 100)
    h_curve = [theoretical_pump_head(q) for q in q_range]
    eta_curve = [theoretical_efficiency(q) * 100 for q in q_range]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Plot 1: Head vs Flow
    ax1.plot(q_range, h_curve, color="navy", linewidth=2, label="H-Q Curve (1500 RPM)")
    ax1.scatter([test_flow], [test_head], color="red", zorder=5, label="Test Operating Point")
    ax1.set_title("Centrifugal Pump Head vs. Flow Rate", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Flow Rate Q (m3/s)")
    ax1.set_ylabel("Head H (m)")
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend()

    # Plot 2: Efficiency vs Flow
    ax2.plot(q_range, eta_curve, color="darkgreen", linewidth=2, label="Efficiency Curve")
    ax2.axvline(Q_BEP, color="orange", linestyle=":", label=f"BEP ({Q_BEP} m3/s)")
    ax2.set_title("Pump Efficiency vs. Flow Rate", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Flow Rate Q (m3/s)")
    ax2.set_ylabel("Efficiency (%)")
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend()

    plt.tight_layout()
    print("Displaying diagnostic pump curves. Close the plot window to finish execution.")
    plt.show()