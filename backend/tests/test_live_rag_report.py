from backend.rag_pipeline.rag import RAGPipeline
import json

rag = RAGPipeline()
readings = {
    "temperature_c": 28.0,
    "humidity_pct": 77.0,
    "soil_moisture_pct": 23.8,
    "rainfall_mm": 1.3,
    "sunlight_wm2": 42.0,
    "source": "WeatherAPI",
}
ml_prediction = {
    "prediction": {
        "risk_pct": 34.09,
        "risk_level": "moderate",
    },
    "model": {
        "name": "XGBoost (boosting)",
    },
}

ans, citations = rag.answer(
    readings=readings,
    ml_output=1,
    crop="tomato",
    location="Vijayawada",
    question="Provide a complete agronomic status assessment and recommendations for tomato (Flowering Stage) based on current field conditions.",
    chat_history=[],
    ml_prediction=ml_prediction,
    mode="report",
)

print("=== GENERATED REPORT ANSWER ===")
print(ans)
print("=== CITATIONS ===")
print(citations)
