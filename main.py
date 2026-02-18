"""
main.py
-------
Flask backend for the Solar PV Yield Calculator.
Run this file to start the app: python main.py

Endpoints:
    GET  /              → Serves the main HTML page
    POST /api/calculate → Runs full solar calculation
    POST /api/compare   → Compares two system sizes
    GET  /api/presets   → Returns Indian city presets
    POST /api/report    → Generates downloadable PDF report
"""

from flask import Flask, render_template, request, jsonify, send_file
import io
import json
from datetime import datetime

from nasa_api import fetch_solar_irradiance
from calculator import run_full_calculation, calculate_monthly_energy, calculate_savings

# PDF generation (reportlab is free)
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import cm
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

app = Flask(__name__)

# ─── Indian City Presets ───────────────────────────────────────────────────────
INDIAN_CITY_PRESETS = {
    "Mumbai":     {"lat": 19.076,  "lon": 72.877,  "tilt": 19},
    "Delhi":      {"lat": 28.704,  "lon": 77.102,  "tilt": 29},
    "Bengaluru":  {"lat": 12.972,  "lon": 77.594,  "tilt": 13},
    "Chennai":    {"lat": 13.083,  "lon": 80.270,  "tilt": 13},
    "Kolkata":    {"lat": 22.573,  "lon": 88.364,  "tilt": 23},
    "Hyderabad":  {"lat": 17.385,  "lon": 78.487,  "tilt": 17},
    "Jaipur":     {"lat": 26.912,  "lon": 75.787,  "tilt": 27},
    "Ahmedabad":  {"lat": 23.023,  "lon": 72.572,  "tilt": 23},
    "Pune":       {"lat": 18.520,  "lon": 73.856,  "tilt": 19},
    "Bhopal":     {"lat": 23.259,  "lon": 77.413,  "tilt": 23},
}


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main calculator page."""
    return render_template("index.html")


@app.route("/api/presets", methods=["GET"])
def get_presets():
    """Return Indian city preset data."""
    return jsonify(INDIAN_CITY_PRESETS)


@app.route("/api/calculate", methods=["POST"])
def calculate():
    """
    Main calculation endpoint.
    Accepts JSON body with user inputs, fetches NASA data, returns full results.
    """
    try:
        data = request.get_json()

        # Validate required inputs
        required = ["latitude", "longitude", "capacity_kw", "efficiency",
                    "tilt_angle", "shading_loss", "electricity_rate"]
        for field in required:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        inputs = {
            "latitude":         float(data["latitude"]),
            "longitude":        float(data["longitude"]),
            "capacity_kw":      float(data["capacity_kw"]),
            "efficiency":       float(data["efficiency"]),
            "tilt_angle":       float(data["tilt_angle"]),
            "shading_loss":     float(data["shading_loss"]),
            "electricity_rate": float(data["electricity_rate"]),
            "monthly_bill":     float(data.get("monthly_bill", 2000)),
        }

        # Fetch solar irradiance from NASA POWER API
        irradiance = fetch_solar_irradiance(inputs["latitude"], inputs["longitude"])

        # Run all calculations
        results = run_full_calculation(inputs, irradiance)
        results["inputs"] = inputs

        return jsonify({"success": True, "data": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/compare", methods=["POST"])
def compare():
    """
    Compare two solar system sizes side-by-side.
    Expects: same inputs but with capacity_kw_1 and capacity_kw_2.
    """
    try:
        data = request.get_json()
        lat  = float(data["latitude"])
        lon  = float(data["longitude"])
        eff  = float(data["efficiency"])
        tilt = float(data["tilt_angle"])
        shad = float(data["shading_loss"])
        rate = float(data["electricity_rate"])
        kw1  = float(data["capacity_kw_1"])
        kw2  = float(data["capacity_kw_2"])

        irradiance = fetch_solar_irradiance(lat, lon)

        def build_summary(capacity_kw):
            energy  = calculate_monthly_energy(irradiance, capacity_kw, eff, tilt, shad, lat)
            savings = calculate_savings(energy, rate)
            yearly_kwh = round(sum(energy), 2)
            yearly_inr = round(sum(savings), 2)
            return {
                "capacity_kw":   capacity_kw,
                "yearly_kwh":    yearly_kwh,
                "yearly_savings":yearly_inr,
                "monthly_energy":energy,
                "monthly_savings":savings,
                "install_cost":  round(capacity_kw * 50000, 0),
                "payback_years": round((capacity_kw * 50000) / yearly_inr, 1) if yearly_inr > 0 else None
            }

        return jsonify({
            "success": True,
            "system1": build_summary(kw1),
            "system2": build_summary(kw2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/report", methods=["POST"])
def generate_report():
    """Generate and return a downloadable PDF report."""
    if not PDF_AVAILABLE:
        return jsonify({"error": "PDF library not installed. Run: pip install reportlab"}), 500

    try:
        data = request.get_json()
        results = data.get("results", {})
        inputs  = data.get("inputs", {})

        buffer = io.BytesIO()
        doc    = SimpleDocTemplate(buffer, pagesize=A4,
                                   rightMargin=2*cm, leftMargin=2*cm,
                                   topMargin=2*cm,  bottomMargin=2*cm)

        styles  = getSampleStyleSheet()
        story   = []

        # Title
        title_style = ParagraphStyle("Title", parent=styles["Title"],
                                     fontSize=20, textColor=colors.HexColor("#f97316"),
                                     spaceAfter=6)
        story.append(Paragraph("☀ Solar PV Yield Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
                                styles["Normal"]))
        story.append(Spacer(1, 0.4*cm))

        # System Details
        story.append(Paragraph("System Details", styles["Heading2"]))
        sys_data = [
            ["Parameter", "Value"],
            ["Location (Lat, Lon)", f"{inputs.get('latitude','')}, {inputs.get('longitude','')}"],
            ["System Capacity",     f"{inputs.get('capacity_kw','')} kW"],
            ["Panel Efficiency",    f"{inputs.get('efficiency','')}%"],
            ["Tilt Angle",          f"{inputs.get('tilt_angle','')}°"],
            ["Shading Loss",        f"{inputs.get('shading_loss','')}%"],
            ["Electricity Rate",    f"₹{inputs.get('electricity_rate','')}/kWh"],
        ]
        t = Table(sys_data, colWidths=[8*cm, 8*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#f97316")),
            ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#fff7ed")]),
            ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#fed7aa")),
            ("FONTSIZE",    (0,0), (-1,-1), 10),
            ("PADDING",     (0,0), (-1,-1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))

        # Energy Output
        story.append(Paragraph("Energy Output", styles["Heading2"]))
        yearly = results.get("yearly", {})
        daily  = results.get("daily",  {})
        energy_data = [
            ["Metric", "Value"],
            ["Daily Energy",   f"{daily.get('energy_kwh',0)} kWh"],
            ["Yearly Energy",  f"{yearly.get('energy_kwh',0)} kWh"],
            ["Yearly Savings", f"₹{yearly.get('savings_inr',0):,}"],
            ["CO₂ Reduction",  f"{yearly.get('co2_kg',0)} kg/year"],
            ["Trees Equivalent", f"{yearly.get('trees_equiv',0)} trees"],
        ]
        t2 = Table(energy_data, colWidths=[8*cm, 8*cm])
        t2.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#16a34a")),
            ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f0fdf4")]),
            ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#bbf7d0")),
            ("FONTSIZE",    (0,0), (-1,-1), 10),
            ("PADDING",     (0,0), (-1,-1), 6),
        ]))
        story.append(t2)
        story.append(Spacer(1, 0.5*cm))

        # ROI
        story.append(Paragraph("Return on Investment", styles["Heading2"]))
        roi = results.get("roi", {})
        roi_data = [
            ["Metric", "Value"],
            ["Installation Cost",    f"₹{int(roi.get('total_cost',0)):,}"],
            ["Payback Period",       f"{roi.get('payback_years','N/A')} years"],
            ["25-Year Total Savings",f"₹{int(roi.get('total_25yr_savings',0)):,}"],
            ["25-Year ROI",          f"{roi.get('roi_25yr','N/A')}%"],
        ]
        t3 = Table(roi_data, colWidths=[8*cm, 8*cm])
        t3.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#7c3aed")),
            ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#faf5ff")]),
            ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#ddd6fe")),
            ("FONTSIZE",    (0,0), (-1,-1), 10),
            ("PADDING",     (0,0), (-1,-1), 6),
        ]))
        story.append(t3)
        story.append(Spacer(1, 0.5*cm))

        # Monthly Table
        story.append(Paragraph("Monthly Breakdown", styles["Heading2"]))
        monthly = results.get("monthly", {})
        month_rows = [["Month", "Energy (kWh)", "Savings (₹)", "CO₂ Saved (kg)"]]
        for i, name in enumerate(monthly.get("names", [])):
            month_rows.append([
                name,
                str(monthly["energy"][i]),
                f"₹{monthly['savings'][i]:,}",
                str(monthly["co2"][i])
            ])
        t4 = Table(month_rows, colWidths=[3*cm, 4*cm, 4.5*cm, 4.5*cm])
        t4.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#0369a1")),
            ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f0f9ff")]),
            ("GRID",        (0,0), (-1,-1), 0.5, colors.HexColor("#bae6fd")),
            ("FONTSIZE",    (0,0), (-1,-1), 9),
            ("PADDING",     (0,0), (-1,-1), 5),
        ]))
        story.append(t4)

        # Footer
        story.append(Spacer(1, 0.8*cm))
        story.append(Paragraph(
            "⚡ Generated by Solar PV Yield Calculator | Data source: NASA POWER API",
            ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8,
                           textColor=colors.grey)
        ))

        doc.build(story)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name="solar_pv_report.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # host="0.0.0.0" is required for Replit to expose a public URL
    app.run(host="0.0.0.0", port=8080, debug=False)
