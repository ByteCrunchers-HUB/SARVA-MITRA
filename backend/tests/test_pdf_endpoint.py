from fastapi.testclient import TestClient
from backend.main import app

def test_generate_pdf_endpoint():
    client = TestClient(app)
    payload = {
        "crop": "Tomato",
        "location_name": "Vijayawada (Andhra Pradesh)",
        "risk_pct": 42.5,
        "risk_level": "Moderate Risk",
        "telemetry": {
            "temperature_c": 27.5,
            "humidity_pct": 65.0,
            "soil_moisture_pct": 24.0,
            "soil_ph": 6.5,
            "nitrogen_ppm": 40.0,
            "phosphorus_ppm": 18.0,
            "potassium_ppm": 110.0,
            "sunlight_lux": 700.0,
            "rainfall_mm": 0.0
        },
        "advisory_text": "# Agronomic Advisory\n\n### Key Findings\n- Temperature is optimal.\n- Soil moisture is within target range.\n\n---\n**Next Steps**: Continue regular monitoring."
    }
    response = client.post("/api/report/pdf", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 3000, f"PDF content too small: {len(response.content)} bytes"
    print(f"Successfully generated PDF! Size: {len(response.content)} bytes")

if __name__ == "__main__":
    test_generate_pdf_endpoint()
