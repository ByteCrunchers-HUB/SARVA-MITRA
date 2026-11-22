"""PDF Report Generator for Sarva Mitra.
Generates an official agronomic field report incorporating:
- Sarva Mitra vector logo (logo.svg) or fallback logo
- Farm location, crop, and growth stage metadata
- Live IoT telemetry readings table
- Machine learning weather risk evaluation
- Comprehensive agronomic advisory & inspection guidance
- Document citations and agricultural advisory disclaimers
"""
from __future__ import annotations

import io
from datetime import datetime, timezone, timedelta
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

IST = timezone(timedelta(hours=5, minutes=30))


def generate_advisory_pdf(
    farm_config: dict,
    telemetry: dict,
    ml_prediction: dict,
    advisory_text: str,
    logo_path: Path | str | None = None,
) -> bytes:
    """Generates a professional PDF report and returns raw bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1b4d3e"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#4a6352"),
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e3d2f"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#222222"),
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
    )
    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=table_cell,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#153628"),
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Italic"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#666666"),
    )

    story = []

    # 1. Header with Logo & Title
    logo_flowable = None
    if logo_path:
        p = Path(logo_path)
        if p.suffix.lower() == ".svg" and p.exists():
            try:
                from svglib.svglib import svg2rlg

                drawing = svg2rlg(str(p))
                if drawing:
                    target_w = 170.0
                    factor = target_w / float(drawing.width)
                    drawing.width = target_w
                    drawing.height = float(drawing.height) * factor
                    drawing.scale(factor, factor)
                    logo_flowable = drawing
            except Exception:
                logo_flowable = None
        if not logo_flowable:
            jpg_alt = p.parent / "logo.jpg"
            if jpg_alt.exists():
                try:
                    logo_flowable = Image(str(jpg_alt), width=150, height=45)
                except Exception:
                    pass

    header_text = [
        Paragraph("<b>SARVA MITRA — UNIVERSAL FARM COMPANION</b>", title_style),
        Paragraph(
            "Official Farm Telemetry, ML Pathogen Risk & Agronomic Advisory Report<br/>"
            f"<i>Report Issued: {datetime.now(IST).strftime('%d %B %Y, %I:%M %p IST')}</i>",
            subtitle_style,
        ),
    ]

    if logo_flowable:
        header_table = Table(
            [[logo_flowable, header_text]],
            colWidths=[180, 350],
        )
        header_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        story.append(header_table)
    else:
        for item in header_text:
            story.append(item)

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2e7d32"), spaceBefore=2, spaceAfter=8))

    # 2. Farm Context Banner
    loc_name = farm_config.get("name", "Farm Location")
    lat = farm_config.get("lat", 16.51)
    lon = farm_config.get("lon", 80.52)
    crop = farm_config.get("crop", "Tomato").title()
    stage = farm_config.get("stage", "Flowering Stage")

    context_data = [
        [
            Paragraph("<b>Target Farm / Region:</b>", table_cell_bold),
            Paragraph(f"{loc_name} ({lat:.4f}° N, {lon:.4f}° E)", table_cell),
            Paragraph("<b>Monitored Crop:</b>", table_cell_bold),
            Paragraph(f"{crop}", table_cell),
        ],
        [
            Paragraph("<b>Growth Stage:</b>", table_cell_bold),
            Paragraph(f"{stage}", table_cell),
            Paragraph("<b>Telemetry Source:</b>", table_cell_bold),
            Paragraph(f"{telemetry.get('source', 'Virtual Weather & Soil Station')}", table_cell),
        ],
    ]
    context_table = Table(context_data, colWidths=[120, 150, 110, 150])
    context_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f7f2")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#c8decb")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0ede2")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(context_table)
    story.append(Spacer(1, 10))

    # 3. Live Telemetry & ML Risk Section
    story.append(Paragraph("1. Real-Time Telemetry & AI Pathogen Risk", section_heading))

    risk_info = (ml_prediction or {}).get("prediction", {})
    risk_pct = risk_info.get("risk_pct", 0.0)
    risk_level = (risk_info.get("risk_level") or risk_info.get("risk_label", "low")).upper()

    risk_bg = "#e8f5e9" if risk_level == "LOW" else ("#fff8e1" if risk_level == "MODERATE" else "#ffebee")
    risk_color = "#2e7d32" if risk_level == "LOW" else ("#f57f17" if risk_level == "MODERATE" else "#c62828")

    telemetry_rows = [
        [
            Paragraph("<b>Sensor Parameter</b>", table_cell_bold),
            Paragraph("<b>Live Reading</b>", table_cell_bold),
            Paragraph("<b>Reference Band</b>", table_cell_bold),
            Paragraph("<b>Status Note</b>", table_cell_bold),
        ],
        [
            Paragraph("Ambient Air Temperature", table_cell),
            Paragraph(f"{telemetry.get('temperature_c', 0.0):.1f} °C", table_cell),
            Paragraph("20.0 – 30.0 °C", table_cell),
            Paragraph("Field canopy level", table_cell),
        ],
        [
            Paragraph("Relative Atmospheric Humidity", table_cell),
            Paragraph(f"{telemetry.get('humidity_pct', 0.0):.1f} %", table_cell),
            Paragraph("50.0 – 75.0 %", table_cell),
            Paragraph("High moisture favors spore growth" if telemetry.get("humidity_pct", 0.0) > 75 else "Optimal band", table_cell),
        ],
        [
            Paragraph("Volumetric Soil Moisture", table_cell),
            Paragraph(f"{telemetry.get('soil_moisture_pct', 0.0):.1f} %", table_cell),
            Paragraph("18.0 – 28.0 %", table_cell),
            Paragraph("Adequate root zone moisture", table_cell),
        ],
        [
            Paragraph("Accumulated Daily Rainfall", table_cell),
            Paragraph(f"{telemetry.get('rainfall_mm', 0.0):.1f} mm", table_cell),
            Paragraph("—", table_cell),
            Paragraph("Precipitation gauge", table_cell),
        ],
        [
            Paragraph("Solar Irradiance", table_cell),
            Paragraph(f"{telemetry.get('sunlight_wm2', 0.0):.0f} W/m²", table_cell),
            Paragraph("0 – 1000 W/m²", table_cell),
            Paragraph("Downward shortwave flux", table_cell),
        ],
    ]
    tel_table = Table(telemetry_rows, colWidths=[150, 90, 110, 180])
    tel_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2efe5")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0e2d3")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(tel_table)
    story.append(Spacer(1, 8))

    # ML Risk Badge Box
    risk_box_data = [
        [
            Paragraph(f"<b>ML Weather Risk Evaluation:</b> <font color='{risk_color}'><b>{risk_pct}% ({risk_level})</b></font>", table_cell_bold),
            Paragraph(
                f"Model: {ml_prediction.get('model', {}).get('name', 'Trained Ensemble')} | "
                f"Action Signal: {'1 (Active)' if risk_level in {'MODERATE', 'HIGH'} else '0 (Normal)'}",
                table_cell,
            ),
        ]
    ]
    risk_box = Table(risk_box_data, colWidths=[240, 290])
    risk_box.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(risk_bg)),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(risk_color)),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(risk_box)
    story.append(Spacer(1, 10))

    # 4. Expert Agronomic Advisory
    story.append(Paragraph("2. Expert Field Diagnostic & Advisory", section_heading))

    # Clean advisory text for reportlab paragraph rendering
    clean_text = advisory_text
    # Remove BEGIN_STRUCTURED_JSON blocks if any
    import re
    clean_text = re.sub(r"BEGIN_STRUCTURED_JSON[\s\S]*?END_STRUCTURED_JSON", "", clean_text).strip()
    clean_text = re.sub(r"```json[\s\S]*?```", "", clean_text).strip()

    # Split into sections/lines and format
    lines = clean_text.split("\n")
    for line in lines:
        line_s = line.strip()
        if not line_s:
            story.append(Spacer(1, 4))
            continue
        # Convert markdown headers
        if line_s.startswith("### "):
            story.append(Paragraph(f"<b>{line_s[4:]}</b>", ParagraphStyle("H3", parent=section_heading, fontSize=10.5, spaceBefore=6, spaceAfter=3)))
        elif line_s.startswith("## "):
            story.append(Paragraph(f"<b>{line_s[3:]}</b>", ParagraphStyle("H2", parent=section_heading, fontSize=11, spaceBefore=8, spaceAfter=4)))
        elif line_s.startswith("# "):
            story.append(Paragraph(f"<b>{line_s[2:]}</b>", section_heading))
        elif line_s.startswith("- ") or line_s.startswith("* "):
            bullet_text = line_s[2:]
            bullet_text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", bullet_text)
            bullet_text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", bullet_text)
            story.append(Paragraph(f"• {bullet_text}", body_style))
        elif re.match(r"^\d+\.\s+", line_s):
            num_text = re.sub(r"^\d+\.\s+", "", line_s)
            num_text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", num_text)
            num_text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", num_text)
            story.append(Paragraph(f"<b>{line_s[:3]}</b> {num_text}", body_style))
        else:
            fmt_line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", line_s)
            fmt_line = re.sub(r"\*(.*?)\*", r"<i>\1</i>", fmt_line)
            story.append(Paragraph(fmt_line, body_style))

    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#cccccc"), spaceBefore=6, spaceAfter=6))

    # 5. Agricultural Notice & Disclaimer
    disclaimer = (
        "<b>OFFICIAL NOTICE & AGRONOMIC DISCLAIMER:</b> "
        "Sarva Mitra telemetry sensors monitor microclimate pathogen risk patterns and do not substitute for certified "
        "laboratory testing or visual inspection. Specific chemical pesticide brand names, spray schedules, and high-potency "
        "dosing are restricted to authorized Agricultural Officers. Farmers are advised to consult their nearest Krishi Vigyan "
        "Kendra (KVK) or local Agricultural Extension Department before applying synthetic agrochemicals."
    )
    story.append(Paragraph(disclaimer, disclaimer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
