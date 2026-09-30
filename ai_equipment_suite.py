import asyncio
import json
import os
import sqlite3
import time
from dataclasses import dataclass
from typing import Dict, Any, List
import numpy as np
from sklearn.ensemble import IsolationForest

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8995918478:AAHA3nAELY0ejJ3fJP58qD2tKOtatgv_qoY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8049623204")

chaos_state = {
    "active_fault": None
}

def dispatch_telegram_alert(pdf_path: str, caption: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(pdf_path, "rb") as f:
            files = {"document": (os.path.basename(pdf_path), f, "application/pdf")}
            data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
            requests.post(url, data=data, files=files, timeout=12)
            print(f"[CHAOS-ESD] Telegram incident report dispatched: {caption}")
    except Exception as e:
        print(f"[CHAOS-ESD] Telegram dispatch failed: {e}")


# ReportLab imports for automated PDF incident reporting
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ==============================================================================
# SECTION 1: 4-ASSET THERMODYNAMIC & HYDRAULIC INTELLIGENCE MODELS
# ==============================================================================

@dataclass
class PumpTelemetry:
    flow_m3h: float
    head_m: float
    power_kw: float
    vibration_mms: float
    bearing_temp_c: float

class PumpIntelligence:
    WATER_DENSITY = 998.0
    GRAVITY = 9.81
    BEP_FLOW = 120.0

    def evaluate(self, tel: PumpTelemetry) -> Dict[str, Any]:
        q_m3s = tel.flow_m3h / 3600.0
        hyd_power_kw = (self.WATER_DENSITY * self.GRAVITY * q_m3s * tel.head_m) / 1000.0
        efficiency_pct = (hyd_power_kw / max(0.1, tel.power_kw)) * 100.0
        
        anomalies = []
        if tel.vibration_mms > 4.5:
            anomalies.append(f"High Vibration ({tel.vibration_mms:.2f} mm/s): Cavitation or imbalance")
        if tel.bearing_temp_c > 75.0:
            anomalies.append(f"High Bearing Temp ({tel.bearing_temp_c:.1f}°C)")
        if abs(tel.flow_m3h - self.BEP_FLOW) / self.BEP_FLOW > 0.35:
            anomalies.append("Operating off Best Efficiency Point")

        health = max(0, min(100, int(100 - (len(anomalies) * 20) - max(0.0, 75.0 - efficiency_pct))))
        return {
            "efficiency_pct": round(min(100.0, efficiency_pct), 2),
            "health_score": health,
            "anomalies": anomalies
        }

@dataclass
class CompressorTelemetry:
    suction_pressure_bar: float
    discharge_pressure_bar: float
    suction_temp_c: float
    discharge_temp_c: float
    flow_cfm: float
    motor_kw: float

class CompressorIntelligence:
    GAMMA = 1.4

    def evaluate(self, tel: CompressorTelemetry) -> Dict[str, Any]:
        p_ratio = max(1.0, tel.discharge_pressure_bar / max(0.1, tel.suction_pressure_bar))
        specific_power = tel.motor_kw / max(1.0, (tel.flow_cfm / 100.0))
        t_in_k = tel.suction_temp_c + 273.15
        t_out_ideal_c = (t_in_k * (p_ratio ** ((self.GAMMA - 1) / self.GAMMA))) - 273.15
        
        anomalies = []
        if tel.discharge_temp_c > (t_out_ideal_c + 30.0):
            anomalies.append("High Discharge Superheat: Valve slip or seal leakage")
        if specific_power > 22.0:
            anomalies.append(f"High Specific Power ({specific_power:.2f} kW/100CFM)")

        health = max(0, min(100, int(100 - (len(anomalies) * 22) - max(0.0, specific_power - 18.0) * 3)))
        return {
            "pressure_ratio": round(p_ratio, 2),
            "specific_power_kw_100cfm": round(specific_power, 2),
            "health_score": health,
            "anomalies": anomalies
        }

@dataclass
class HeatExchangerTelemetry:
    hot_in_temp_c: float
    hot_out_temp_c: float
    cold_in_temp_c: float
    cold_out_temp_c: float
    hot_flow_m3h: float
    cold_flow_m3h: float

class HeatExchangerIntelligence:
    WATER_CP = 4.186

    def evaluate(self, tel: HeatExchangerTelemetry) -> Dict[str, Any]:
        m_hot = (tel.hot_flow_m3h * 1000.0) / 3600.0
        m_cold = (tel.cold_flow_m3h * 1000.0) / 3600.0
        q_hot = m_hot * self.WATER_CP * (tel.hot_in_temp_c - tel.hot_out_temp_c)
        q_cold = m_cold * self.WATER_CP * (tel.cold_out_temp_c - tel.cold_in_temp_c)
        
        dt1 = max(0.1, tel.hot_in_temp_c - tel.cold_out_temp_c)
        dt2 = max(0.1, tel.hot_out_temp_c - tel.cold_in_temp_c)
        lmtd = (dt1 - dt2) / np.log(dt1 / dt2) if dt1 != dt2 else dt1
        heat_imbalance_pct = abs(q_hot - q_cold) / max(0.1, max(q_hot, q_cold)) * 100.0
        
        anomalies = []
        if heat_imbalance_pct > 8.0:
            anomalies.append(f"Duty Imbalance ({heat_imbalance_pct:.1f}%): Sensor calibration drift")
        if lmtd < 3.0:
            anomalies.append("Critically low LMTD: Operating near pinch point")

        health = max(0, min(100, int(100 - (len(anomalies) * 20) - (heat_imbalance_pct * 1.5))))
        return {
            "duty_kw": round((q_hot + q_cold) / 2.0, 2),
            "lmtd_c": round(lmtd, 2),
            "heat_imbalance_pct": round(heat_imbalance_pct, 2),
            "health_score": health,
            "anomalies": anomalies
        }

@dataclass
class ChillerTowerTelemetry:
    chw_supply_temp_c: float
    chw_return_temp_c: float
    chw_flow_rate_m3h: float
    compressor_kw: float
    cw_supply_temp_c: float
    cw_return_temp_c: float
    cw_flow_rate_m3h: float
    ambient_wet_bulb_c: float
    basin_tds_ppm: float
    makeup_tds_ppm: float

class ChillerTowerIntelligence:
    WATER_CP = 4.186
    TON_KW = 3.51685

    def evaluate(self, tel: ChillerTowerTelemetry) -> Dict[str, Any]:
        m_chw = (tel.chw_flow_rate_m3h * 1000.0) / 3600.0
        q_evap_kw = m_chw * self.WATER_CP * (tel.chw_return_temp_c - tel.chw_supply_temp_c)
        cooling_tons = max(0.1, q_evap_kw / self.TON_KW)
        kw_per_ton = tel.compressor_kw / cooling_tons
        tower_approach = tel.cw_return_temp_c - tel.ambient_wet_bulb_c
        coc = tel.basin_tds_ppm / max(1.0, tel.makeup_tds_ppm)
        
        anomalies = []
        if kw_per_ton > 0.70:
            anomalies.append(f"High Specific Power ({kw_per_ton:.2f} kW/TR): Scaling suspected")
        if tower_approach > 4.5:
            anomalies.append(f"Excessive Tower Approach ({tower_approach:.1f}°C)")
        if coc > 5.5:
            anomalies.append(f"High Cycles of Concentration ({coc:.1f}): Scaling risk")

        health = max(0, min(100, int(100 - (len(anomalies) * 18) - max(0.0, kw_per_ton - 0.58) * 80)))
        return {
            "cooling_capacity_tons": round(cooling_tons, 1),
            "kw_per_ton": round(kw_per_ton, 3),
            "tower_approach_c": round(tower_approach, 2),
            "cycles_of_concentration": round(coc, 2),
            "health_score": health,
            "anomalies": anomalies
        }

# ==============================================================================
# SECTION 2: PREDICTIVE MAINTENANCE & REMAINING USEFUL LIFE (RUL) ENGINE
# ==============================================================================

class PredictiveMaintenanceEngine:
    def __init__(self):
        self.pump_bearing_damage = 0.0
        self.chiller_fouling_index = 0.0
        self.baseline_rul_hours = 2400.0

    def step_degradation(self, vib_mms: float, chiller_kw_ton: float) -> Dict[str, Any]:
        if vib_mms > 4.5:
            self.pump_bearing_damage += 0.25 * ((vib_mms / 4.5) ** 2)
        else:
            self.pump_bearing_damage += 0.01

        if chiller_kw_ton > 0.68:
            self.chiller_fouling_index += 0.30 * ((chiller_kw_ton / 0.60) ** 1.8)
        else:
            self.chiller_fouling_index += 0.02

        self.pump_bearing_damage = min(99.0, self.pump_bearing_damage)
        self.chiller_fouling_index = min(99.0, self.chiller_fouling_index)

        critical_damage = max(self.pump_bearing_damage, self.chiller_fouling_index)
        projected_rul = max(12.0, self.baseline_rul_hours * (1.0 - (critical_damage / 100.0)))

        return {
            "pump_bearing_wear_pct": round(self.pump_bearing_damage, 1),
            "chiller_fouling_pct": round(self.chiller_fouling_index, 1),
            "fleet_rul_hours": int(projected_rul)
        }

    def reset_chiller_fouling(self):
        self.chiller_fouling_index = 0.0

    def reset_pump_wear(self):
        self.pump_bearing_damage = max(0.0, self.pump_bearing_damage - 15.0)

# ==============================================================================
# SECTION 3: SQLITE TIME-SERIES REPOSITORY & MACHINE LEARNING DRIFT DETECTOR
# ==============================================================================

class TelemetryRepository:
    def __init__(self, db_path: str = "equipment_telemetry.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fleet_telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    plant_health INTEGER,
                    status TEXT,
                    pump_health INTEGER,
                    comp_health INTEGER,
                    hex_health INTEGER,
                    chiller_health INTEGER,
                    raw_json TEXT
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def log_snapshot(self, evaluation: Dict[str, Any], raw_frame: Dict[str, Any]):
        diag = evaluation["diagnostics"]
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO fleet_telemetry (
                    timestamp, plant_health, status, 
                    pump_health, comp_health, hex_health, chiller_health, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evaluation["timestamp"],
                evaluation["plant_health"],
                evaluation["status"],
                diag["pump"]["health_score"],
                diag["compressor"]["health_score"],
                diag["hex"]["health_score"],
                diag["chiller_tower"]["health_score"],
                json.dumps(raw_frame)
            ))
            conn.commit()
        finally:
            conn.close()

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM fleet_telemetry ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows][::-1]
        finally:
            conn.close()

class MLAnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.08, random_state=42)
        self.is_fitted = False
        self._train_baseline()

    def _train_baseline(self):
        np.random.seed(42)
        nominal_features = []
        for _ in range(150):
            nominal_features.append([
                np.random.normal(118.0, 1.0),
                np.random.normal(2.1, 0.2),
                np.random.normal(17.4, 0.3),
                np.random.normal(92.0, 1.0),
                np.random.normal(3.8, 0.4),
                np.random.normal(0.61, 0.02)
            ])
        self.model.fit(np.array(nominal_features))
        self.is_fitted = True

    def predict_drift(self, frame: Dict[str, Any], diag: Dict[str, Any]) -> bool:
        feature_vector = np.array([[
            frame["pump"]["flow_m3h"],
            frame["pump"]["vibration_mms"],
            diag["compressor"]["specific_power_kw_100cfm"],
            frame["compressor"]["discharge_temp_c"],
            diag["chiller_tower"]["tower_approach_c"],
            diag["chiller_tower"]["kw_per_ton"]
        ]])
        pred = self.model.predict(feature_vector)
        return bool(pred[0] == -1)

# ==============================================================================
# SECTION 4: AUTOMATED REPORTLAB PDF INCIDENT GENERATOR
# ==============================================================================

class PDFIncidentReporter:
    @staticmethod
    def generate_incident_report(report_data: Dict[str, Any], filename: str = "incident_report.pdf") -> str:
        doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        elements = []

        title_style = ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1A365D"),
            spaceAfter=8
        )
        elements.append(Paragraph("AI Equipment Intelligence Incident Report", title_style))
        elements.append(Paragraph(f"<b>Timestamp:</b> {report_data['timestamp']} | <b>Plant Status:</b> {report_data['status']} (Health: {report_data['plant_health']}/100)", styles['Normal']))
        elements.append(Spacer(1, 15))

        diag = report_data["diagnostics"]
        table_data = [
            ["Asset Component", "Primary Metric", "Health Score", "Condition"]
        ]
        
        status_for = lambda h: "Optimal" if h >= 85 else ("Warning" if h >= 65 else "Critical")

        table_data.append(["Centrifugal Pump", f"{diag['pump']['efficiency_pct']}% Wire-to-Water Eff", f"{diag['pump']['health_score']}/100", status_for(diag['pump']['health_score'])])
        table_data.append(["Recip/Centrif Compressor", f"{diag['compressor']['specific_power_kw_100cfm']} kW/100CFM", f"{diag['compressor']['health_score']}/100", status_for(diag['compressor']['health_score'])])
        table_data.append(["Shell & Tube HEX", f"{diag['hex']['duty_kw']} kW Thermal Duty", f"{diag['hex']['health_score']}/100", status_for(diag['hex']['health_score'])])
        table_data.append(["Chiller & Cooling Tower", f"{diag['chiller_tower']['kw_per_ton']} kW/TR", f"{diag['chiller_tower']['health_score']}/100", status_for(diag['chiller_tower']['health_score'])])

        t = Table(table_data, colWidths=[150, 160, 90, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 15))

        elements.append(Paragraph("<b>Triggered Diagnostic Advisories:</b>", styles['Heading3']))
        if report_data["alarms"]:
            for alarm in report_data["alarms"]:
                elements.append(Paragraph(f"• <font color='#C53030'><b>{alarm}</b></font>", styles['Normal']))
        else:
            elements.append(Paragraph("• No physical limit alarms recorded during this cycle.", styles['Normal']))

        if report_data.get("ml_anomaly"):
            elements.append(Paragraph("• <font color='#DD6B20'><b>[ML DRIFT ALERT] Multivariate Isolation Forest detected an operational drift pattern.</b></font>", styles['Normal']))

        doc.build(elements)
        return filename

