import io
from fastapi.testclient import TestClient
from backend.main import app

def test_ui_and_voice():
    with TestClient(app) as client:
        # 1. UI HTML structure verification
        res_ui = client.get("/ui/")
        assert res_ui.status_code == 200
        html = res_ui.text
        # Check separate views exist
        assert 'id="view-history"' in html
        assert 'id="view-schemes"' in html
        assert 'id="nav-history"' in html
        assert 'id="nav-schemes"' in html
        assert 'PM-KISAN' in html
        assert 'Soil Health Card Scheme' in html
        assert 'btn-download-chat-report' in html
        print("Separate History and Schemes views in HTML: PASS")

        # 2. Test chat endpoint with mode='report' (initial sync assessment)
        req_report = {
            "question": "Provide a complete agronomic status assessment and recommendations for tomato based on current field conditions.",
            "crop": "tomato",
            "lat": 16.51,
            "lon": 80.52,
            "location": "Vijayawada",
            "chat_history": [],
            "mode": "report"
        }
        res_report = client.post("/api/chat", json=req_report)
        assert res_report.status_code == 200, res_report.text
        data_rep = res_report.json()
        assert data_rep["answer"]
        print("Chat initial report mode: PASS (answer length:", len(data_rep["answer"]), ")")

        # 3. Test chat endpoint with mode='chat' (conversational Q&A)
        req_chat = {
            "question": "How can I prevent flower drop and yellowing leaves under these conditions?",
            "crop": "tomato",
            "lat": 16.51,
            "lon": 80.52,
            "location": "Vijayawada",
            "chat_history": [
                {"role": "assistant", "content": data_rep["answer"][:200]}
            ],
            "mode": "chat"
        }
        res_chat = client.post("/api/chat", json=req_chat)
        assert res_chat.status_code == 200, res_chat.text
        data_chat = res_chat.json()
        assert data_chat["answer"]
        print("Chat conversational mode: PASS")

        # 4. Test transcribe endpoint error handling on empty/invalid
        res_trans_empty = client.post("/api/transcribe", files={"file": ("test.wav", b"", "audio/wav")})
        assert res_trans_empty.status_code == 400
        print("Transcribe endpoint empty check: PASS")

    print("\n=== ALL UI & VOICE TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_ui_and_voice()
