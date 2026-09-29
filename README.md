# ⚡ AI Energy & Equipment Intelligence Suite

### Physics-Informed Machine Learning & Diagnostic Suite for Industrial Process & Rotating Machinery

---

## 📌 Executive Summary

The **AI Energy & Equipment Intelligence Suite** is an industrial plant intelligence platform engineered to bridge first-principles mechanical engineering with machine learning.

Rather than treating industrial equipment as black-box statistical entities, this system couples governing physical laws (thermodynamics, fluid mechanics, and ISO vibration standards) with trained classifiers to identify root causes of equipment degradation, compute real-time energy penalties ($\text{kW}$ waste), quantify financial leakage ($\$/\text{year}$), and recommend corrective maintenance actions.

---

## 🏭 Monitored Asset Fleet

### 1. Centrifugal Pump System (Hydraulics & Mechanics)

* **Governing Physics:** Euler Turbomachinery Equations, Pump Quadratic Droop Characteristics, and Affinity Scaling Laws:
  $$H = \left( H_0 - k \cdot Q^2 \right) \cdot \left( \frac{N}{N_{\text{ref}}} \right)^2$$

* **Power Dynamics:** Hydraulic to shaft power conversion:
  $$P_{\text{hyd}} = \frac{\rho \cdot g \cdot Q \cdot H}{1000} \quad [\text{kW}]$$
  $$P_{\text{shaft}} = \frac{P_{\text{hyd}}}{\eta}$$

* **Diagnostic Scope:**
  * Impeller wear-ring clearance expansion & internal recirculatory slip.
  * Volute cutwater cavitation / suction strainer starvation ($\text{NPSH}_a < \text{NPSH}_r$).
  * Mechanical vibration severity mapping conforming to **ISO 10816-3** (Zones A through D).
  * Excess hydraulic electrical penalty ($\text{kW}$) and annualized operational loss.

---

### 2. Centrifugal Gas Compressor System (Thermodynamics & Aerodynamics)

* **Thermodynamic Model:** Real-gas polytropic compression conforming to Schultz & ASME PTC 10 guidelines:
  $$n = \frac{1}{1 - \left( \frac{\gamma - 1}{\gamma \cdot \eta_p} \right)}$$
  $$T_2 = T_1 \cdot (r_p)^{\frac{n - 1}{n}}$$
  $$H_p = Z_{\text{avg}} \cdot \frac{R_{\text{univ}}}{M_w} \cdot T_1 \cdot \left( \frac{n}{n - 1} \right) \cdot \left[ (r_p)^{\frac{n - 1}{n}} - 1 \right] \quad [\text{kJ/kg}]$$

* **Aerodynamic Stability & Surge Proximity:**
  $$\text{Surge Margin (\%)} = \left( \frac{\dot{m}_{\text{live}} - \dot{m}_{\text{surge}}}{\dot{m}_{\text{surge}}} \right) \times 100\%$$

* **Diagnostic Scope:**
  * Real-time aerodynamic surge trip risk detection ($< 10\%$ critical threshold).
  * Polymeric and particulate impeller fouling detection via polytropic efficiency droop ($\Delta \eta_p$) and thermal accumulation.
  * Rotor unbalance, hydrodynamic journal bearing deterioration, and flow buffeting vibration analysis.
  * Gas shaft power deviation against healthy aerodynamic baseline curves.

---

### 3. Shell & Tube Heat Exchanger System (Thermal & Hydraulics)

* **Governing Heat Duty & Thermal Balance:**
  $$Q = \dot{m}_h \cdot c_{p,h} \cdot (T_{h,\text{in}} - T_{h,\text{out}}) = \dot{m}_c \cdot c_{p,c} \cdot (T_{c,\text{out}} - T_{c,\text{in}}) \quad [\text{kW}]$$

* **Log Mean Temperature Difference (LMTD) & Heat Transfer:**
  $$\text{LMTD}_{\text{cf}} = \frac{(T_{h,\text{in}} - T_{c,\text{out}}) - (T_{h,\text{out}} - T_{c,\text{in}})}{\ln \left( \frac{T_{h,\text{in}} - T_{c,\text{out}}}{T_{h,\text{out}} - T_{c,\text{in}}} \right)}$$
  $$U_{\text{actual}} = \frac{Q}{A \cdot F_t \cdot \text{LMTD}_{\text{cf}}} \quad \left[ \frac{\text{W}}{\text{m}^2 \cdot \text{K}} \right]$$

* **TEMA Fouling Resistance & Hydraulic Penalty:**
  $$R_f = \frac{1}{U_{\text{actual}}} - \frac{1}{U_{\text{clean}}} \quad \left[ \frac{\text{m}^2 \cdot \text{K}}{\text{W}} \right]$$
  $$\Delta P_{\text{fouled}} = \Delta P_{\text{clean}} \cdot \left( 1 + \beta \cdot R_f \right) \cdot \left( \frac{\dot{m}}{\dot{m}_{\text{ref}}} \right)^{1.85}$$

* **Diagnostic Scope:**
  * Tube-side scaling/coking detection vs. shell-side bundle particulate sedimentation.
  * TEMA alert threshold violation ($R_f \ge 0.00035 \text{ to } 0.0005\,\text{m}^2\cdot\text{K/W}$).
  * Tube bundle bypass, baffle leakage, and cross-contamination indicators.
  * Pump/compressor auxiliary pumping energy penalty driven by fouling hydraulic constriction.