# ==============================================================================
# SECTION 5: NATIVE ASYNCIO INDUSTRIAL PLC / SCADA TCP REGISTER BRIDGE
# ==============================================================================

class NativeIndustrialTCPBridge:
    def __init__(self, host: str = "127.0.0.1", port: int = 5020):
        self.host = host
        self.port = port
        self.registers = {
            "40001_plant_health": 100,
            "40002_plant_status": 0,
            "40003_pump_health": 100,
            "40004_comp_health": 100,
            "40005_hex_health": 100,
            "40006_chiller_health": 100,
            "40007_pump_flow_x10": 1180,
            "40008_chiller_kw_per_tr_x100": 60
        }

    def update_registers(self, plant_health: int, status_code: int, p_h: int, c_h: int, h_h: int, ct_h: int, flow: float, kw_tr: float):
        self.registers["40001_plant_health"] = plant_health
        self.registers["40002_plant_status"] = status_code
        self.registers["40003_pump_health"] = p_h
        self.registers["40004_comp_health"] = c_h
        self.registers["40005_hex_health"] = h_h
        self.registers["40006_chiller_health"] = ct_h
        self.registers["40007_pump_flow_x10"] = int(flow * 10)
        self.registers["40008_chiller_kw_per_tr_x100"] = int(kw_tr * 100)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            payload = json.dumps(self.registers).encode('utf-8') + b"\n"
            writer.write(payload)
            await writer.drain()
        except Exception:
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        async with server:
            await server.serve_forever()

tcp_bridge = NativeIndustrialTCPBridge()

# ==============================================================================
# SECTION 6: ACTUATOR CONTROLS & AUTONOMOUS AGENT
# ==============================================================================

class SCADAActuators:
    def __init__(self):
        self.blowdown_open = False
        self.pump_vfd_hz = 50.0
        self.fouling_mitigation_active = False
        self.autonomous_healing_enabled = True

actuators = SCADAActuators()

