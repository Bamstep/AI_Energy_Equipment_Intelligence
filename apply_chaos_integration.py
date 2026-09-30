import re

with open("ai_equipment_suite.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Add requests and Telegram credentials if not already present
if "TELEGRAM_BOT_TOKEN" not in code:
    import_hook = "import uvicorn"
    telegram_header = """import uvicorn
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
"""
    code = code.replace(import_hook, telegram_header, 1)

# 2. Hook Telegram Dispatch right after PDF generation in process_frame
pdf_block_old = """            pdf_path = self.pdf.generate_incident_report(eval_result)
            self.last_pdf_generated_at = now
            eval_result["pdf_generated"] = pdf_path"""

pdf_block_new = """            pdf_path = self.pdf.generate_incident_report(eval_result)
            self.last_pdf_generated_at = now
            eval_result["pdf_generated"] = pdf_path
            caption = f"CRITICAL TRIP: Plant Health {plant_health}/100 | Status: {status}"
            if chaos_state.get("active_fault"):
                caption = f"CHAOS INTERLOCK: {chaos_state['active_fault']} | " + caption
            dispatch_telegram_alert(pdf_path, caption)"""

code = code.replace(pdf_block_old, pdf_block_new, 1)

# 3. Add Chaos Endpoints right below /download-report
endpoint_target = """    return HTMLResponse("<h3>No telemetry recorded yet to export.</h3>")"""

chaos_endpoints = """    return HTMLResponse("<h3>No telemetry recorded yet to export.</h3>")

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
    return {"active_fault": chaos_state.get("active_fault")}"""

if "/api/chaos/inject" not in code:
    code = code.replace(endpoint_target, chaos_endpoints, 1)

# 4. Inject chaos overrides in telemetry_generator
telemetry_hook = "vfd_ratio = actuators.pump_vfd_hz / 50.0"
telemetry_chaos_override = """vfd_ratio = actuators.pump_vfd_hz / 50.0

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
            hx_hot_out_override = 88.0"""

if "Dynamic Chaos Engineering Overrides" not in code:
    code = code.replace(telemetry_hook, telemetry_chaos_override, 1)

# Hook the overrides into the raw_frame dict values
code = code.replace(
    '"vibration_mms": round(2.1 + (2.6 if (tick == 7 and vfd_ratio >= 1.0) else 0) + abs(noise(0.1)), 2),',
    '"vibration_mms": pump_vib_override if pump_vib_override is not None else round(2.1 + (2.6 if (tick == 7 and vfd_ratio >= 1.0) else 0) + abs(noise(0.1)), 2),'
)
code = code.replace(
    '"bearing_temp_c": round(58.0 + noise(), 1)',
    '"bearing_temp_c": pump_temp_override if pump_temp_override is not None else round(58.0 + noise(), 1)'
)
code = code.replace(
    '"discharge_pressure_bar": round(7.2 + noise(0.05), 2),',
    '"discharge_pressure_bar": comp_pressure_override if comp_pressure_override is not None else round(7.2 + noise(0.05), 2),'
)
code = code.replace(
    '"flow_cfm": round(450.0 + noise(2.0), 1),',
    '"flow_cfm": comp_flow_override if comp_flow_override is not None else round(450.0 + noise(2.0), 1),'
)
code = code.replace(
    '"hot_out_temp_c": round(55.0 + noise(), 1),',
    '"hot_out_temp_c": hx_hot_out_override if hx_hot_out_override is not None else round(55.0 + noise(), 1),'
)

with open("ai_equipment_suite.py", "w", encoding="utf-8") as f:
    f.write(code)

print("SUCCESS: Chaos Engine & Telegram Alerting merged into ai_equipment_suite.py!")
