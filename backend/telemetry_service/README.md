# 📡 Telemetry & Virtual Sensor Service

The `telemetry_service` provides a resilient **Virtual Sensor Layer** that eliminates the need for expensive, high-maintenance physical IoT/ESP32 sensor deployments on farms. 

By querying open meteorological, satellite, and soil APIs, the service streams real-time and 8-day consecutive historical environmental telemetry formatted strictly for the **ML Risk Engine** (`backend/ml_engine`) and the **RAG Advisory Pipeline** (`backend/rag_pipeline`).

---

## 📌 Project Links

* **GitHub Repository:** [https://github.com/ByteCrunchers-HUB/SARVA-MITRA](https://github.com/ByteCrunchers-HUB/SARVA-MITRA)
* **Live Web Application:** [https://sarva-mitra-api.onrender.com/ui/](https://sarva-mitra-api.onrender.com/ui/)
* **Live API Documentation:** [https://sarva-mitra-api.onrender.com/docs](https://sarva-mitra-api.onrender.com/docs)
* **Setup Guide:** [SETUP.md](../../SETUP.md)

---

## 1. Verified Telemetry API Integrations

| Provider | Status | Role in Telemetry Pipeline |
|---|---|---|
| **WeatherAPI** | ✅ **Active (200 OK)** | Real-time air temperature, relative humidity, precipitation, wind |
| **Tomorrow.io** | ✅ **Active (200 OK)** | Real-time solar irradiance (`solarGHI`), high-precision weather |
| **AgroMonitoring** | ✅ **Active (200 OK)** | Agricultural soil temperature & satellite context |
| **Open-Meteo** | ✅ **Active (200 OK)** | Hourly/Daily continuous soil moisture (`0-1cm`), solar radiation, precipitation, elevation, and 8-day history backfill |
| **ISRIC SoilGrids** | ✅ **Active (200 OK)** | Static soil pH, organic carbon, clay %, sand %, silt % |
| **OpenWeatherMap** | ⏳ *Fallback Available* | Key supported; service automatically falls back to WeatherAPI and Open-Meteo without service interruption |

---

## 2. Architecture & File Structure

```text
backend/telemetry_service/
├── __init__.py           # Package marker
├── config.py             # Environment configuration & API credentials
├── service.py            # Core telemetry aggregation & ML/RAG schema formatting
├── app.py                # Standalone FastAPI microservice
├── requirements.txt      # Module dependencies
├── README.md             # Telemetry documentation
└── tests/
    └── test_service.py   # Unit & end-to-end integration tests (Telemetry -> ML -> RAG)
```

---

## 3. Endpoints (`backend/telemetry_service/app.py`)

Run as a standalone microservice:
```bash
uvicorn backend.telemetry_service.app:app --host 0.0.0.0 --port 8003 --reload
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

The unified backend imports and queries `telemetry_service` in-process with zero network overhead:

```python
from backend.telemetry_service.service import telemetry_service

# 1. Fetch real-time readings
current = telemetry_service.get_current_readings(lat=16.51, lon=80.52)

# 2. Fetch consecutive 8-day historical trends
history = telemetry_service.get_historical_records(lat=16.51, lon=80.52)

# 3. Assemble ML PredictRequest schema
ml_payload = telemetry_service.build_ml_payload(
    lat=16.51,
    lon=80.52,
    location="Vijayawada",
)

# 4. Assemble RAG AdvisoryRequest schema
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

Run the automated integration test:
```bash
SARVA_MODEL_PATH=backend/ml_engine/models/sarva_mitra_risk_model.joblib PYTHONPATH=. python backend/telemetry_service/tests/test_service.py
```

Expected result:
- **Current readings:** Successfully queried from WeatherAPI & Open-Meteo
- **8-Day History:** Consecutive daily records generated and validated
- **ML Engine Integration:** Successfully returned risk prediction
- **RAG Integration:** Agronomic advisory generated using live telemetry

---

## 👥 Credits — Team ANVEXA

* **PRIYANSHU SARMA**
* **LIBERATOR NYADUNDU**
* **RYALI VENKATA SRI VIJAY KARTHIK**
* **Gajulapalli Venkata Raviteja**
* **Sneha Sarma**

**Repository:** [https://github.com/ByteCrunchers-HUB/SARVA-MITRA](https://github.com/ByteCrunchers-HUB/SARVA-MITRA)  
**Live App:** [https://sarva-mitra-api.onrender.com/ui/](https://sarva-mitra-api.onrender.com/ui/)