class AutonomousHealingAgent:
    @staticmethod
    def evaluate_and_heal(eval_result: Dict[str, Any], raw_frame: Dict[str, Any]) -> List[str]:
        if not actuators.autonomous_healing_enabled:
            return []

        actions_taken = []
        diag = eval_result["diagnostics"]

        # 1. Self-Healing Chiller Tube Scaling
        if diag["chiller_tower"]["kw_per_ton"] > 0.72:
            actuators.fouling_mitigation_active = True
            matrix.rul_engine.reset_chiller_fouling()
            actions_taken.append("[AGENT ACTION] Chiller scale surge detected -> Executed automatic chemical flush.")

        # 2. Self-Healing High Cooling Tower Cycles of Concentration
        if diag["chiller_tower"]["cycles_of_concentration"] > 5.5:
            actuators.blowdown_open = True
            actions_taken.append("[AGENT ACTION] High basin TDS -> Automated blowdown valve energized.")

        # 3. Self-Healing Pump Off-Design / Vibration Spikes
        if raw_frame["pump"]["vibration_mms"] > 4.2 or actuators.pump_vfd_hz > 52.0:
            actuators.pump_vfd_hz = 50.0
            matrix.rul_engine.reset_pump_wear()
            actions_taken.append("[AGENT ACTION] Pump cavitation stress -> Reset VFD to nominal 50.0 Hz.")

        return actions_taken

# ==============================================================================
# SECTION 7: GLOBAL FLEET MATRIX COORDINATOR
# ==============================================================================

class GlobalFleetMatrix:
    def __init__(self):
        self.pump = PumpIntelligence()
        self.comp = CompressorIntelligence()
        self.hex = HeatExchangerIntelligence()
        self.chiller = ChillerTowerIntelligence()
        self.db = TelemetryRepository()
        self.ml = MLAnomalyDetector()
        self.pdf = PDFIncidentReporter()
        self.rul_engine = PredictiveMaintenanceEngine()
        self.agent = AutonomousHealingAgent()
        self.last_pdf_generated_at = 0.0

    def process_frame(self, frame: Dict[str, Any]) -> Dict[str, Any]:
        p = self.pump.evaluate(PumpTelemetry(**frame["pump"]))
        c = self.comp.evaluate(CompressorTelemetry(**frame["compressor"]))
        h = self.hex.evaluate(HeatExchangerTelemetry(**frame["heat_exchanger"]))
        ct = self.chiller.evaluate(ChillerTowerTelemetry(**frame["chiller_tower"]))

        healths = [p["health_score"], c["health_score"], h["health_score"], ct["health_score"]]
        alarms = (
            [f"[Pump] {a}" for a in p["anomalies"]] +
            [f"[Compressor] {a}" for a in c["anomalies"]] +
            [f"[HEX] {a}" for a in h["anomalies"]] +
            [f"[Chiller/Tower] {a}" for a in ct["anomalies"]]
        )
        plant_health = int(np.mean(healths))
        status = "OPTIMAL" if plant_health >= 85 else ("WARNING" if plant_health >= 65 else "CRITICAL")
        
        diag = {"pump": p, "compressor": c, "hex": h, "chiller_tower": ct}
        ml_alert = self.ml.predict_drift(frame, diag)

        rul_data = self.rul_engine.step_degradation(
            vib_mms=frame["pump"]["vibration_mms"],
            chiller_kw_ton=ct["kw_per_ton"]
        )

        eval_result = {
            "timestamp": frame["timestamp"],
            "plant_health": plant_health,
            "status": status,
            "alarms": alarms,
            "ml_anomaly": ml_alert,
            "rul": rul_data,
            "diagnostics": diag,
            "agent_actions": []
        }

        # Autonomous closed-loop intervention
        actions = self.agent.evaluate_and_heal(eval_result, frame)
        eval_result["agent_actions"] = actions

        # Update Industrial PLC / SCADA TCP Registers
        status_code = 0 if status == "OPTIMAL" else (1 if status == "WARNING" else 2)
        tcp_bridge.update_registers(
            plant_health=plant_health,
            status_code=status_code,
            p_h=p["health_score"],
            c_h=c["health_score"],
            h_h=h["health_score"],
            ct_h=ct["health_score"],
            flow=frame["pump"]["flow_m3h"],
            kw_tr=ct["kw_per_ton"]
        )

        self.db.log_snapshot(eval_result, frame)

        now = time.time()
        if (status in ["WARNING", "CRITICAL"] or ml_alert) and (now - self.last_pdf_generated_at > 30.0):
            pdf_path = self.pdf.generate_incident_report(eval_result)
            self.last_pdf_generated_at = now
            eval_result["pdf_generated"] = pdf_path

            current_fault = chaos_state.get("active_fault")
            last_dispatched_fault = getattr(self, "_last_dispatched_fault", None)
            last_dispatch_time = getattr(self, "_last_dispatch_time", 0.0)

            # Throttle: Only dispatch if fault changed, or if status worsened to CRITICAL, or cooldown expired (60s)
            should_dispatch = False
            if current_fault and current_fault != last_dispatched_fault:
                should_dispatch = True
            elif (now - last_dispatch_time) > 60.0 and (status in ["WARNING", "CRITICAL"] or ml_alert):
                should_dispatch = True

            if should_dispatch:
                self._last_dispatched_fault = current_fault
                self._last_dispatch_time = now
                caption = f"CRITICAL TRIP: Plant Health {plant_health}/100 | Status: {status}"
                if current_fault:
                    caption = f"CHAOS INTERLOCK: {current_fault} | " + caption
                dispatch_telegram_alert(pdf_path, caption)

        return eval_result

# ==============================================================================
# SECTION 8: FASTAPI APPLICATION & DASHBOARD UI
# ==============================================================================

