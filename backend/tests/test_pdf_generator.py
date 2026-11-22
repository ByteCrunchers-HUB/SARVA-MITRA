from pathlib import Path
from frontend.pdf_generator import generate_advisory_pdf

def test_generation():
    farm = {
        "name": "Vijayawada",
        "lat": 16.51,
        "lon": 80.52,
        "crop": "tomato",
        "stage": "🌸 Flowering & Fruit Set (50-80 days)"
    }
    telemetry = {
        "temperature_c": 24.5,
        "humidity_pct": 82.0,
        "soil_moisture_pct": 21.0,
        "rainfall_mm": 2.5,
        "sunlight_wm2": 320.0,
        "source": "Open-Meteo & Agromonitoring"
    }
    prediction = {
        "model": {"name": "XGBoost + LightGBM Ensemble"},
        "prediction": {"risk_pct": 74.2, "risk_level": "moderate"}
    }
    advisory = """### 1. What the sensors show
Temperature 24.5 °C, humidity 82 %, soil moisture 21 % (02_weather_thresholds_by_disease, S1).

### 2. What the model signal means
The model flagged an elevated weather proxy risk. Look for early foliar spots.

### 3. What you can do now
- Maintain ridge drainage to prevent root waterlogging (irrigation_tomato, S2).
- Inspect lower canopy for dark concentric rings (early blight checklist).

### 4. Next steps
Contact your nearest KVK officer if water-soaked lesions expand."""

    pdf_bytes = generate_advisory_pdf(
        farm_config=farm,
        telemetry=telemetry,
        ml_prediction=prediction,
        advisory_text=advisory,
        logo_path=Path("frontend/assets/logo.svg")
    )
    print(f"Generated PDF bytes: {len(pdf_bytes)}")
    assert len(pdf_bytes) > 5000, "PDF too small"
    
    # Save a test file to verify
    test_out = Path("frontend/assets/sample_report.pdf")
    test_out.write_bytes(pdf_bytes)
    print("Saved sample report to", test_out)

if __name__ == "__main__":
    test_generation()
