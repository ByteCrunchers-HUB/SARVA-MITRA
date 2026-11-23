from backend.rag_pipeline.rag import clean_advisory_text

def test_clean_advisory_text():
    sample_with_truncated_json = """Advisory

Your sensors report: humidity 52 %, no rain, soil moisture 15.5 %, sunlight 500 W/m2, temperature 30.9 C.
The model has flagged an unusual pattern - this is only a warning signal, not a diagnosis.

I could not find a documented tomato problem that matches these exact readings.

Please inspect the plants for any visible symptoms and share what you see with your local KVK.

BEGIN_STRUCTURED_JSON { "response_mode": "ML_OUTPUT_1", "overview": "Sensors show humidity 52 %, soil moisture 15.5 %", "sensor_readings": { "humidity_pct": 52.0 }, "recommendations": [ { "step": "Inspect the tomato plants today
"""
    cleaned = clean_advisory_text(sample_with_truncated_json)
    assert "BEGIN_STRUCTURED_JSON" not in cleaned, "BEGIN_STRUCTURED_JSON should be stripped"
    assert "response_mode" not in cleaned, "Raw JSON should be stripped"
    assert "Your sensors report: humidity 52 %" in cleaned, "Advisory text should be preserved"
    assert "Please inspect the plants for any visible symptoms" in cleaned, "Advisory text should be preserved"
    print("Test passed: clean_advisory_text successfully stripped truncated JSON!")

if __name__ == "__main__":
    test_clean_advisory_text()
