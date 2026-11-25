"""PDF Report Generator for Sarva Mitra.
Generates an official agronomic field report incorporating:
- Sarva Mitra crisp official emblem (icon.png/logo)
- Farm location, crop, and growth stage metadata (sanitized of emojis/tofu)
- Live IoT telemetry readings table
- Machine learning weather risk evaluation
- Comprehensive agronomic advisory & inspection guidance with fully parsed Markdown tables
- Document citations and agricultural advisory disclaimers
"""
from __future__ import annotations

import io
import re
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

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
    "\U00002702-\U000027B0"  # dingbats
    "\U000024C2-\U0001F251"  # enclosed characters
    "\U0001F004-\U0001F0CF"  # various symbols
    "\U00002600-\U000026FF"  # misc symbols (sun, cloud, warning, etc.)
    "\U00002300-\U000023FF"  # misc technical (hourglass, etc.)
    "\U00002B50-\U00002B55"  # star symbols
    "]+",
    flags=re.UNICODE,
)

CHAR_REPLACEMENTS = {
    "\u2011": "-",
    "\u2010": "-",
    "\u2012": "-",
    "\u2013": "-",
    "\u2014": " - ",
    "\u2015": " - ",
    "\u00ad": "",
    "\u00a0": " ",
    "\u200b": "",
    "\u2009": " ",
    "\u202f": " ",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2026": "...",
    "\u00b2": "2",
    "\u00b3": "3",
    "\u00b0": " deg",
    "\u2103": " C",
    "\u25a0": "-",
    "■": "-",
    "▪": "-",
    "▫": "-",
    "●": "*",
    "○": "*",
    "◆": "*",
    "◇": "*",
    "✔": "[OK]",
    "✔️": "[OK]",
    "✅": "[OK]",
    "❌": "[X]",
    "⚠️": "[!]",
    "💡": "*",
    "🔍": "*",
    "📄": "*",
    "🌸": "",
    "🍅": "",
    "🌶️": "",
    "🌾": "",
    "🌿": "",
    "→": "->",
    "←": "<-",
    "\ufe0f": "",
    "\ufe0e": "",
}


def sanitize_for_pdf(text: str) -> str:
    """Strips emojis and normalizes non-Latin punctuation/hyphens that cause black squares (■)."""
    if not text:
        return ""
    text = re.sub(r"W\s*m[■\^]?2", "W/m2", text)
    text = re.sub(r"W/m[■\^]?2", "W/m2", text)
    for orig, rep in CHAR_REPLACEMENTS.items():
        text = text.replace(orig, rep)
    text = EMOJI_PATTERN.sub("", text)

    # Filter unprintable characters for Helvetica (strictly ASCII 32-126 + newline/tab and &bull;)
    cleaned = []
    for char in text:
        code = ord(char)
        if code in (9, 10, 13) or 32 <= code <= 126:
            cleaned.append(char)
        elif char == "•":
            cleaned.append("&bull;")
        else:
            cleaned.append(" ")
    return "".join(cleaned).strip()


def format_inline_markup(line: str) -> str:
    """Escapes raw XML and converts markdown **bold** and *italic* into valid ReportLab tags."""
    if not line:
        return ""
    # Normalize unclosed <br> tags to valid XML <br/>
    line = re.sub(r"<br\s*/?>", "<br/>", line, flags=re.IGNORECASE)
    # Escape raw ampersands not part of valid HTML entities
    line = re.sub(r"&(?!([a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);)", "&amp;", line)
    # Convert bold and italic markdown to ReportLab tags
    line = re.sub(r"\*\*\*(.*?)\*\*\*", r"<b><i>\1</i></b>", line)
    line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", line)
    line = re.sub(r"\*(.*?)\*", r"<i>\1</i>", line)
    line = re.sub(r"___(.*?)___", r"<b><i>\1</i></b>", line)
    line = re.sub(r"__(.*?)__", r"<b>\1</b>", line)
    line = re.sub(r"`(.*?)`", r"<font face='Courier'>\1</font>", line)

    # Protect allowed tags: <b>, </b>, <i>, </i>, <br/>, <font ...>, </font>
    parts = re.split(r"(</?[bi]>|<br/>|</?font[^>]*>)", line)
    escaped_parts = []
    for p in parts:
        if re.match(r"^</?[bi]>$|^<br/>$|^</?font[^>]*>$", p):
            escaped_parts.append(p)
        else:
            p = p.replace("<", "&lt;").replace(">", "&gt;")
            escaped_parts.append(p)
    return "".join(escaped_parts)