app = FastAPI(title="AI Equipment Intelligence SCADA")
matrix = GlobalFleetMatrix()

class ControlCommand(BaseModel):
    action: str
    value: float = 0.0

@app.post("/api/control")
async def execute_actuator_command(cmd: ControlCommand):
    global actuators
    if cmd.action == "trigger_blowdown":
        actuators.blowdown_open = True
        return {"status": "success", "message": "Manual Tower blowdown energized. Flushing basin TDS."}
    elif cmd.action == "clean_condenser":
        actuators.fouling_mitigation_active = True
        matrix.rul_engine.reset_chiller_fouling()
        return {"status": "success", "message": "Manual acid-wash flush initiated. Condenser cleared."}
    elif cmd.action == "adjust_pump_vfd":
        actuators.pump_vfd_hz = max(30.0, min(60.0, cmd.value))
        matrix.rul_engine.reset_pump_wear()
        return {"status": "success", "message": f"Pump VFD speed set to {actuators.pump_vfd_hz} Hz."}
    elif cmd.action == "toggle_agent":
        actuators.autonomous_healing_enabled = not actuators.autonomous_healing_enabled
        state = "ENABLED" if actuators.autonomous_healing_enabled else "DISABLED"
        return {"status": "success", "message": f"Autonomous Self-Healing Agent is now {state}."}
    return {"status": "ignored"}

