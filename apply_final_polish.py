with open("ai_equipment_suite.py", "r", encoding="utf-8") as f:
    code = f.read()

# 1. Smarter dispatch throttling: only send on NEW state transition or if 60s have elapsed
old_dispatch_hook = """            pdf_path = self.pdf.generate_incident_report(eval_result)
            self.last_pdf_generated_at = now
            eval_result["pdf_generated"] = pdf_path
            caption = f"CRITICAL TRIP: Plant Health {plant_health}/100 | Status: {status}"
            if chaos_state.get("active_fault"):
                caption = f"CHAOS INTERLOCK: {chaos_state['active_fault']} | " + caption
            dispatch_telegram_alert(pdf_path, caption)"""

new_dispatch_hook = """            pdf_path = self.pdf.generate_incident_report(eval_result)
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
                dispatch_telegram_alert(pdf_path, caption)"""

if old_dispatch_hook in code:
    code = code.replace(old_dispatch_hook, new_dispatch_hook)

# 2. Add Native Chaos Action Buttons into the HTML UI
html_target = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">'
chaos_ui_banner = """<!-- CHAOS CONTROL CONSOLE -->
        <div class="bg-gray-800 border border-red-900/60 rounded-xl p-5 mb-8 shadow-lg">
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center space-x-3">
                    <span class="inline-block w-3 h-3 rounded-full bg-red-500 animate-pulse"></span>
                    <h2 class="text-lg font-bold text-red-400 uppercase tracking-wide">Chaos Injection & ESD Simulation</h2>
                </div>
                <button onclick="resetChaos()" class="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-4 py-2 rounded shadow transition">
                    RESET ESD / NORMALIZE
                </button>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <button onclick="injectChaos('BEARING_SEIZURE')" class="bg-red-950/80 hover:bg-red-800 border border-red-700/60 text-red-200 px-4 py-3 rounded-lg font-mono text-sm text-left transition flex items-center justify-between">
                    <span>Bearing Seizure (Pump)</span>
                    <span class="text-xs bg-red-800 px-2 py-0.5 rounded text-white">48.6 mm/s</span>
                </button>
                <button onclick="injectChaos('COMPRESSOR_SURGE')" class="bg-amber-950/80 hover:bg-amber-800 border border-amber-700/60 text-amber-200 px-4 py-3 rounded-lg font-mono text-sm text-left transition flex items-center justify-between">
                    <span>Compressor Surge</span>
                    <span class="text-xs bg-amber-800 px-2 py-0.5 rounded text-white">9.8 bar</span>
                </button>
                <button onclick="injectChaos('TUBE_RUPTURE')" class="bg-purple-950/80 hover:bg-purple-800 border border-purple-700/60 text-purple-200 px-4 py-3 rounded-lg font-mono text-sm text-left transition flex items-center justify-between">
                    <span>HX Tube Rupture</span>
                    <span class="text-xs bg-purple-800 px-2 py-0.5 rounded text-white">Excursion</span>
                </button>
            </div>
        </div>

        <script>
            async function injectChaos(faultType) {
                try {
                    await fetch('/api/chaos/inject', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({fault_type: faultType})
                    });
                } catch(e) { console.error(e); }
            }
            async function resetChaos() {
                try {
                    await fetch('/api/chaos/reset', {method: 'POST'});
                } catch(e) { console.error(e); }
            }
        </script>
        <!-- /CHAOS CONTROL CONSOLE -->

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">"""

if 'CHAOS CONTROL CONSOLE' not in code and html_target in code:
    code = code.replace(html_target, chaos_ui_banner, 1)

with open("ai_equipment_suite.py", "w", encoding="utf-8") as f:
    f.write(code)

print("SUCCESS: Throttling & Dashboard Controls applied.")
