# ⚡ AI Energy & Equipment Intelligence Suite
### *Physics-Informed Machine Learning & Diagnostic Suite for Industrial Process & Rotating Machinery*

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Machine Learning](https://img.shields.io/badge/ML-Scikit--Learn-F7931E.svg)](https://scikit-learn.org/)
[![Status](https://img.shields.io/badge/Status-Operational%20v2.0-success.svg)]()

---

## 📌 Executive Summary

The AI Energy & Equipment Intelligence Suite is an industrial plant intelligence platform engineered to bridge first-principles mechanical engineering with machine learning.

Rather than treating industrial equipment as black-box statistical entities, this system couples governing physical laws (thermodynamics, fluid mechanics, and ISO vibration standards) with trained classifiers to identify root causes of equipment degradation, compute real-time energy penalties (kW waste), quantify financial leakage ($/year), and recommend corrective maintenance actions.

---

## 🏭 Monitored Asset Fleet

### 1. Centrifugal Pump System (Hydraulics & Mechanics)
* Governing Physics: Euler Turbomachinery Equations, Pump Quadratic Droop Characteristics, and Affinity Scaling Laws:
  H = (H0 - k * Q^2) * (N / N_ref)^2
* Power Dynamics: Hydraulic to shaft power conversion:
  P_hyd = (rho * g * Q * H) / 1000
  P_shaft = P_hyd / eta
* Diagnostic Scope:
  - Impeller wear-ring clearance expansion & internal slip.
  - Volute cutwater cavitation / suction strainer starvation.
  - Mechanical vibration severity mapping conforming to ISO 10816-3 (Zones A through D).
  - Excess hydraulic electrical penalty (kW) and annualized operational loss.

---

### 2. Centrifugal Gas Compressor System (Thermodynamics & Aerodynamics)
* Thermodynamic Model: Real-gas polytropic compression under Schultz / ASME PTC 10 guidelines:
  n = 1 / (1 - ((gamma - 1) / (gamma * eta_p)))
  T2 = T1 * (r_p)^((n - 1) / n)
  H_p = Z_avg * R * T1 * (n / (n - 1)) * ((r_p)^((n - 1) / n) - 1)
* Aerodynamic Stability & Surge Proximity:
  Surge Margin (%) = ((m_dot_live - m_dot_surge) / m_dot_surge) * 100
* Diagnostic Scope:
  - Real-time aerodynamic surge trip risk detection (< 10% critical threshold).
  - Polymeric and particulate impeller fouling detection via polytropic efficiency droop and thermal accumulation.
  - Unbalance, journal bearing deterioration, and flow buffeting vibration analysis.
  - Gas shaft power deviation against healthy aerodynamic baseline curves.

---

### 3. Shell & Tube Heat Exchanger (Roadmap / In-Development)
* Governing Physics: Logarithmic Mean Temperature Difference (LMTD) & NTU Method:
  Delta_T_lm = (Delta_T_1 - Delta_T_2) / ln(Delta_T_1 / Delta_T_2)
  Q = U * A * F * Delta_T_lm
* Diagnostic Scope:
  - Thermal fouling factor resistance (Rf) tracking across tube-side and shell-side circuits.
  - Utility stream waste quantification and thermal heat recovery degradation.

---

## 🧱 Repository Architecture

AI_Energy_Equipment_Intelligence/
│
├── engineering/                          # Physics & Diagnostic Engines
│   ├── pump_engineering.py               # Hydraulic governing equations & curves
│   ├── pump_intelligence.py              # ISO 10816 vibration & pump fault reasoning
│   ├── compressor_engineering.py         # Polytropic thermodynamics & surge limits
│   └── compressor_intelligence.py        # Compressor root-cause diagnostic engine
│
├── data/                                 # Telemetry Generation & Datasets
│   ├── generate_compressor_data.py       # Physics-informed synthetic compressor data
│   ├── compressor_dataset.csv            # 1,200 compressor operating records
│   └── (pump dataset artifacts)
│
├── models/                               # Machine Learning Pipelines
│   ├── train_compressor_classifier.py    # Training & evaluation pipeline (RF / LR)
│   ├── compressor_condition_model.joblib # Serialized compressor production model
│   └── pump_condition_model.joblib       # Serialized pump production model
│
├── app/                                  # Multi-Asset Operator Dashboard
│   └── streamlit_app.py                  # Interactive dual-asset telemetry suite
│
├── requirements.txt                      # Project dependencies
└── README.md                             # Documentation

---

## 🚀 Quickstart & Installation

1. Clone the Repository:
   git clone https://github.com/Bamstep/AI_Energy_Equipment_Intelligence.git
   cd AI_Energy_Equipment_Intelligence

2. Set Up Virtual Environment:
   # On Windows:
   python -m venv venv
   .\venv\Scripts\activate

   # On Linux/macOS:
   python3 -m venv venv
   source venv/bin/activate

3. Install Dependencies:
   pip install -r requirements.txt
   (Core packages: streamlit, scikit-learn, pandas, numpy, matplotlib, joblib)

4. Execute the Plant Suite:
   streamlit run app/streamlit_app.py

   Open http://localhost:8501 in your browser to interact with the fleet monitor.

---

## 📊 Diagnostic Rule Hierarchy & Standards

| Metric / Parameter | Evaluation Standard | Warning Threshold | Critical Fault Action |
| :--- | :--- | :--- | :--- |
| Vibration (RMS) | ISO 10816-3 (Class II/III) | > 2.8 mm/s (Zone C) | > 4.5 mm/s (Zone D: Immediate Trip / Spectral FFT Analysis) |
| Compressor Surge Margin | ASME PTC 10 / OEM Dynamic | 10% - 15% Buffer | < 10% (Modulate Anti-Surge Recycle Valve Immediately) |
| Pump Hydraulic Head | Euler Droop Curve | -6% deviation | Inspect Suction Strainer & Check Wear-Ring Clearances |
| Polytropic Efficiency | ASME Real Gas Thermodynamics | -6% deviation | Schedule Online/Offline Impeller & Diffuser Wash Cycle |

---

## 👤 Author
* Bamidele Stephen Omotayo
* Focus: Mechanical Engineering, Process Plant Intelligence, Predictive Maintenance & Energy Optimization.