@app.get("/api/plc-registers")
async def get_plc_registers():
    return tcp_bridge.registers

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI SCADA Fleet Command</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: monospace; }
        .card { background-color: #161b22; border: 1px solid #30363d; }
    </style>
</head>
<body class="p-6">
    <div class="max-w-7xl mx-auto space-y-6">
        <!-- Header -->
        <header class="flex justify-between items-center pb-4 border-b border-gray-800">
            <div>
                <h1 class="text-2xl font-bold text-white tracking-wider">AI EQUIPMENT INTELLIGENCE SUITE</h1>
                <p class="text-xs text-gray-400">REAL-TIME SCADA BUS, AUTONOMOUS AGENT, INDUSTRIAL TCP & STREAMLIT PORTAL</p>
            </div>
            <div class="flex items-center space-x-3">
                <span id="timestamp" class="text-sm bg-gray-800 px-3 py-1 rounded border border-gray-700">--:--:--</span>
                <span id="plant-status" class="text-sm font-bold px-3 py-1 rounded bg-green-900 text-green-300">CONNECTING...</span>
                <a href="/download-report" class="text-xs bg-blue-600 hover:bg-blue-700 text-white font-bold py-1 px-3 rounded">Export PDF</a>
            </div>
        </header>

        <!-- KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="card p-4 rounded-lg">
                <p class="text-xs text-gray-400">FLEET COMPOSITE HEALTH</p>
                <h2 id="health-index" class="text-3xl font-bold text-white mt-1">--</h2>
                <div class="w-full bg-gray-800 h-2 rounded mt-3 overflow-hidden">
                    <div id="health-bar" class="bg-green-500 h-2 transition-all duration-300" style="width: 100%"></div>
                </div>
            </div>
            <div class="card p-4 rounded-lg">
                <p class="text-xs text-gray-400">PREDICTED FLEET RUL</p>
                <h2 id="rul-hours" class="text-3xl font-bold text-emerald-400 mt-1">-- hrs</h2>
                <p id="rul-breakdown" class="text-[10px] text-gray-400 mt-1">Wear: --% | Fouling: --%</p>
            </div>
            <div class="card p-4 rounded-lg">
                <p class="text-xs text-gray-400">AUTONOMOUS HEALING</p>
                <h2 id="agent-status" class="text-xl font-bold text-indigo-400 mt-2">ACTIVE</h2>
                <p class="text-[10px] text-gray-500 mt-1">Self-mitigating physical drift</p>
            </div>
            <div class="card p-4 rounded-lg">
                <p class="text-xs text-gray-400">INDUSTRIAL TCP BRIDGE</p>
                <h2 class="text-xl font-bold text-amber-400 mt-2">PORT 5020</h2>
                <p class="text-[10px] text-gray-500 mt-1">Active JSON/Binary registers</p>
            </div>
        </div>

        <!-- Bidirectional Actuators & Agent Toggle -->
        <div class="card p-4 rounded-lg border-indigo-900/50 bg-[#111827]">
            <h3 class="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-3">SCADA Actuator Control & Agent Dispatch</h3>
            <div class="flex flex-wrap gap-4 items-center">
                <button onclick="sendCommand('trigger_blowdown')" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-xs font-bold transition">
                    Flush Tower Blowdown
                </button>
                <button onclick="sendCommand('clean_condenser')" class="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded text-xs font-bold transition">
                    Cycle Condenser Flush
                </button>
                <button onclick="sendCommand('toggle_agent')" class="px-4 py-2 bg-purple-700 hover:bg-purple-800 text-white rounded text-xs font-bold transition">
                    Toggle Auto-Healing Agent
                </button>
                <div class="flex items-center space-x-2 bg-gray-800 px-3 py-1.5 rounded border border-gray-700">
                    <span class="text-xs text-gray-300">Pump VFD (Hz):</span>
                    <button onclick="adjustVfd(-2.5)" class="px-2 py-0.5 bg-gray-700 hover:bg-gray-600 rounded text-xs font-bold">-</button>
                    <span id="vfd-display" class="text-xs font-bold text-white w-10 text-center">50.0</span>
                    <button onclick="adjustVfd(2.5)" class="px-2 py-0.5 bg-gray-700 hover:bg-gray-600 rounded text-xs font-bold">+</button>
                </div>
                <span id="action-msg" class="text-xs text-yellow-400 italic"></span>
            </div>
        </div>

        <!-- Real-Time Trend Charts -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="card p-4 rounded-lg">
                <p class="text-xs text-gray-400 font-bold mb-2">FLEET HEALTH TREND (LAST 25 CYCLES)</p>
                <div class="h-44"><canvas id="healthChart"></canvas></div>
            </div>
            <div class="card p-4 rounded-lg">
                <p class="text-xs text-gray-400 font-bold mb-2">CHILLER EFFICIENCY TREND (kW/TR)</p>
                <div class="h-44"><canvas id="efficiencyChart"></canvas></div>
            </div>
        </div>

        <!-- 4 Assets Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="card p-4 rounded-lg">
                <div class="flex justify-between items-center mb-2">
                    <span class="font-bold text-white text-sm">PUMP-101</span>
                    <span id="pump-health" class="text-xs px-2 py-0.5 rounded bg-gray-800 text-green-400 font-bold">--</span>
                </div>
                <div class="text-xs space-y-1 text-gray-300">
                    <p>Eff: <span id="pump-eff" class="text-white font-bold">--</span>%</p>
                    <p>Flow: <span id="pump-flow" class="text-white">--</span> m³/h</p>
                    <p>Vibration: <span id="pump-vib" class="text-white">--</span> mm/s</p>
                </div>
            </div>

            <div class="card p-4 rounded-lg">
                <div class="flex justify-between items-center mb-2">
                    <span class="font-bold text-white text-sm">COMPRESSOR-201</span>
                    <span id="comp-health" class="text-xs px-2 py-0.5 rounded bg-gray-800 text-green-400 font-bold">--</span>
                </div>
                <div class="text-xs space-y-1 text-gray-300">
                    <p>P-Ratio: <span id="comp-pratio" class="text-white font-bold">--</span></p>
                    <p>SpecPower: <span id="comp-power" class="text-white">--</span> kW/100CFM</p>
                    <p>Disch Temp: <span id="comp-temp" class="text-white">--</span> °C</p>
                </div>
            </div>

            <div class="card p-4 rounded-lg">
                <div class="flex justify-between items-center mb-2">
                    <span class="font-bold text-white text-sm">HEX-301</span>
                    <span id="hex-health" class="text-xs px-2 py-0.5 rounded bg-gray-800 text-green-400 font-bold">--</span>
                </div>
                <div class="text-xs space-y-1 text-gray-300">
                    <p>Thermal Duty: <span id="hex-duty" class="text-white font-bold">--</span> kW</p>
                    <p>LMTD: <span id="hex-lmtd" class="text-white">--</span> °C</p>
                    <p>Imbalance: <span id="hex-imbalance" class="text-white">--</span>%</p>
                </div>
            </div>

            <div class="card p-4 rounded-lg">
                <div class="flex justify-between items-center mb-2">
                    <span class="font-bold text-white text-sm">CHILLER-PLANT-401</span>
                    <span id="ct-health" class="text-xs px-2 py-0.5 rounded bg-gray-800 text-green-400 font-bold">--</span>
                </div>
                <div class="text-xs space-y-1 text-gray-300">
                    <p>Tonnage: <span id="ct-tons" class="text-white font-bold">--</span> TR</p>
                    <p>Spec Energy: <span id="ct-eff" class="text-white">--</span> kW/TR</p>
                    <p>Tower Approach: <span id="ct-approach" class="text-white">--</span> °C</p>
                </div>
            </div>
        </div>

        <!-- Alarm and Autonomous Action Log -->
        <div class="card p-4 rounded-lg">
            <h3 class="text-xs font-bold text-gray-400 mb-2 uppercase">Diagnostic & Autonomous Action Feed</h3>
            <div id="alarm-box" class="h-28 overflow-y-auto space-y-1 text-xs text-gray-300 border border-gray-800 p-2 rounded bg-black">
                <div class="text-gray-500">Autonomous healing agent standby...</div>
            </div>
        </div>
    </div>

    <script>
        let currentVfd = 50.0;

        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: '#21262d' }, ticks: { color: '#8b949e', font: { size: 9 } } },
                y: { grid: { color: '#21262d' }, ticks: { color: '#8b949e', font: { size: 9 } } }
            },
            plugins: { legend: { display: false } }
        };

        const healthCtx = document.getElementById('healthChart').getContext('2d');
        const healthChart = new Chart(healthCtx, {
            type: 'line',
            data: { labels: [], datasets: [{ data: [], borderColor: '#10B981', borderWidth: 2, tension: 0.3, fill: false }] },
            options: chartOptions
        });

        const effCtx = document.getElementById('efficiencyChart').getContext('2d');
        const effChart = new Chart(effCtx, {
            type: 'line',
            data: { labels: [], datasets: [{ data: [], borderColor: '#3B82F6', borderWidth: 2, tension: 0.3, fill: false }] },
            options: chartOptions
        });

        function pushChartPoint(chart, label, value, maxPoints = 25) {
            chart.data.labels.push(label);
            chart.data.datasets[0].data.push(value);
            if (chart.data.labels.length > maxPoints) {
                chart.data.labels.shift();
                chart.data.datasets[0].data.shift();
            }
            chart.update('none');
        }

        async function sendCommand(action, value = 0.0) {
            const res = await fetch('/api/control', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action, value})
            });
            const data = await res.json();
            const msgEl = document.getElementById('action-msg');
            msgEl.innerText = data.message;
            setTimeout(() => { msgEl.innerText = ''; }, 4000);
        }

        function adjustVfd(delta) {
            currentVfd = Math.max(30.0, Math.min(60.0, currentVfd + delta));
            document.getElementById('vfd-display').innerText = currentVfd.toFixed(1);
            sendCommand('adjust_pump_vfd', currentVfd);
        }

        const ws = new WebSocket(`ws://${location.host}/ws/telemetry`);
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            const frame = data.raw;
            const eval = data.evaluation;
            const diag = eval.diagnostics;

            document.getElementById('timestamp').innerText = eval.timestamp;
            document.getElementById('health-index').innerText = eval.plant_health;
            document.getElementById('health-bar').style.width = eval.plant_health + '%';
            document.getElementById('rul-hours').innerText = eval.rul.fleet_rul_hours + ' hrs';
            document.getElementById('rul-breakdown').innerText = `Wear: ${eval.rul.pump_bearing_wear_pct}% | Fouling: ${eval.rul.chiller_fouling_pct}%`;

            const statusEl = document.getElementById('plant-status');
            statusEl.innerText = eval.status;
            if(eval.status === 'OPTIMAL') {
                statusEl.className = 'text-sm font-bold px-3 py-1 rounded bg-green-900 text-green-300';
            } else if(eval.status === 'WARNING') {
                statusEl.className = 'text-sm font-bold px-3 py-1 rounded bg-yellow-900 text-yellow-300';
            } else {
                statusEl.className = 'text-sm font-bold px-3 py-1 rounded bg-red-900 text-red-300';
            }

            pushChartPoint(healthChart, eval.timestamp, eval.plant_health);
            pushChartPoint(effChart, eval.timestamp, diag.chiller_tower.kw_per_ton);

            // Asset Telemetry Mapping
            document.getElementById('pump-health').innerText = diag.pump.health_score + '/100';
            document.getElementById('pump-eff').innerText = diag.pump.efficiency_pct;
            document.getElementById('pump-flow').innerText = frame.pump.flow_m3h;
            document.getElementById('pump-vib').innerText = frame.pump.vibration_mms;

            document.getElementById('comp-health').innerText = diag.compressor.health_score + '/100';
            document.getElementById('comp-pratio').innerText = diag.compressor.pressure_ratio;
            document.getElementById('comp-power').innerText = diag.compressor.specific_power_kw_100cfm;
            document.getElementById('comp-temp').innerText = frame.compressor.discharge_temp_c;

            document.getElementById('hex-health').innerText = diag.hex.health_score + '/100';
            document.getElementById('hex-duty').innerText = diag.hex.duty_kw;
            document.getElementById('hex-lmtd').innerText = diag.hex.lmtd_c;
            document.getElementById('hex-imbalance').innerText = diag.hex.heat_imbalance_pct;

            document.getElementById('ct-health').innerText = diag.chiller_tower.health_score + '/100';
            document.getElementById('ct-tons').innerText = diag.chiller_tower.cooling_capacity_tons;
            document.getElementById('ct-eff').innerText = diag.chiller_tower.kw_per_ton;
            document.getElementById('ct-approach').innerText = diag.chiller_tower.tower_approach_c;

            // Alarm & Autonomous Action Feed
            const alarmBox = document.getElementById('alarm-box');
            alarmBox.innerHTML = '';
            
            if (eval.agent_actions && eval.agent_actions.length > 0) {
                eval.agent_actions.forEach(action => {
                    const row = document.createElement('div');
                    row.className = 'text-indigo-400 font-bold';
                    row.innerText = `[${eval.timestamp}] ⚡ ${action}`;
                    alarmBox.appendChild(row);
                });
            }

            if (eval.alarms.length > 0) {
                eval.alarms.forEach(a => {
                    const row = document.createElement('div');
                    row.className = 'text-red-400';
                    row.innerText = `[${eval.timestamp}] ▲ ${a}`;
                    alarmBox.appendChild(row);
                });
            }

            if (!eval.agent_actions?.length && !eval.alarms.length) {
                alarmBox.innerHTML = '<div class="text-green-500">Autonomous systems nominal. No corrective interventions required.</div>';
            }
        };
    </script>
