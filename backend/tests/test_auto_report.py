import io
import pypdf
from fastapi.testclient import TestClient
from backend.main import app

def test_auto_report_generation():
    client = TestClient(app)
    # 1. Test POST with advisory_text=None
    res = client.post(
        "/api/report/pdf",
        json={
            "crop": "tomato",
            "location": "Vijayawada, AP",
            "lat": 16.51,
            "lon": 80.52,
            "stage": "flowering"
        }
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    reader = pypdf.PdfReader(io.BytesIO(res.content))
    text = "\n".join(page.extract_text() for page in reader.pages)
    
    print(f"Total pages: {len(reader.pages)}")
    print(f"Total characters: {len(text)}")
    assert len(text) > 800, f"Report is too short! ({len(text)} chars)"
    assert "High-Priority Field Scouting" in text or "Agronomic" in text or "Early Blight" in text, "Key report content missing!"
    print("Test passed: Comprehensive report generated automatically!")

if __name__ == "__main__":
    test_auto_report_generation()