def parse_markdown_table(
    table_lines: list[str],
    header_style: ParagraphStyle,
    cell_style: ParagraphStyle,
) -> Table | None:
    """Parses raw markdown table lines into a styled ReportLab Table Flowable."""
    if not table_lines:
        return None

    rows = []
    for line in table_lines:
        line_s = line.strip()
        if not line_s or line_s.count("|") < 1:
            continue
        cells = [c.strip() for c in line_s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        if not cells:
            continue
        # Skip delimiter row like |---|---| or |:---|:---|
        if all(re.match(r"^:?-+:?$", c.strip()) for c in cells if c.strip()):
            continue
        rows.append(cells)

    if not rows:
        return None

    num_cols = max(len(r) for r in rows)
    for r in rows:
        while len(r) < num_cols:
            r.append("")

    PAGE_WIDTH = 532.0
    if num_cols == 5:
        col_widths = [36.0, 110.0, 150.0, 136.0, 100.0]
    elif num_cols == 4:
        col_widths = [50.0, 140.0, 182.0, 160.0]
    elif num_cols == 3:
        col_widths = [140.0, 262.0, 130.0]
    elif num_cols == 2:
        col_widths = [180.0, 352.0]
    else:
        col_widths = [PAGE_WIDTH / num_cols] * num_cols

    table_data = []
    for r_idx, row in enumerate(rows):
        row_cells = []
        is_header = r_idx == 0
        style = header_style if is_header else cell_style
        for cell in row:
            clean_cell = sanitize_for_pdf(cell)
            formatted_cell = format_inline_markup(clean_cell)
            if is_header and not formatted_cell.startswith("<b>"):
                formatted_cell = f"<b>{formatted_cell}</b>"
            row_cells.append(Paragraph(formatted_cell, style))
        table_data.append(row_cells)

    rl_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    rl_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2efe5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#153628")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fbf9")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c8decb")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    return rl_table


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
        fontSize=17,
        leading=21,
        textColor=colors.HexColor("#1b4d3e"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#4a6352"),
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        textColor=colors.HexColor("#1e3d2f"),
        spaceBefore=10,
        spaceAfter=5,
    )
    h2_style = ParagraphStyle(
        "H2Heading",
        parent=section_heading,
        fontSize=10.5,
        leading=14,
        spaceBefore=8,
        spaceAfter=4,
    )
    h3_style = ParagraphStyle(
        "H3Heading",
        parent=section_heading,
        fontSize=9.5,
        leading=13,
        spaceBefore=6,
        spaceAfter=3,
        textColor=colors.HexColor("#2e7d32"),
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#222222"),
        spaceAfter=3,
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
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
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor("#666666"),
    )

    story = []

    # 1. Header with Logo & Brand Title
    logo_flowable = None
    assets_dir = Path(__file__).resolve().parent / "assets"
    report_svg = assets_dir / "logo-report.svg"
    emblem_png = assets_dir / "logo-emblem.png"

    # Prioritize clean report vector logo (no unmapped tofu glyphs) or antialiased rounded emblem
    target_path = Path(logo_path) if logo_path else report_svg
    # Force use of logo-report.svg if logo.svg is passed to eliminate Telugu font tofu squares
    if target_path.name == "logo.svg" and report_svg.exists():
        target_path = report_svg
    if not target_path.exists():
        target_path = report_svg if report_svg.exists() else emblem_png

    if target_path.exists():
        if target_path.suffix.lower() == ".svg":
            try:
                from svglib.svglib import svg2rlg

                drawing = svg2rlg(str(target_path))
                if drawing:
                    target_w = 190.0
                    factor = target_w / float(drawing.width)
                    drawing.width = target_w
                    drawing.height = float(drawing.height) * factor
                    drawing.scale(factor, factor)
                    logo_flowable = drawing
            except Exception:
                logo_flowable = None
        elif target_path.suffix.lower() in (".png", ".jpg", ".jpeg"):
            try:
                logo_flowable = Image(str(target_path), width=44, height=44)
            except Exception:
                logo_flowable = None

    if not logo_flowable and emblem_png.exists():
        try:
            logo_flowable = Image(str(emblem_png), width=44, height=44)
        except Exception:
            logo_flowable = None

    header_text = [
        Paragraph("<font color='#2E6B4F' size='14'><b>SARVA MITRA</b></font> <font color='#3C4641' size='10.5'>— UNIVERSAL FARM COMPANION</font>", title_style),
        Paragraph(
            "Official Farm Telemetry, ML Pathogen Risk &amp; Agronomic Advisory Report<br/>"
            f"<i>Report Issued: {datetime.now(IST).strftime('%d %B %Y, %I:%M %p IST')}</i>",
            subtitle_style,
        ),
    ]

    if logo_flowable:
        if hasattr(logo_flowable, "width") and logo_flowable.width > 100:
            header_meta = [
                Paragraph("<b>Official Farm Telemetry, ML Pathogen Risk &amp; Agronomic Advisory Report</b>", subtitle_style),
                Paragraph(f"<i>Report Issued: {datetime.now(IST).strftime('%d %B %Y, %I:%M %p IST')}</i>", subtitle_style),
            ]
            header_table = Table(
                [[logo_flowable, header_meta]],
                colWidths=[200, 332],
            )
            header_table.setStyle(
                TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ])
            )
            story.append(header_table)
        else:
            header_table = Table(
                [[logo_flowable, header_text]],
                colWidths=[54, 478],
            )
            header_table.setStyle(
                TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ])
            )
            story.append(header_table)
    else:
        for item in header_text:
            story.append(item)

    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2e7d32"), spaceBefore=2, spaceAfter=8))

    # 2. Farm Context Banner
    loc_name = sanitize_for_pdf(str(farm_config.get("name", "Farm Location")))
    lat = float(farm_config.get("lat", 16.51))
    lon = float(farm_config.get("lon", 80.52))
    crop = sanitize_for_pdf(str(farm_config.get("crop", "Tomato"))).title()
    stage = sanitize_for_pdf(str(farm_config.get("stage", "Flowering Stage")))

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
            Paragraph(f"{sanitize_for_pdf(str(telemetry.get('source', 'Virtual Weather & Soil Station')))}", table_cell),
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
    story.append(Spacer(1, 8))

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
            Paragraph("20.0 - 30.0 °C", table_cell),
            Paragraph("Field canopy level", table_cell),
        ],
        [
            Paragraph("Relative Atmospheric Humidity", table_cell),
            Paragraph(f"{telemetry.get('humidity_pct', 0.0):.1f} %", table_cell),
            Paragraph("50.0 - 75.0 %", table_cell),
            Paragraph("High moisture favors spore growth" if telemetry.get("humidity_pct", 0.0) > 75 else "Optimal band", table_cell),
        ],
        [
            Paragraph("Volumetric Soil Moisture", table_cell),
            Paragraph(f"{telemetry.get('soil_moisture_pct', 0.0):.1f} %", table_cell),
            Paragraph("18.0 - 28.0 %", table_cell),
            Paragraph("Adequate root zone moisture", table_cell),
        ],
        [
            Paragraph("Accumulated Daily Rainfall", table_cell),
            Paragraph(f"{telemetry.get('rainfall_mm', 0.0):.1f} mm", table_cell),
            Paragraph("-", table_cell),
            Paragraph("Precipitation gauge", table_cell),
        ],
        [
            Paragraph("Solar Irradiance", table_cell),
            Paragraph(f"{telemetry.get('sunlight_wm2', 0.0):.0f} W/m2", table_cell),
            Paragraph("0 - 1000 W/m2", table_cell),
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
    model_name = sanitize_for_pdf((ml_prediction or {}).get("model", {}).get("name", "Trained Ensemble"))
    risk_box_data = [
        [
            Paragraph(f"<b>ML Weather Risk Evaluation:</b> <font color='{risk_color}'><b>{risk_pct}% ({risk_level})</b></font>", table_cell_bold),
            Paragraph(
                f"Model: {model_name} | "
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
    story.append(Spacer(1, 8))

    # 4. Expert Agronomic Advisory
    story.append(Paragraph("2. Expert Field Diagnostic & Advisory", section_heading))

    # Clean advisory text for reportlab paragraph rendering
    clean_text = advisory_text or ""
    clean_text = re.sub(r"BEGIN_STRUCTURED_JSON[\s\S]*?END_STRUCTURED_JSON", "", clean_text, flags=re.IGNORECASE).strip()
    clean_text = re.sub(r"BEGIN_STRUCTURED_JSON[\s\S]*$", "", clean_text, flags=re.IGNORECASE).strip()
    clean_text = re.sub(r"```(?:json)?\s*\{[\s\S]*?\}\s*```", "", clean_text, flags=re.IGNORECASE).strip()
    clean_text = re.sub(r"```(?:json)?\s*\{[\s\S]*$", "", clean_text, flags=re.IGNORECASE).strip()
    clean_text = re.sub(r'\{\s*"response_mode"[\s\S]*$', '', clean_text, flags=re.IGNORECASE).strip()
    clean_text = re.sub(r"END_STRUCTURED_JSON", "", clean_text, flags=re.IGNORECASE).strip()
    clean_text = re.sub(r"^```(?:markdown)?\s*\n", "", clean_text.strip(), flags=re.IGNORECASE)
    clean_text = re.sub(r"\n```\s*$", "", clean_text.strip())

    # Parse lines with markdown table detection
    lines = clean_text.split("\n")
    table_buffer: list[str] = []

    for line in lines:
        line_s = line.strip()

        # Ignore markdown fence delimiters e.g. ``` or ```markdown
        if line_s.startswith("```"):
            if table_buffer:
                t = parse_markdown_table(table_buffer, table_cell_bold, table_cell)
                if t:
                    story.append(t)
                    story.append(Spacer(1, 6))
                table_buffer = []
            continue

        # Check if line is a table row (starts with | or contains at least 2 pipes)
        is_table_line = (line_s.startswith("|") or line_s.count("|") >= 2) and not line_s.startswith("#")
        if is_table_line:
            table_buffer.append(line_s)
            continue

        # If we were accumulating a markdown table, flush and render it
        if table_buffer:
            t = parse_markdown_table(table_buffer, table_cell_bold, table_cell)
            if t:
                story.append(t)
                story.append(Spacer(1, 6))
            table_buffer = []

        if not line_s:
            story.append(Spacer(1, 4))
            continue

        sanitized_line = sanitize_for_pdf(line_s)
        if not sanitized_line:
            continue

        # Headings
        if sanitized_line.startswith("### "):
            story.append(Paragraph(format_inline_markup(f"<b>{sanitized_line[4:]}</b>"), h3_style))
        elif sanitized_line.startswith("## "):
            story.append(Paragraph(format_inline_markup(f"<b>{sanitized_line[3:]}</b>"), h2_style))
        elif sanitized_line.startswith("# "):
            story.append(Paragraph(format_inline_markup(f"<b>{sanitized_line[2:]}</b>"), section_heading))
        # Bullet Lists: -, *, •
        elif sanitized_line.startswith("- ") or sanitized_line.startswith("* ") or sanitized_line.startswith("• "):
            prefix_len = 2
            bullet_text = sanitized_line[prefix_len:].strip()
            story.append(Paragraph(f"&bull; {format_inline_markup(bullet_text)}", body_style))
        # Numbered Lists: 1., 2., etc.
        elif re.match(r"^\d+[\.\)]\s+", sanitized_line):
            m = re.match(r"^(\d+[\.\)])\s+(.*)$", sanitized_line)
            if m:
                story.append(Paragraph(f"<b>{m.group(1)}</b> {format_inline_markup(m.group(2))}", body_style))
            else:
                story.append(Paragraph(format_inline_markup(sanitized_line), body_style))
        else:
            story.append(Paragraph(format_inline_markup(sanitized_line), body_style))

    # Flush any trailing table
    if table_buffer:
        t = parse_markdown_table(table_buffer, table_cell_bold, table_cell)
        if t:
            story.append(t)
            story.append(Spacer(1, 6))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#cccccc"), spaceBefore=4, spaceAfter=6))

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
