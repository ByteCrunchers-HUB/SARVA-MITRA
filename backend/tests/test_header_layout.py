from pathlib import Path
from frontend.pdf_generator import generate_advisory_pdf
import pypdf
import io

farm_cfg = {
    "name": "Vijayawada, AP",
    "lat": 16.51,
    "lon": 80.52,
    "crop": "Tomato",
    "stage": "Flowering & Fruit Set (50-80 days)",
}

telemetry = {
    "temperature_c": 28.5,
    "humidity_pct": 74.0,
    "soil_moisture_pct": 22.4,
    "rainfall_mm": 0.2,
    "sunlight_wm2": 450.0,
    "source": "WeatherAPI",
}

ml_prediction = {
    "prediction": {
        "risk_pct": 32.5,
        "risk_level": "moderate",
    },
    "model": {
        "name": "XGBoost (boosting)",
    },
}

advisory_sample = """### 1. Executive Microclimate & Pathogen Risk Assessment
- **Field Microclimate**: Ambient Air Temperature is **28.5°C**, Relative Humidity is **74.0%**, Volumetric Soil Moisture is **22.4%** (Optimal).
- **ML Pathogen Risk Status**: **32.50% (MODERATE)** | Signal Code: **1 (Active)**.

### 2. High-Priority Field Scouting & Disease Checklist
Walk the crop rows in an inverted 'W' pattern during morning hours (07:30–10:00). Closely check the following priority issues:

| Crop Disease / Suspect Pathogen | Diagnostic Symptoms in Field | Priority Level |
|---|---|---|
| **Early Blight (Alternaria solani)** | Target-like concentric brown rings on older lower leaves progressing upward. | High |
| **Late Blight (Phytophthora infestans)** | Rapidly enlarging water-soaked lesions turning dark with white downy mold under saturated humidity. | High |
| **Blossom-End Rot** | Water-soaked dark leathering at fruit blossom end due to moisture fluctuations. | Moderate |

### 3. Practical Agronomic Field Interventions
| Management Area | Recommended Field Action | Operational Timing |
|---|---|---|
| **Irrigation & Hydration** | Maintain current 2-day pulse drip irrigation. Avoid heavy flood irrigation. | Early morning (06:00–08:30) |
| **Canopy Hygiene** | Prune senescent lower leaves up to 20 cm from ground; weed row margins. | Dry sunny midday |
| **Biological Protection** | Spray Neem Oil emulsion (5 ml/L + surfactant) or Trichoderma viride (5g/L). | Calm evening hours |
| **Crop Nutrition** | Foliar spray of Calcium Nitrate (5g/L) + Boron (1g/L) to prevent blossom-end rot. | Active fruit set |

### 4. Critical Boundaries & Official Notice
- Telemetry monitors microclimate pathogen risk patterns and does not substitute for laboratory testing.
"""

pdf_bytes = generate_advisory_pdf(
    farm_config=farm_cfg,
    telemetry=telemetry,
    ml_prediction=ml_prediction,
    advisory_text=advisory_sample,
    logo_path=Path("frontend/assets/logo-report.svg"),
)

reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
print(f"Total pages: {len(reader.pages)}")
for i, page in enumerate(reader.pages):
    print(f"\n--- PAGE {i+1} ---")
    print(page.extract_text())
