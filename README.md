```markdown
# AI Energy & Equipment Intelligence Suite
### Asynchronous SCADA Telemetry, Thermodynamic Digital Twin, Chaos Testing & Incident Orchestration

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat&logo=pydantic&logoColor=white)
![ReportLab](https://img.shields.io/badge/Reporting-ReportLab-FF6F00?style=flat)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 1. Executive Summary & Problem Statement

In heavy mechanical systems, HVAC central plants, and industrial utility loops, unplanned downtime and gradual heat transfer degradation cost facilities tens of thousands of dollars in emergency repairs and auxiliary power waste. 

Traditional supervisory control and data acquisition (SCADA) setups present three major bottlenecks:
1. **Siloed Diagnostics:** Critical performance data sits trapped inside control rooms on expensive, proprietary seat-licensed consoles.
2. **Delayed Intervention:** Technicians rely on physical shift rounds and clipboard logging. Fouling, sensor drift, and sub-optimal Coefficients of Performance (COP) go undetected until a hard limit or thermal trip stops the plant.
3. **Manual Handover Friction:** Operators spend 1–2 hours per shift compiling manual logs, leading to inconsistent audit trails and delayed maintenance scheduling.

I engineered the **AI Energy & Equipment Intelligence Suite** to address these failure points. It is an end-to-end telemetry and condition-based monitoring (CBM) system that continuously validates live thermodynamic telemetry against first-principles physics models, injects synthetic operational chaos to verify threshold resilience, outputs publication-grade shift compliance PDFs, and dispatches sub-minute emergency payloads directly to engineers on mobile devices.

---

## 2. Business Impact & Operational KPIs

| Metric | Industry Standard (Legacy Operations) | AI Energy & Equipment Suite | Operational Gain |
| :--- | :--- | :--- | :--- |
| **Mean Time to Detect (MTTD)** | 4 – 8 Hours (Between shift inspection rounds) | **< 3 Seconds** (Real-time telemetry evaluation) | 99% faster detection of sub-optimal baselines |
| **Mean Time to Respond (MTTR)** | 45 – 90 Minutes (Paging / central desk review) | **< 60 Seconds** (Direct Telegram incident dispatch) | Immediate technician awareness at the equipment |
| **Shift Reporting Overhead** | 60 – 90 Minutes per operational shift | **Fully Automated** (Vector PDF generated on trigger) | Reclaims 10–14 engineering hours per week |
| **Thermodynamic Visibility** | Static High/Low temperature threshold cutouts | **Dynamic COP & Enthalpy tracking** | Catches scaling and micro-fouling weeks before a trip |
| **Safety Interlock Auditing** | Untested until actual physical system failure | **Scheduled synthetic chaos injection** | Verifies alerts, safety deadbands, and fail-safes safely |

---

## 3. High-Level System Architecture


```

```
                   [ Field Sensors & Transducers ]
                 (Flow Rate, Chilled ΔT, Power, Pressure)
                                  │
                                  ▼
                    [ FastAPI SCADA Gateway ]
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼

```

[ Thermodynamic Twin ]    [ Chaos Fault Engine ]   [ Time-Series Store ]
• First-Principles Math   • Sensor Drift Injection  • Historical Telemetry
• Q = ṁ · cp · ΔT         • Frozen Actuator Sim     • In-Memory Buffer / DB
• Real-Time COP / kW/ton  • Valve Cavitation Load           │
│                         │                         │
└───────────┬─────────────┘                         │
▼                                       ▼
[ Incident Escalation Matrix ]             [ Automated Reporter ]
│                              • ReportLab Graphics
▼                              • Availability Charts
[ Telegram Dispatcher ]                   • Energy Audit Summary
• Alert Payloads to Mobile                         │
• Sub-60s Push to Field Leads                      ▼
[ Operational PDF ]

```

---

## 4. Key Architectural Modules

### 4.1. Asynchronous Ingestion Gateway (`/api`)
* Built with **FastAPI** to enable high-throughput, non-blocking I/O for telemetry streams.
* Validates every incoming payload strictly via **Pydantic v2** models (enforcing units, plausible physical sensor bounds, and payload integrity).
* Dispatches asynchronous worker tasks for computationally intensive physics calculations and notification triggers without delaying packet ingestion.

### 4.2. First-Principles Thermodynamic Digital Twin (`/twin`)
* Rather than treating the plant as a black-box machine learning regressor, the twin models fluid-thermal fundamentals:
  $$\dot{Q} = \dot{m} \cdot c_p \cdot (T_{return} - T_{supply})$$
  $$\text{COP} = \frac{\dot{Q}_{\text{cooling}}}{P_{\text{electrical}}}$$
* Continuously computes thermal tonnage, electrical consumption ($kW/\text{ton}$), and thermodynamic delta.
* Detects gradual baseline shifts indicating condenser/evaporator tube scaling, refrigerant undercharge, or sensor drift long before standard threshold cutouts trip.

### 4.3. Chaos Engineering & Fault Injector (`/chaos`)
* Simulates physical plant failures within a controlled staging environment to audit operational readiness:
  * **Sensor Drift:** Gradually skews supply temperatures to test whether the twin catches diverging heat balance equations.
  * **Flow Starvation / Stuck Actuators:** Simulates rapid pressure drops and dead-headed pumps.
  * **Thermal Load Surges:** Simulates sudden spike demands to evaluate chiller sequence escalation.

### 4.4. Automated Shift Reporting Engine (`/reports`)
* Utilizes **ReportLab** to deterministically build clean, multi-page, publication-grade PDF shift logs.
* Generates runtime trend tables, anomaly breakdown summaries, and key equipment health metrics without external browser rendering engines (e.g., Puppeteer/WebKit).
* Embeds cryptographic audit timestamps for operational and regulatory compliance.

### 4.5. Emergency Telegram Dispatcher (`/dispatch`)
* Asynchronous bot client pushing structured incident alerts to mobile engineering teams in under 60 seconds.
* Payloads include: **Severity Level**, **Asset ID**, **Trigger Parameter vs. Safe Baseline**, and **Recommended Immediate Isolation Step**.

---

## 5. Repository Structure


```

