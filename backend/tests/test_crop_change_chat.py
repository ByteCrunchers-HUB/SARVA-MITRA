from fastapi.testclient import TestClient
from backend.main import app

def test_crop_change_chat():
    client = TestClient(app)
    crops = ["tomato", "chilli", "ragi"]
    for c in crops:
        res = client.post("/api/chat", json={
            "question": f"Provide status report for {c}",
            "crop": c,
            "lat": 16.51,
            "lon": 80.52,
            "location": "Vijayawada",
            "stage": "Flowering Stage",
            "mode": "report"
        })
        print(f"Crop {c}: status {res.status_code}")
        assert res.status_code == 200, f"Crop {c} failed with {res.status_code}: {res.text}"
        data = res.json()
        assert len(data.get("answer", "")) > 100, f"Empty answer for {c}"
    print("All crop changes passed with HTTP 200 and complete report answers!")

if __name__ == "__main__":
    test_crop_change_chat()