</body>
</html>
"""

@app.get("/")
async def get_dashboard():
    return HTMLResponse(content=DASHBOARD_HTML)

@app.get("/download-report")
async def download_report():
    report_file = "incident_report.pdf"
    if os.path.exists(report_file):
        return FileResponse(report_file, media_type="application/pdf", filename=report_file)
    latest_rows = matrix.db.get_history(limit=1)
    if latest_rows:
        raw_frame = json.loads(latest_rows[0]["raw_json"])
        eval_data = matrix.process_frame(raw_frame)
        path = matrix.pdf.generate_incident_report(eval_data, filename=report_file)
        return FileResponse(path, media_type="application/pdf", filename=report_file)
    return HTMLResponse("<h3>No telemetry recorded yet to export.</h3>")

class ChaosInjectRequest(BaseModel):
    fault_type: str

@app.post("/api/chaos/inject")
async def api_chaos_inject(req: ChaosInjectRequest):
    fault = req.fault_type.upper()
    if fault not in ["BEARING_SEIZURE", "COMPRESSOR_SURGE", "TUBE_RUPTURE"]:
        return {"status": "error", "message": f"Unknown fault type: {fault}"}
    chaos_state["active_fault"] = fault
    # Force immediate reporting by resetting rate limiter
    matrix.last_pdf_generated_at = 0.0
    return {"status": "injected", "fault": fault}

@app.post("/api/chaos/reset")
async def api_chaos_reset():
    chaos_state["active_fault"] = None
    return {"status": "normalized", "active_fault": None}

@app.get("/api/chaos/status")
async def api_chaos_status():
    return {"active_fault": chaos_state.get("active_fault")}

# ==============================================================================
# SECTION 9: SCADA TELEMETRY GENERATOR
# ==============================================================================

async def telemetry_generator():
    tick = 0
    while True:
        tick += 1
        noise = lambda scale=0.3: float(np.random.normal(0, scale))
        
        # Check actuator overrides & agent triggers
        if actuators.blowdown_open:
            basin_tds = 750.0
            actuators.blowdown_open = False
        else:
            basin_tds = min(2400.0, 1650.0 + (tick * 25.0))

        if actuators.fouling_mitigation_active:
            fouling = 0.0
            actuators.fouling_mitigation_active = False
        else:
            fouling = min(1.5, tick * 0.25) if tick >= 4 else 0.0

        vfd_ratio = actuators.pump_vfd_hz / 50.0

        # Dynamic Chaos Engineering Overrides
        pump_vib_override = None
        pump_temp_override = None
        comp_pressure_override = None
        comp_flow_override = None
        hx_hot_out_override = None

        if chaos_state.get("active_fault") == "BEARING_SEIZURE":
            pump_vib_override = 48.6
            pump_temp_override = 142.0
        elif chaos_state.get("active_fault") == "COMPRESSOR_SURGE":
            comp_pressure_override = 9.8
            comp_flow_override = 60.0
        elif chaos_state.get("active_fault") == "TUBE_RUPTURE":
            hx_hot_out_override = 88.0

        raw_frame = {
            "timestamp": time.strftime("%H:%M:%S"),
            "pump": {
                "flow_m3h": round((118.0 * vfd_ratio) + noise(), 1),
                "head_m": round((45.0 * (vfd_ratio ** 2)) + noise(), 1),
                "power_kw": round((18.5 * (vfd_ratio ** 3)) + noise(0.1), 1),
                "vibration_mms": pump_vib_override if pump_vib_override is not None else round(2.1 + (2.6 if (tick == 7 and vfd_ratio >= 1.0) else 0) + abs(noise(0.1)), 2),
                "bearing_temp_c": pump_temp_override if pump_temp_override is not None else round(58.0 + noise(), 1)
            },
            "compressor": {
                "suction_pressure_bar": round(1.01 + noise(0.01), 2),
                "discharge_pressure_bar": comp_pressure_override if comp_pressure_override is not None else round(7.2 + noise(0.05), 2),
                "suction_temp_c": round(24.0 + noise(), 1),
                "discharge_temp_c": round(92.0 + (fouling * 10) + noise(), 1),
                "flow_cfm": comp_flow_override if comp_flow_override is not None else round(450.0 + noise(2.0), 1),
                "motor_kw": round(78.0 + noise(0.5), 1)
            },
            "heat_exchanger": {
                "hot_in_temp_c": round(85.0 + noise(), 1),
                "hot_out_temp_c": hx_hot_out_override if hx_hot_out_override is not None else round(55.0 + noise(), 1),
                "cold_in_temp_c": round(25.0 + noise(), 1),
                "cold_out_temp_c": round(48.0 + noise(), 1),
                "hot_flow_m3h": round(30.0 + noise(0.1), 1),
                "cold_flow_m3h": round(38.0 + noise(0.1), 1)
            },
            "chiller_tower": {
                "chw_supply_temp_c": round(6.7 + noise(0.1), 1),
                "chw_return_temp_c": round(12.3 + noise(0.1), 1),
                "chw_flow_rate_m3h": round(240.0 + noise(), 1),
                "compressor_kw": round(290.0 + (fouling * 30) + noise(1.0), 1),
                "cw_supply_temp_c": round(35.5 + noise(), 1),
                "cw_return_temp_c": round(29.8 + (fouling * 1.5) + noise(), 1),
                "cw_flow_rate_m3h": round(320.0 + noise(), 1),
                "ambient_wet_bulb_c": 25.0,
                "basin_tds_ppm": round(basin_tds, 0),
                "makeup_tds_ppm": 310.0
            }
        }
        yield raw_frame
        await asyncio.sleep(1.2)

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        async for raw_frame in telemetry_generator():
            eval_result = matrix.process_frame(raw_frame)
            payload = {
                "raw": raw_frame,
                "evaluation": eval_result
            }
            await websocket.send_text(json.dumps(payload))
    except WebSocketDisconnect:
        pass

# ==============================================================================
# SECTION 10: ENTRY POINT (WITH GRACEFUL SHUTDOWN HANDLER)
# ==============================================================================

async def run_servers():
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    
    print("\n" + "=" * 80)
    print("   AI EQUIPMENT INTELLIGENCE SUITE - INDUSTRIAL SCADA ARCHITECTURE")
    print("=" * 80)
    print(" • Web Dashboard: http://127.0.0.1:8000")
    print(" • Native Industrial TCP Bridge: 127.0.0.1:5020 (Holding Registers active)")
    print(" • Autonomous Healing Agent: ACTIVE (Continuous self-mitigating feedback)")
    print(" • Analytics Engine: python -m streamlit run streamlit_app.py")
    print("=" * 80)
    print("Press Ctrl+C to shut down all SCADA services gracefully.\n")

    try:
        await asyncio.gather(
            server.serve(),
            tcp_bridge.start()
        )
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        print("\n[INFO] SCADA services stopped cleanly. Databases and sockets closed.")

if __name__ == "__main__":
    try:
        asyncio.run(run_servers())
    except KeyboardInterrupt:
        pass