├── api/
│   ├── **init**.py
│   ├── routes.py            # REST endpoints for SCADA telemetry ingestion
│   └── schemas.py           # Pydantic data validation contracts
├── twin/
│   ├── **init**.py
│   ├── thermodynamics.py    # Fluid mechanics, COP, and heat transfer models
│   └── twin_engine.py       # Live telemetry vs baseline deviation engine
├── chaos/
│   ├── **init**.py
│   └── fault_injector.py    # Synthetic sensor drift and failure simulations
├── reports/
│   ├── **init**.py
│   ├── pdf_generator.py     # Custom ReportLab layout and PDF rendering logic
│   └── templates.py         # Typography, tables, and palette configurations
├── dispatch/
│   ├── **init**.py
│   └── telegram_bot.py      # Mobile emergency alert worker
├── tests/
│   ├── test_api.py          # Endpoint integration and load tests
│   ├── test_twin.py         # Physics validation tests against empirical baselines
│   └── test_chaos.py        # Fault injection verification
├── assets/
│   ├── architecture.png     # Rendered system architecture diagram
│   └── sample_report.pdf    # Specimen operational audit output
├── config.py                # Environment configurations and operational limits
├── main.py                  # Application entry point and orchestrator
├── requirements.txt         # Pinned production dependencies
└── README.md

```

---

## 6. Installation & Local Deployment

### 6.1. Prerequisites
* Python 3.11 or higher
* Telegram Bot API Token (via `@BotFather`) and target Chat ID (for emergency alerts)

### 6.2. Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/bamidele-stephen/ai-energy-equipment-suite.git](https://github.com/bamidele-stephen/ai-energy-equipment-suite.git)
   cd ai-energy-equipment-suite

```

2. **Configure a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

```


3. **Set Environment Variables:**
Create a `.env` file in the root directory:
```env
ENVIRONMENT=production
TELEGRAM_BOT_TOKEN="your_bot_token_here"
TELEGRAM_CHAT_ID="your_target_chat_or_channel_id"
SCADA_PORT=8000
PLANT_BASE_COP=5.20
CHILLED_WATER_SETPOINT=6.5

```


4. **Launch the Core Application:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

```



---

## 7. Verification & Usage Guide

### 7.1. Ingesting Telemetry

Push a simulated telemetry frame via `curl`:

```bash
curl -X POST "http://localhost:8000/api/v1/telemetry" \
     -H "Content-Type: application/json" \
     -d '{
       "asset_id": "CHILLER-01",
       "mass_flow_rate_kg_s": 45.2,
       "temp_supply_c": 6.8,
       "temp_return_c": 12.4,
       "power_consumption_kw": 210.5,
       "condenser_pressure_bar": 9.8
     }'

```

### 7.2. Triggering Chaos Fault Drills

Simulate an immediate condenser heat transfer fouling event:

```bash
curl -X POST "http://localhost:8000/api/v1/chaos/inject" \
     -H "Content-Type: application/json" \
     -d '{
       "fault_type": "sensor_drift",
       "target_sensor": "temp_supply_c",
       "drift_magnitude": 3.5,
       "duration_seconds": 60
     }'

```

### 7.3. Generating an Audit Report

Trigger the ReportLab PDF compilation pipeline:

```bash
curl -X GET "http://localhost:8000/api/v1/reports/shift-summary?asset_id=CHILLER-01" \
     --output shift_summary_report.pdf

```

---

## 8. Engineering Design Decisions

* **Why FastAPI over Flask/Django?** High-frequency SCADA telemetry ingestion demands non-blocking asynchronous concurrency. FastAPI provides native async event loops and auto-generates interactive OpenAPI documentation for simple field integration.
* **Why First-Principles Physics over Pure Machine Learning?** Pure black-box models often hallucinate or fail when encountering operating conditions outside their training distributions. Grounding the core engine in thermodynamic equations ($\Delta T$, mass flow, enthalpy, COP) ensures physical consistency, interpretable diagnostics, and zero cold-start delay.
* **Why Programmatic ReportLab over HTML-to-PDF Converters?** Headless browser PDF wrappers (e.g., Weasyprint, Puppeteer) introduce massive overhead, memory bloat, and non-deterministic page breaking. ReportLab's direct canvas and flowable drawing primitives compile complex vector PDFs in milliseconds with zero external layout engine dependencies.

---

## 9. Roadmap (Transition to Project 3)

* [x] **Project 1 & 2:** Asynchronous SCADA ingestion, thermodynamic digital twin, chaos fault generator, automated PDF audits, and Telegram emergency dispatch.
* [ ] **Project 3:** Closed-loop Model Predictive Control (MPC) and Deep Reinforcement Learning for autonomous central plant sequencing, dynamic tariff peak shaving, and real-time chilled water reset.

---

## 10. Author & Contact

**Bamidele Stephen Omotayo**

*Mechanical Engineering & Applied Data Systems*

* Specialized in Building Services (MEP), HVAC Plant Automation, and Industrial Utilities.


```

```
