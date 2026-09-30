import os
import io
import time
import requests
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

app = FastAPI(title="Chaos & Incident Management Engine")

# Telegram Bot Credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8995918478:AAHA3nAELY0ejJ3fJP58qD2tKOtatgv_qoY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8049623204")

system_state = {
    "health_status": "NORMAL",
    "vibration_rms": 2.1,
    "bearing_temp": 64.0,
    "pressure_differential": 1.2,
    "flow_rate": 450.0,
    "emergency_shutdown_active": False,
    "last_fault": None
}

class FaultRequest(BaseModel):
    fault_type: str

def generate_pdf_report(fault_type: str, state_snapshot: dict) -> bytes:
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Red Header Banner
    p.setFillColor(colors.HexColor("#B71C1C"))
    p.rect(0, height - 70, width, 70, fill=1, stroke=0)
    
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, height - 42, "CRITICAL INCIDENT: EMERGENCY TRIP REPORT")

    # Metadata
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, height - 100, f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    p.drawString(40, height - 120, f"Injected Failure: {fault_type}")
    p.drawString(40, height - 140, "Automation Response: EMERGENCY SHUTDOWN TRIGGERED")

    p.drawString(40, height - 175, "Final Telemetry Snapshot Prior to Interlock:")

    # Metrics
    p.setFont("Helvetica", 10)
    y = height - 200
    for key, value in state_snapshot.items():
        p.drawString(60, y, f"- {key}: {value}")
        y -= 20

    p.save()
    buffer.seek(0)
    return buffer.getvalue()

def dispatch_telegram_alert(pdf_bytes: bytes, caption: str):
    print("Initiating Telegram alert dispatch...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    files = {"document": ("incident_report.pdf", pdf_bytes, "application/pdf")}
    data = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption}
    try:
        res = requests.post(url, data=data, files=files, timeout=15)
        print(f"Telegram response: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Telegram dispatch failed: {e}")

def trigger_emergency_shutdown(fault_name: str, background_tasks: BackgroundTasks):
    system_state["health_status"] = "CRITICAL"
    system_state["emergency_shutdown_active"] = True
    system_state["last_fault"] = fault_name

    pdf_data = generate_pdf_report(fault_name, system_state.copy())
    with open("incident_report.pdf", "wb") as f:
        f.write(pdf_data)

    caption = f"CRITICAL INTERLOCK TRIP: {fault_name}"
    background_tasks.add_task(dispatch_telegram_alert, pdf_data, caption)

@app.get("/api/incident/report")
def download_report():
    pdf_path = "incident_report.pdf"
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="No incident report has been generated yet.")
    return FileResponse(pdf_path, media_type="application/pdf", filename="incident_report.pdf")

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
      <title>Plant Chaos Engineering Panel</title>
      <style>
        body { background: #0b0c10; color: #fff; font-family: sans-serif; display: flex; justify-content: center; padding: 50px 20px; }
        .panel { padding: 24px; background: #121212; border-radius: 8px; max-width: 600px; width: 100%; border: 1px solid #222; }
        .status-box { margin-bottom: 16px; padding: 12px; background: #1e1e1e; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        button { padding: 12px; border: none; border-radius: 4px; color: #fff; font-weight: bold; cursor: pointer; }
        .red { background: #d32f2f; }
        .pink { background: #c2185b; }
        .purple { background: #7b1fa2; }
        .green { background: #388e3c; }
        .download-btn { background: #ff9800; color: #000; text-decoration: none; padding: 8px 14px; border-radius: 4px; font-weight: bold; display: none; }
        pre { background: #000; padding: 10px; border-radius: 4px; font-size: 13px; color: #64ffda; }
      </style>
    </head>
    <body>
      <div class="panel">
        <h2 style="color: #f44336; margin-top: 0;">Chaos Testing & Fault Injection</h2>
        <div class="status-box">
          <div>
            <strong>Status: </strong><span id="status">SYSTEM NOMINAL</span>
          </div>
          <a id="pdf-link" class="download-btn" href="/api/incident/report" target="_blank">View PDF Report</a>
        </div>
        <div class="grid">
          <button class="red" onclick="inject('BEARING_SEIZURE')">Inject Bearing Seizure</button>
          <button class="pink" onclick="inject('TUBE_RUPTURE')">Inject Tube Rupture</button>
          <button class="purple" onclick="inject('COMPRESSOR_SURGE')">Inject Compressor Surge</button>
          <button class="green" onclick="resetSys()">Normalize & Reset ESD</button>
        </div>
        <h4>Live Telemetry:</h4>
        <pre id="telemetry">Loading telemetry...</pre>
      </div>
      <script>
        function updateStatus(data) {
          const isCritical = data.telemetry.health_status === 'CRITICAL';
          const statusElem = document.getElementById('status');
          const pdfLink = document.getElementById('pdf-link');
          
          statusElem.innerText = isCritical ? 'CRITICAL - ESD ACTIVATED' : 'SYSTEM NOMINAL';
          statusElem.style.color = isCritical ? '#f44336' : '#4caf50';
          pdfLink.href = '/api/incident/report?t=' + new Date().getTime();
          pdfLink.style.display = isCritical ? 'inline-block' : 'none';
          document.getElementById('telemetry').innerText = JSON.stringify(data.telemetry, null, 2);
        }
        async function inject(type) {
          if (!confirm('Inject catastrophic fault: ' + type + '?')) return;
          const res = await fetch('/api/chaos/inject', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({fault_type: type})
          });
          const data = await res.json();
          updateStatus(data);
        }
        async function resetSys() {
          const res = await fetch('/api/chaos/reset', { method: 'POST' });
          const data = await res.json();
          updateStatus(data);
        }
        resetSys();
      </script>
    </body>
    </html>
    """

@app.post("/api/chaos/inject")
def inject_fault(fault: FaultRequest, background_tasks: BackgroundTasks):
    ft = fault.fault_type.upper()

    if ft == "BEARING_SEIZURE":
        system_state["vibration_rms"] = 48.6
        system_state["bearing_temp"] = 142.0
        trigger_emergency_shutdown("Sudden Bearing Seizure", background_tasks)
    elif ft == "TUBE_RUPTURE":
        system_state["pressure_differential"] = 0.05
        system_state["flow_rate"] = 890.0
        trigger_emergency_shutdown("Primary Tube Rupture", background_tasks)
    elif ft == "COMPRESSOR_SURGE":
        system_state["flow_rate"] = 85.0
        system_state["pressure_differential"] = 4.8
        system_state["vibration_rms"] = 32.0
        trigger_emergency_shutdown("Compressor Surge & Aerodynamic Stall", background_tasks)
    else:
        raise HTTPException(status_code=400, detail="Invalid fault type specified.")

    return {
        "status": "Fault Injected",
        "action_taken": "Automated ESD Trip Activated",
        "telemetry": system_state
    }

@app.post("/api/chaos/reset")
def reset_system():
    system_state.update({
        "health_status": "NORMAL",
        "vibration_rms": 2.1,
        "bearing_temp": 64.0,
        "pressure_differential": 1.2,
        "flow_rate": 450.0,
        "emergency_shutdown_active": False,
        "last_fault": None
    })
    return {"status": "System normalized", "telemetry": system_state}
