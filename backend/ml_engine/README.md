# 🧠 Machine Learning Risk Engine

The `ml_engine` is a core analytical component of Sarva Mitra, providing **8-day rolling window weather-risk forecasting and agricultural anomaly scoring**.

Rather than attempting to diagnose a disease without visual input, the ML model calculates a **weather-induced disease susceptibility index (%)**, signaling whether environmental conditions are conducive to fungal, bacterial, or moisture-related crop stress.

---

## 📌 Project Links

* **GitHub Repository:** [https://github.com/ByteCrunchers-HUB/SARVA-MITRA](https://github.com/ByteCrunchers-HUB/SARVA-MITRA)
* **Live Web Application:** [https://sarva-mitra-api.onrender.com/ui/](https://sarva-mitra-api.onrender.com/ui/)
* **API Documentation:** [https://sarva-mitra-api.onrender.com/docs](https://sarva-mitra-api.onrender.com/docs)
* **Setup Guide:** [SETUP.md](../../SETUP.md)

---

## 🔬 Model Overview

- **Algorithm:** LightGBM / Gradient-Boosted Decision Trees ensemble.
- **Model Bundle:** `backend/ml_engine/models/sarva_mitra_risk_model.joblib`
- **Static Soil Features:** `backend/ml_engine/models/static_features.csv`
- **Training Artifacts & Notebook:** `backend/ml_engine/ml model.ipynb`
- **Model Metrics:** Stored in `backend/ml_engine/models/metrics.json`

### Risk Classification Tiers:
* **🟢 Low Risk (`0% - 20%`):** Optimal microclimate. Routine cultural practices recommended. (ML Output Code: `0`)
* **🟡 Moderate Risk (`20% - 60%`):** Elevated humidity or moisture anomalies. Preventative monitoring advised. (ML Output Code: `1`)
* **🔴 High Risk (`60% - 100%`):** Critical conditions (persistent leaf wetness, heavy precipitation, temperature stress). Immediate intervention indicated. (ML Output Code: `1`)

---

## 📂 Directory Structure

```text
backend/ml_engine/
├── backend.py             # Inference API & schema validation (FastAPI)
├── requirements.txt       # ML framework dependencies
├── ml model.ipynb         # Training, feature engineering & cross-validation notebook
├── dataset/               # Training datasets and feature references
├── models/
│   ├── sarva_mitra_risk_model.joblib  # Trained model weights & preprocessors
│   ├── static_features.csv            # Regional static soil grids reference
│   └── metrics.json                   # Cross-validation performance metrics
├── Dockerfile             # Container configuration
└── README.md              # ML engine documentation
```

---

## 📡 API Endpoints (`backend/ml_engine/backend.py`)

Run standalone:
```bash
uvicorn backend.ml_engine.backend:app --host 0.0.0.0 --port 8002 --reload
```

### 1. `GET /health`
Returns model metadata, loaded bundle path, and training metrics.

### 2. `GET /locations`
Lists geographic coordinates represented in the static features table.

### 3. `POST /predict`
Evaluates consecutive 8-day daily sequence plus current sensor reading to predict risk % and category.

* **Example Payload:**
```json
{
  "lat": 16.51,
  "lon": 80.52,
  "target_date": "2026-11-25",
  "history": [
    {
      "date": "2026-11-17",
      "air_temperature_c": 24.5,
      "humidity_pct": 72.0,
      "rainfall_mm": 0.0,
      "sunlight_wm2": 380.0,
      "soil_moisture_pct": 22.0,
      "leaf_wet_days": 1
    }
  ],
  "current": {
    "air_temperature_c": 25.1,
    "humidity_pct": 78.0,
    "rainfall_mm": 0.0,
    "sunlight_wm2": 350.0,
    "soil_moisture_pct": 21.5,
    "leaf_wet_days": 1
  }
}
```

* **Example Response:**
```json
{
  "risk_pct": 14.8,
  "risk_level": "low",
  "risk_bands": { "low_max": 20, "moderate_max": 60 },
  "index_type": "weather_based_proxy",
  "validated": true
}
```

---

## 🧪 Testing

Run model inference verification:

```bash
SARVA_MODEL_PATH=backend/ml_engine/models/sarva_mitra_risk_model.joblib PYTHONPATH=. python backend/tests/test_unified.py
```

---

## 👥 Credits — Team ANVEXA

* **PRIYANSHU SARMA**
* **LIBERATOR NYADUNDU** (ML Model Engineering & Training)
* **RYALI VENKATA SRI VIJAY KARTHIK**
* **Gajulapalli Venkata Raviteja**
* **Sneha Sarma**

**Repository:** [https://github.com/ByteCrunchers-HUB/SARVA-MITRA](https://github.com/ByteCrunchers-HUB/SARVA-MITRA)  
**Live Application:** [https://sarva-mitra-api.onrender.com/ui/](https://sarva-mitra-api.onrender.com/ui/)
