from reportlab.lib.styles import getSampleStyleSheet
from frontend.pdf_generator import parse_markdown_table, generate_advisory_pdf

styles = getSampleStyleSheet()
h_style = styles["Normal"]
c_style = styles["Normal"]

table_text = [
    "| Sensor Parameter | Live Reading | Reference Band | Status Note |",
    "| --- | --- | --- | --- |",
    "| Ambient Air Temperature | 28.0 °C | 20.0 - 30.0 °C | Optimal |",
    "| Relative Humidity | 77.0 % | 50.0 - 75.0 % | Elevated |"
]

tbl = parse_markdown_table(table_text, h_style, c_style)
print("Table parsed:", tbl is not None)
if tbl:
    print("Col widths:", tbl._colWidths)
    print("Row count:", len(tbl._cellvalues))

# Test full PDF generation with a table in advisory_text
adv_with_table = """### Agronomic Assessment

| Disease | Symptoms | Immediate Action |
| --- | --- | --- |
| Early Blight | Concentric dark rings on lower leaves | Spray preventive neem oil (5ml/L) |
| Late Blight | Water-soaked pale lesions | Avoid overhead irrigation |

- Maintain optimal soil moisture.
"""

farm_cfg = {"name": "Vijayawada", "lat": 16.51, "lon": 80.52, "crop": "tomato", "stage": "flowering"}
telem = {"temperature_c": 28.0, "humidity_pct": 77.0, "soil_moisture_pct": 23.8, "rainfall_mm": 1.3, "sunlight_wm2": 42.0}
pred = {"prediction": {"risk_pct": 34.09, "risk_level": "moderate"}}

pdf_bytes = generate_advisory_pdf(farm_cfg, telem, pred, adv_with_table)
print("Generated PDF bytes:", len(pdf_bytes))
