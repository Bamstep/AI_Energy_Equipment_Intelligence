import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# THERMODYNAMIC & GAS CONSTANTS (Clean Natural Gas Baseline)
# ---------------------------------------------------------------------------
R_SPECIFIC = 518.3       # J/(kg*K) - Specific gas constant for methane/natural gas
GAMMA = 1.30             # Ratio of specific heats (Cp / Cv)
T1_SUCTION_K = 293.15    # Suction temperature (20 deg C = 293.15 K)
P1_SUCTION_BAR = 20.0    # Absolute suction pressure (20 bar = 2,000,000 Pa)
Z_AVG = 0.95             # Average gas compressibility factor

# Illustrative Design Reference Parameters
N_REF_RPM = 9500.0       # Nominal rotor speed (high-speed centrifugal compressor)
ETA_P_DESIGN = 0.82      # Design polytropic efficiency (82%)
M_DOT_DESIGN = 12.0      # Design mass flow rate (kg/s)
SURGE_FLOW_KG_S = 6.5    # Surge limit flow rate at design speed


# ---------------------------------------------------------------------------
# CORE THERMODYNAMIC & COMPRESSOR EQUATIONS
# ---------------------------------------------------------------------------
def calculate_polytropic_exponent(eta_p, gamma=GAMMA):
    """
    Calculates polytropic temperature exponent: (n - 1) / n = (gamma - 1) / (gamma * eta_p)
    """
    if eta_p <= 0:
        raise ValueError("Polytropic efficiency must be strictly positive.")
    return (gamma - 1.0) / (gamma * eta_p)


def calculate_discharge_temperature(t1_k, pressure_ratio, eta_p, gamma=GAMMA):
    """
    Calculates actual discharge temperature T2 (Kelvin):
    T2 = T1 * (P2 / P1) ^ ((n-1)/n)
    """
    m_exp = calculate_polytropic_exponent(eta_p, gamma)
    return t1_k * (pressure_ratio ** m_exp)


def calculate_polytropic_head_j_kg(t1_k, pressure_ratio, eta_p, r_gas=R_SPECIFIC, z_avg=Z_AVG, gamma=GAMMA):
    """
    Calculates polytropic head H_p in Joules per kilogram (J/kg):
    H_p = Z_avg * R * T1 * (1 / m_exp) * [ (P2/P1)^m_exp - 1 ]
    """
    m_exp = calculate_polytropic_exponent(eta_p, gamma)
    head_j_kg = (z_avg * r_gas * t1_k / m_exp) * ((pressure_ratio ** m_exp) - 1.0)
    return head_j_kg


def calculate_gas_power_kw(mass_flow_kg_s, head_j_kg, eta_p):
    """
    Calculates required compressor gas power in kilowatts:
    P_gas = (mass_flow * H_p) / (eta_p * 1000)
    """
    if eta_p <= 0:
        raise ValueError("Efficiency must be strictly positive.")
    return (mass_flow_kg_s * head_j_kg) / (eta_p * 1000.0)


def calculate_surge_margin_pct(mass_flow_kg_s, surge_flow_limit=SURGE_FLOW_KG_S):
    """
    Calculates safety margin away from aerodynamic surge:
    Surge Margin (%) = ((m_dot - m_dot_surge) / m_dot) * 100
    """
    return ((mass_flow_kg_s - surge_flow_limit) / mass_flow_kg_s) * 100.0


def theoretical_pressure_ratio(mass_flow_kg_s, rpm=N_REF_RPM):
    """
    Simplified compressor characteristic curve:
    Pressure ratio slopes downward as mass flow increases, scaled with speed squared.
    """
    speed_ratio = rpm / N_REF_RPM
    # Base curve: r_p = 2.45 - 0.0035 * m_dot^2
    base_rp = 2.45 - 0.0035 * (mass_flow_kg_s ** 2)
    adjusted_rp = 1.0 + (base_rp - 1.0) * (speed_ratio ** 2)
    return max(float(adjusted_rp), 1.05)


# ---------------------------------------------------------------------------
# SCRIPT VERIFICATION
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 65)
    print("COMPRESSOR ENGINEERING MODULE: VERIFICATION RUN")
    print("=" * 65)

    test_flow = 12.0  # kg/s
    test_rp = theoretical_pressure_ratio(test_flow)
    test_eta = 0.82
    test_t2 = calculate_discharge_temperature(T1_SUCTION_K, test_rp, test_eta)
    test_hp = calculate_polytropic_head_j_kg(T1_SUCTION_K, test_rp, test_eta)
    test_power = calculate_gas_power_kw(test_flow, test_hp, test_eta)
    test_sm = calculate_surge_margin_pct(test_flow)

    print(f"Suction Pressure (P1):       {P1_SUCTION_BAR:.1f} bar")
    print(f"Suction Temperature (T1):    {T1_SUCTION_K - 273.15:.1f} °C ({T1_SUCTION_K:.2f} K)")
    print(f"Design Mass Flow:            {test_flow:.1f} kg/s")
    print(f"Operating Pressure Ratio:    {test_rp:.3f}")
    print(f"Discharge Pressure (P2):     {P1_SUCTION_BAR * test_rp:.2f} bar")
    print(f"Discharge Temperature (T2):  {test_t2 - 273.15:.1f} °C ({test_t2:.2f} K)")
    print(f"Polytropic Head (H_p):       {test_hp / 1000.0:.2f} kJ/kg")
    print(f"Gas Compressor Power:        {test_power:,.1f} kW")
    print(f"Surge Margin:                {test_sm:.1f}%")
    print("=" * 65)