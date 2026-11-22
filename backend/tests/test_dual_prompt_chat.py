from backend.rag_pipeline.rag import RAGPipeline

def test_dual_prompts():
    rag = RAGPipeline()
    readings = {
        "temperature_c": 24.5,
        "humidity_pct": 82.0,
        "soil_moisture_pct": 21.0,
        "rainfall_mm": 2.5,
        "sunlight_wm2": 320.0,
        "risk_pct": 74.2,
        "risk_level": "moderate"
    }
    prediction = {
        "model": {"name": "XGBoost Ensemble"},
        "prediction": {"risk_pct": 74.2, "risk_level": "moderate"}
    }

    # 1. Turn 1: Initial Report Mode
    print("\n--- Testing Turn 1: Report Mode ---")
    ans_report, struct_report = rag.answer(
        readings=readings,
        ml_output=1,
        crop="tomato",
        location="Vijayawada",
        question="Provide a complete agronomic status assessment.",
        chat_history=[],
        ml_prediction=prediction,
        mode="report"
    )
    print("Report excerpt:\n", ans_report[:200], "...")
    assert "sensors show" in ans_report.lower() or "humidity" in ans_report.lower()
    print("Report Mode: PASS")

    # 2. Turn 2: Chat Mode (User asking specific question)
    print("\n--- Testing Turn 2: Chat Mode ---")
    chat_hist = [
        {"role": "user", "content": "Provide a complete agronomic status assessment."},
        {"role": "assistant", "content": ans_report[:200]}
    ]
    ans_chat, struct_chat = rag.answer(
        readings=readings,
        ml_output=1,
        crop="tomato",
        location="Vijayawada",
        question="How can I prevent flower drop and yellowing leaves under these conditions?",
        chat_history=chat_hist,
        ml_prediction=prediction,
        mode="chat"
    )
    print("Chat response:\n", ans_chat)
    # Check for suggested follow-up questions (accounting for unicode non-breaking hyphens)
    norm = ans_chat.replace("\u2011", "-").lower()
    assert "suggested follow-up" in norm or "suggested questions" in norm or "follow-up questions" in norm
    print("Chat Mode with Suggested Follow-Up Questions: PASS")
    print("\n=== ALL DUAL PROMPT TESTS PASSED! ===")

if __name__ == "__main__":
    test_dual_prompts()
