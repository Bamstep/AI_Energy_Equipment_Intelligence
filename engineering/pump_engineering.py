"""
Fluid Mechanics and Centrifugal Pump Governing Engineering Equations
"""
import numpy as np

# Reference Baseline Constants (Standard Water at 20°C)
RHO_WATER = 1000.0       # kg/m^3
GRAVITY = 9.81           # m/s^2
N_REF_RPM = 1500.0       # Nominal synchronous reference speed
N_DESIGN = 1500.0        # Design speed alias
H0_SHUTOFF = 62.0        # Shut-off head at zero flow (meters)
K_CURVE = 16000.0        # Empirical resistance/droop coefficient

# Best Efficiency Point (BEP)
BEP_FLOW_M3_S = 0.027    # Best Efficiency Point flow rate (~97.2 m^3/h)
Q_BEP = 0.027            # Alias for BEP flow rate
BEP_EFFICIENCY = 0.78    # Nominal design hydraulic efficiency at BEP
ETA_BEP = 0.78           # Alias for BEP efficiency


def theoretical_pump_head(flow_rate_m3_s, rpm=N_REF_RPM):
    """
    Computes theoretical dynamic delivered head H (meters) using quadratic
    droop characteristic coupled with Affinity Law speed scaling.
    H = (H0 - k * Q^2) * (N / N_ref)^2
    """
    speed_ratio = rpm / N_REF_RPM
    base_head = H0_SHUTOFF - K_CURVE * (flow_rate_m3_s ** 2)
    scaled_head = base_head * (speed_ratio ** 2)
    return float(np.maximum(scaled_head, 5.0))


def theoretical_head(flow_rate_m3_s, rpm=N_REF_RPM):
    """Alias for theoretical_pump_head."""
    return theoretical_pump_head(flow_rate_m3_s, rpm)


def pump_characteristic_head(flow_rate_m3_s, rpm=N_REF_RPM):
    """Alias for theoretical_pump_head."""
    return theoretical_pump_head(flow_rate_m3_s, rpm)


def theoretical_efficiency(flow_rate_m3_s):
    """
    Parabolic theoretical hydraulic efficiency curve peaking at BEP.
    eta = eta_bep - C * (Q - Q_bep)^2
    """
    c_eff = 850.0
    eff = BEP_EFFICIENCY - c_eff * ((flow_rate_m3_s - BEP_FLOW_M3_S) ** 2)
    return float(np.clip(eff, 0.30, BEP_EFFICIENCY))


def pump_efficiency_curve(flow_rate_m3_s):
    """Alias for theoretical_efficiency."""
    return theoretical_efficiency(flow_rate_m3_s)


def calculate_hydraulic_power_kw(flow_rate_m3_s, head_m, rho=RHO_WATER, g=GRAVITY):
    """
    Hydraulic power transferred to fluid in kilowatts:
    P_hyd = (rho * g * Q * H) / 1000
    """
    return (rho * g * flow_rate_m3_s * head_m) / 1000.0


def calculate_input_power_kw(hydraulic_power_kw, efficiency):
    """
    Shaft input power required from electric motor:
    P_input = P_hyd / efficiency
    """
    if efficiency <= 0:
        raise ValueError("Hydraulic efficiency must be positive.")
    return hydraulic_power_kw / efficiency


def calculate_efficiency_from_power(flow_rate_m3_s, head_m, input_power_kw, rho=RHO_WATER, g=GRAVITY):
    """
    Computes hydraulic efficiency given fluid telemetry and measured shaft power:
    eta = P_hyd / P_input
    """
    if input_power_kw <= 0:
        return 0.0
    p_hyd = calculate_hydraulic_power_kw(flow_rate_m3_s, head_m, rho, g)
    return p_hyd / input_power_kw


if __name__ == "__main__":
    print(f"Q_BEP: {Q_BEP}, ETA_BEP: {ETA_BEP}")