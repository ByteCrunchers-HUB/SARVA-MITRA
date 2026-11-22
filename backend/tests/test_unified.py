import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from fastapi.testclient import TestClient
from backend.main import app

def test_unified_backend():
    print("=== TESTING UNIFIED BACKEND ===")

    with TestClient(app) as client:
        # 1. Root & Health
        print("\n--- 1. Testing GET / and GET /api/health ---")
        res_root = client.get("/")
        assert res_root.status_code == 200, res_root.text
        print("Root response:", res_root.json()["service"])

        res_health = client.get("/api/health")
        assert res_health.status_code == 200, res_health.text
        health_data = res_health.json()
        print("Health status:", health_data["status"])
        print("Telemetry active providers:", health_data["telemetry"]["active_providers"])
        print("ML Engine model:", health_data["ml_engine"]["model_name"])
        print("RAG Pipeline Groq keys count:", health_data["rag_pipeline"]["groq_keys_count"])
        assert health_data["status"] == "ok"
        assert health_data["ml_engine"]["loaded"] is True

        # 2. Unified Dashboard Endpoint
        print("\n--- 2. Testing Unified GET /api/dashboard ---")
        res_dash = client.get("/api/dashboard?lat=16.51&lon=80.52&location=Vijayawada&crop=tomato")
        assert res_dash.status_code == 200, res_dash.text
        dash_data = res_dash.json()
        print("Dashboard crop:", dash_data["crop"])
        print("Current telemetry:", dash_data["current_telemetry"])
        print("ML risk:", dash_data["ml_risk"])
        print("Historical trends count:", len(dash_data["historical_trends"]))
        print("Quick advisory:", dash_data["quick_advisory"])
        assert "temperature_c" in dash_data["current_telemetry"]
        assert "risk_pct" in dash_data["ml_risk"]
        assert len(dash_data["historical_trends"]) == 8

        # 3. Unified Farmer Chat Endpoint
        print("\n--- 3. Testing Unified POST /api/chat ---")
        chat_payload = {
            "question": "What is the recommended soil moisture level and care for tomato right now?",
            "crop": "tomato",
            "lat": 16.51,
            "lon": 80.52,
            "location": "Vijayawada",
            "chat_history": []
        }
        res_chat = client.post("/api/chat", json=chat_payload)
        assert res_chat.status_code == 200, res_chat.text
        chat_data = res_chat.json()
        print("Answer snippet:", chat_data["answer"][:180], "...")
        print("Risk evaluation:", chat_data["risk"])
        print("Telemetry context:", chat_data["telemetry"])
        print("Chat history count:", len(chat_data["chat_history"]))
        assert chat_data["answer"]
        assert len(chat_data["chat_history"]) == 2

        # 4. Individual Endpoints
        print("\n--- 4. Testing Individual Endpoints ---")
        res_tel = client.get("/api/telemetry/current?lat=16.51&lon=80.52")
        assert res_tel.status_code == 200
        print("Telemetry current: PASS")

        res_ml_h = client.get("/api/ml/health")
        assert res_ml_h.status_code == 200
        print("ML health: PASS")

        res_rag_h = client.get("/api/rag/health")
        assert res_rag_h.status_code == 200
        print("RAG health: PASS")

    print("\n=== ALL UNIFIED BACKEND TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_unified_backend()
