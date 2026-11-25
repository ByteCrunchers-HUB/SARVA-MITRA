import io
import pypdf
from fastapi.testclient import TestClient
from backend.main import app

def test_home_and_chat_reports():
    client = TestClient(app)
    
    # Case 1: HomeScreen call (advisory_text is None)
    print("Testing Case 1: HomeScreen call (no advisory_text)...")
    res1 = client.post("/api/report/pdf", json={
        "crop": "Tomato",
        "location": "Vijayawada",
        "lat": 16.51,
        "lon": 80.52,
        "stage": "Flowering & Fruit Set (50-80 days)",
        "advisory_text": None
    })
    assert res1.status_code == 200, f"Case 1 failed: {res1.status_code}"
    reader1 = pypdf.PdfReader(io.BytesIO(res1.content))
    text1 = "\n".join(page.extract_text() or "" for page in reader1.pages)
    print(f"Case 1 -> Pages: {len(reader1.pages)}, Chars: {len(text1)}")
    assert len(reader1.pages) >= 2, f"Expected at least 2 pages, got {len(reader1.pages)}"
    assert len(text1) > 1000, f"Expected > 1000 chars, got {len(text1)}"
    assert "Real-Time Telemetry" in text1
    assert "Early Blight" in text1 or "Scouting" in text1 or "Disease" in text1 or "Agronomic" in text1
    print("Case 1 passed: Home screen download produces complete multi-page report!")

    # Case 2: Short text passed (e.g. quick advisory or short message)
    print("\nTesting Case 2: Short text passed (should be upgraded to full report)...")
    short_text = "Moderate risk (29.87%). Monitor soil moisture closely. Maintain proper field drainage and check crop stage."
    res2 = client.post("/api/report/pdf", json={
        "crop": "Tomato",
        "location": "Vijayawada",
        "lat": 16.51,
        "lon": 80.52,
        "stage": "Flowering & Fruit Set (50-80 days)",
        "advisory_text": short_text
    })
    assert res2.status_code == 200, f"Case 2 failed: {res2.status_code}"
    reader2 = pypdf.PdfReader(io.BytesIO(res2.content))
    text2 = "\n".join(page.extract_text() or "" for page in reader2.pages)
    print(f"Case 2 -> Pages: {len(reader2.pages)}, Chars: {len(text2)}")
    assert len(reader2.pages) >= 2, f"Expected at least 2 pages, got {len(reader2.pages)}"
    assert len(text2) > 1000, f"Expected > 1000 chars, got {len(text2)}"
    print("Case 2 passed: Short text safely upgraded to full report!")

    # Case 3: Chilli crop from Home screen
    print("\nTesting Case 3: Chilli crop from Home screen...")
    res3 = client.post("/api/report/pdf", json={
        "crop": "Chilli",
        "location": "Guntur",
        "lat": 16.30,
        "lon": 80.45,
        "stage": "Flowering Stage",
        "advisory_text": None
    })
    assert res3.status_code == 200, f"Case 3 failed: {res3.status_code}"
    reader3 = pypdf.PdfReader(io.BytesIO(res3.content))
    text3 = "\n".join(page.extract_text() or "" for page in reader3.pages)
    print(f"Case 3 -> Pages: {len(reader3.pages)}, Chars: {len(text3)}")
    assert len(reader3.pages) >= 2
    assert "Anthracnose" in text3 or "Powdery Mildew" in text3 or "Chilli" in text3
    print("Case 3 passed: Chilli full report generated!")

if __name__ == "__main__":
    test_home_and_chat_reports()
