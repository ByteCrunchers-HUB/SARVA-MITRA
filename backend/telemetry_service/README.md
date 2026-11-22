# Telemetry & Virtual Sensor Service (Replacing IoT Hardware)

The `telemetry_service` replaces physical IoT/ESP32 hardware with live and historical environmental data fetched from free meteorological and soil APIs. It formats payloads that directly satisfy the schemas for the **ML Engine** (`backend/ml_engine`) and **RAG Advisory Pipeline** (`backend/rag_pipeline`).

---

## 1. Verified API Status

| Provider | Status | Role in Telemetry Pipeline |
|---|---|---|
| **WeatherAPI** | ✅ **Active (200 OK)** | Real-time air temperature, relative humidity, precipitation |
| **Tomorrow.io** | ✅ **Active (200 OK)** | Real-time solar irradiance (`solarGHI`), high-precision weather |
| **AgroMonitoring** | ✅ **Active (200 OK)** | Agricultural soil temperature & satellite context |
| **Open-Meteo** | ✅ **Active (200 OK)** | Hourly/Daily continuous soil moisture (`0-1cm`), solar radiation, precipitation, elevation, and 8-day history backfill |
| **ISRIC SoilGrids** | ✅ **Active (200 OK)** | Soil pH, organic carbon, clay %, sand %, silt % |
| **OpenWeatherMap** | ⏳ *Pending Activation* | Key was newly generated; OpenWeatherMap keys typically activate within 10–60 minutes of creation. The service seamlessly falls back to WeatherAPI and Open-Meteo in the meantime. |

---

## 2. Architecture & File Structure

```text
backend/telemetry_service/
├── __init__.py           # Package marker
├── config.py             # Environment configuration & API credentials
├── service.py            # Core telemetry aggregation & ML/RAG schema formatting
├── app.py                # Standalone FastAPI service with pipeline endpoints
├── requirements.txt      # Dependencies
├── README.md             # Documentation
└── tests/
    └── test_service.py   # Unit & end-to-end integration tests (Telemetry -> ML -> RAG)
```

---

## 3. Endpoints (`backend/telemetry_service/app.py`)

Run the standalone service:
```bash
.venv/bin/python -m uvicorn backend.telemetry_service.app:app --host 0.0.0.0 --port 8003 --reload
```

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service and provider connectivity check |
| `GET` | `/telemetry/current` | Real-time readings (`temperature_c`, `humidity_pct`, `soil_moisture_pct`, `sunlight_wm2`, `rainfall_mm`, `leaf_wet_days`) |
| `GET` | `/telemetry/history` | Consecutive 8-day historical daily records strictly validated for ML Engine |
| `GET` | `/telemetry/ml-payload` | Generates ready-to-post JSON for ML Engine `POST /predict` |
| `GET` | `/telemetry/rag-payload`| Generates ready-to-post JSON for RAG `POST /advisory` |
| `POST`| `/pipeline/predict` | Fetches telemetry and immediately proxies to ML Engine `/predict` |
| `POST`| `/pipeline/advisory` | Fetches telemetry, invokes ML prediction, and queries RAG for advisory |

---

## 4. Programmatic Python Usage

You can also import and use the service directly within the backend without extra HTTP hops:

```python
from backend.telemetry_service.service import telemetry_service

# 1. Get real-time readings
current = telemetry_service.get_current_readings(lat=16.51, lon=80.52)

# 2. Get 8-day ML-ready history
history = telemetry_service.get_historical_records(lat=16.51, lon=80.52)

# 3. Build ML Engine PredictRequest payload
ml_payload = telemetry_service.build_ml_payload(
    lat=16.51,
    lon=80.52,
    location="Vijayawada",
)

# 4. Build RAG AdvisoryRequest payload
rag_payload = telemetry_service.build_rag_payload(
    crop="tomato",
    question="How is my soil moisture and crop risk today?",
    lat=16.51,
    lon=80.52,
    location="Vijayawada",
)
```

---

## 5. Test Verification

Run the end-to-end integration suite:
```bash
SARVA_MODEL_PATH=backend/ml_engine/models/sarva_mitra_risk_model.joblib PYTHONPATH=. .venv/bin/python backend/telemetry_service/tests/test_service.py
```

Result:
- **Current readings:** Successfully fetched from WeatherAPI & Open-Meteo
- **8-Day History:** Consecutive daily records generated and validated
- **ML Engine:** Successfully predicted `risk_pct: 0.4% (low)`
- **RAG Pipeline:** Successfully produced agronomic advisory using live telemetry
