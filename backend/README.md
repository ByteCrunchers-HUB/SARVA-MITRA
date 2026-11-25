# 🌱 Sarva Mitra — Unified Backend API

A production-grade, unified **FastAPI** backend that seamlessly consolidates:
1. **Telemetry & Virtual Sensors** (`backend/telemetry_service`): Multi-API weather, solar, soil moisture, and historical backfill.
2. **Machine Learning Risk Engine** (`backend/ml_engine`): Anomaly detection & LightGBM / ensemble weather-risk model with 8-day consecutive trend scoring.
3. **RAG Agricultural Advisory Pipeline** (`backend/rag_pipeline`): MongoDB Atlas vector search & Groq LLM advisory.
4. **Automated Advisory Report Generator**: Dynamic PDF field report generation with ReportLab and SVG graphics.
5. **Modern Static Web UI**: Serves the rich, responsive web application at `/ui/`.

---

## 📌 Project Links

* **GitHub Repository:** [https://github.com/ByteCrunchers-HUB/SARVA-MITRA](https://github.com/ByteCrunchers-HUB/SARVA-MITRA)
* **Live Web App:** [https://sarva-mitra-api.onrender.com/ui/](https://sarva-mitra-api.onrender.com/ui/)
* **Live Swagger Docs:** [https://sarva-mitra-api.onrender.com/docs](https://sarva-mitra-api.onrender.com/docs)
* **Live ReDoc:** [https://sarva-mitra-api.onrender.com/redoc](https://sarva-mitra-api.onrender.com/redoc)
* **Setup Guide:** [SETUP.md](../SETUP.md)

---

## 🚀 How to Run the Unified Server

From the project root:

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Launch FastAPI server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Once running:
- 🌐 **Web Interface:** Open `http://localhost:8000/ui/`
- 📚 **Swagger UI:** Open `http://localhost:8000/docs`
- 📑 **ReDoc:** Open `http://localhost:8000/redoc`

---

## 🎨 Unified Endpoints for UI / Frontend

These high-level endpoints allow frontend applications to fetch complete dashboards and advisory dialogues with single, consolidated HTTP calls.

### 1. `GET /api/dashboard`
Populates the entire farmer dashboard in one call (live sensors, 8-day history, ML risk, and quick advice).

* **Query Parameters:**
  * `lat` (float, default: `16.51`)
  * `lon` (float, default: `80.52`)
  * `location` (string, default: `"Vijayawada"`)
  * `crop` (string, default: `"tomato"`)

* **Example Response:**
```json
{
  "status": "ok",
  "generated_at": "2026-11-25T09:00:00+05:30",
  "location": { "name": "Vijayawada", "lat": 16.51, "lon": 80.52 },
  "crop": "tomato",
  "current_telemetry": {
    "temperature_c": 24.0,
    "humidity_pct": 87.0,
    "soil_moisture_pct": 16.1,
    "rainfall_mm": 0.0,
    "sunlight_wm2": 0.0,
    "leaf_wet_days": 1,
    "source": "WeatherAPI"
  },
  "historical_trends": [
    {
      "date": "2026-11-17",
      "soil_moisture_pct": 23.71,
      "sunlight_wm2": 408.36,
      "rainfall_mm": 0.7,
      "leaf_wet_days": 1,
      "air_temperature_c": 25.1,
      "humidity_pct": 68.0
    }
  ],
  "ml_risk": {
    "risk_pct": 0.4,
    "risk_level": "low",
    "risk_bands": { "low_max": 20, "moderate_max": 60 },
    "ml_output_code": 0
  },
  "quick_advisory": "Low risk (0.4%). Environmental and soil conditions are optimal. Continue standard fertilizer and irrigation practices."
}
```

---

### 2. `POST /api/chat`
Stateful conversational agronomic assistant. Automatically injects live farm telemetry and ML risk into RAG for contextual guidance.

* **Request Body:**
```json
{
  "question": "Leaves are curling with small yellow spots, what should I inspect and spray?",
  "crop": "tomato",
  "lat": 16.51,
  "lon": 80.52,
  "location": "Vijayawada",
  "chat_history": []
}
```

* **Example Response:**
```json
{
  "schema_version": "2.0",
  "session_id": "c1f7b093-9c84-482a-bc9e-9764ff3f3a81",
  "crop": "tomato",
  "location": { "name": "Vijayawada", "lat": 16.51, "lon": 80.52 },
  "answer": "**Advisory**\n\nYour current sensor readings show humidity 87%, soil moisture 16.1%...",
  "structured": {
    "diagnosis": "Early leaf curl / whitefly vector caution",
    "action_items": ["Inspect underside of leaves for whiteflies", "Maintain 20-30% soil moisture"],
    "irrigation": "Hold overhead irrigation"
  },
  "risk": {
    "risk_pct": 0.4,
    "risk_level": "low",
    "ml_output": 0
  },
  "telemetry": {
    "temperature_c": 24.0,
    "humidity_pct": 87.0,
    "soil_moisture_pct": 16.1,
    "rainfall_mm": 0.0,
    "sunlight_wm2": 0.0
  },
  "chat_history": [
    { "role": "user", "content": "Leaves are curling with small yellow spots..." },
    { "role": "assistant", "content": "**Advisory**\n\nYour current sensor readings..." }
  ]
}
```

---

### 3. `POST /api/report/generate`
Generates a downloadable, high-fidelity PDF advisory report summarizing current sensor status, ML risk level, and agronomic action items.

* **Request Body:**
```json
{
  "crop": "tomato",
  "location": "Vijayawada",
  "lat": 16.51,
  "lon": 80.52,
  "stage": "Flowering & Fruit Set (50-80 days)",
  "advisory_text": "..."
}
```
* **Returns:** Binary `application/pdf` stream (`Sarva_Mitra_Advisory_Report.pdf`).

---

### 4. `GET /api/health`
Aggregated health check monitoring:
- Telemetry provider connectivity (WeatherAPI, Tomorrow.io, AgroMonitoring, Open-Meteo)
- ML model bundle loaded in memory
- MongoDB Atlas Vector Index & Groq LLM API connectivity

---

## 🛠️ Mounted Sub-Module Endpoints

For modular operations, microservices remain independently accessible:

* **Telemetry:**
  * `GET /api/telemetry/current?lat=...&lon=...`
  * `GET /api/telemetry/history?lat=...&lon=...&days=8`
  * `GET /api/telemetry/ml-payload`
  * `GET /api/telemetry/rag-payload`
* **ML Engine:**
  * `GET /api/ml/health`
  * `POST /api/ml/predict`
* **RAG Pipeline:**
  * `GET /api/rag/health`
  * `GET /api/rag/diagnostics`
  * `POST /api/rag/advisory`

---

## 🧪 Testing

Run the automated integration test:

```bash
SARVA_MODEL_PATH=backend/ml_engine/models/sarva_mitra_risk_model.joblib PYTHONPATH=. python backend/tests/test_unified.py
```

---

## 👥 Credits — Team ANVEXA

* **PRIYANSHU SARMA**
* **LIBERATOR NYADUNDU**
* **RYALI VENKATA SRI VIJAY KARTHIK**
* **Gajulapalli Venkata Raviteja**
* **Sneha Sarma**

**Repository:** [https://github.com/ByteCrunchers-HUB/SARVA-MITRA](https://github.com/ByteCrunchers-HUB/SARVA-MITRA)  
**Live Backend & UI:** [https://sarva-mitra-api.onrender.com/ui/](https://sarva-mitra-api.onrender.com/ui/)
