"""
AI Energy & Equipment Intelligence Suite
Module: PDF Diagnostic Work Order & Engineering Report Generator
"""

import io
from datetime import datetime
from fpdf import FPDF

class EngineeringReportPDF(FPDF):
    def header(self):
        self.set_fill_color(26, 28, 36)
        self.rect(0, 0, 210, 28, 'F')
        
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, 'AI ENERGY & EQUIPMENT INTELLIGENCE SUITE', ln=True, align='L')
        self.set_font('Helvetica', '', 9)
        self.cell(0, 4, 'Automated Machinery Condition & Turnaround Diagnostic Report', ln=True, align='L')
        self.ln(8)

    def footer(self):
        self.set_y(-18)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 6, f'Page {self.page_no()}/{{nb}} | ISO 10816-3 / ASME PTC 10 / TEMA Standards Verification', align='C')

def generate_pdf_report(asset_name: str, status: str, health_index: float, 
                        financial_loss: float, kpis: dict, findings: list, 
                        recommendations: list) -> bytes:
    pdf = EngineeringReportPDF(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.ln(10)

    # Metadata Strip
    pdf.set_fill_color(240, 242, 246)
    pdf.set_text_color(40, 40, 40)
    pdf.set_font('Helvetica', 'B', 10)
    
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.cell(100, 8, f" ASSET: {asset_name.upper()}", fill=True)
    pdf.cell(90, 8, f" TIMESTAMP: {timestamp_str}", fill=True, ln=True, align='R')
    pdf.ln(4)

    # Health & Financial Summary Box
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(63, 10, f"Condition: {status}", border=1, align='C')
    pdf.cell(63, 10, f"Health Index: {health_index}/100", border=1, align='C')
    pdf.cell(64, 10, f"Loss: ${financial_loss:,.2f}/yr", border=1, align='C', ln=True)
    pdf.ln(6)

    # Key Operating Telemetry
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(20, 45, 90)
    pdf.cell(0, 7, "1. Primary Thermo-Hydraulic & Operating KPIs", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(30, 30, 30)
    for key, val in kpis.items():
        pdf.cell(95, 6, f"- {key}:", border=0)
        pdf.cell(95, 6, f"{val}", border=0, ln=True)
    pdf.ln(5)

    # Diagnostic Findings
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(20, 45, 90)
    pdf.cell(0, 7, "2. Physics-Informed Diagnostic Findings", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    pdf.set_font('Helvetica', '', 9.5)
    pdf.set_text_color(30, 30, 30)
    for item in findings:
        pdf.multi_cell(0, 5, f"* {item}")
        pdf.ln(1)
    pdf.ln(4)

    # Maintenance Action Items
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(20, 45, 90)
    pdf.cell(0, 7, "3. Prescriptive Turnaround & Maintenance Work Order", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    pdf.set_font('Helvetica', '', 9.5)
    pdf.set_text_color(30, 30, 30)
    for idx, rec in enumerate(recommendations, 1):
        pdf.multi_cell(0, 5, f"{idx}. [ACTION REQUIRED] {rec}")
        pdf.ln(1)

    return bytes(pdf.output())