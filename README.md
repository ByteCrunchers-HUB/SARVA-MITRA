# 🌱 Sarva Mitra — Universal Farm Companion

> **One platform. Any farm. Any language.**
>
> Sarva Mitra (*“friend of all”*) is an AI-driven agricultural companion designed to monitor farm conditions, forecast disease and weather risks, and communicate actionable agronomic guidance in conversational language.

---

## 🚜 What is Sarva Mitra?

Farmers face major challenges with unpredictable weather, late detection of crop stress, disease outbreaks, and language barriers. Sarva Mitra solves this by connecting hyper-local environmental data, machine learning risk models, and a grounded Retrieval-Augmented Generation (RAG) advisory assistant into a single feedback loop.

### 💡 Software Telemetry Architecture
To eliminate hardware failure points and make the system instantly accessible without costly ESP32/sensor deployments, **Sarva Mitra integrates a Virtual Telemetry Layer**. It queries open meteorological, satellite, and soil databases for any target coordinates worldwide, streaming continuous real-time and 8-day historical data into the ML and AI models.

---

## 🧩 System Architecture

```text
       ┌────────────────────────────────────────────────────────┐
       │             Virtual Telemetry Service                  │
       │  (Open-Meteo, WeatherAPI, Tomorrow.io, AgroMonitoring) │
       └───────────────────────────┬────────────────────────────┘
                                   │
                     [Live & 8-Day Historical Telemetry]
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │              ML Weather Risk Engine                    │
       │   (8-day consecutive trend anomaly & risk scoring)     │
       └───────────────────────────┬────────────────────────────┘
                                   │
                      [Risk % & Signal (Low/Mod/High)]
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │            RAG Agronomic Advisory Pipeline             │
       │    (MongoDB Atlas Vector Search + Groq gpt-oss-120b)   │
       └───────────────────────────┬────────────────────────────┘
                                   │
           ┌───────────────────────┴───────────────────────┐
           ▼                                               ▼
┌──────────────────────┐                       ┌──────────────────────┐
│  Streamlit Web UI    │                       │  Unified REST API    │
│  (Interactive Chat   │                       │  (FastAPI Dashboard  │
│   & Telemetry Cards) │                       │   & Q&A Endpoints)   │
└──────────────────────┘                       └──────────────────────┘
```

---

## 📂 Repository Structure

```text
SARVA-MITRA/
├── frontend/
│   ├── app.py                     # Interactive Streamlit Web Dashboard & Continuous Chat
│   ├── Dockerfile                 # Container image for Streamlit on Render
│   └── README.md                  # Frontend guide
├── backend/
│   ├── main.py                    # Unified FastAPI Server (combines all modules)
│   ├── telemetry_service/         # Multi-API virtual sensor telemetry engine
│   ├── ml_engine/                 # LightGBM/ensemble disease & weather risk model
│   ├── rag_pipeline/              # MongoDB vector search + Groq LLM advisory
│   ├── tests/
│   │   └── test_unified.py        # End-to-end integration test suite
│   └── README.md                  # Unified API documentation
├── requirements.txt               # Unified project dependencies
├── render.yaml                    # Infrastructure-as-code for Render deployment
└── .env                           # Environment keys and database credentials
```

---

## 🛠️ Quickstart (Local Setup)

### 1. Prerequisites
* Python 3.10 – 3.12 (or WSL2 on Windows)
* Git

### 2. Clone and Setup Environment

```bash
git clone https://github.com/ByteCrunchers-HUB/SARVA-MITRA.git
cd SARVA-MITRA

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure `.env`

Create a `.env` file in the root directory (or update existing):

```dotenv
# MongoDB Atlas Vector Search
MONGODB_URI="your_mongodb_atlas_connection_string"
MONGODB_DATABASE=soil-rag-db
MONGODB_COLLECTION=soil-rag-collection
MONGODB_VECTOR_INDEX=rag_vector_index

# Groq LLM API
GROQ_API_KEY="your_groq_api_key"
GROQ_API_KEY_2="optional_round_robin_key"
GROQ_API_KEY_3="optional_round_robin_key"
GROQ_MODEL="openai/gpt-oss-120b"

# Telemetry APIs
WEATHERAPI_KEY="your_weatherapi_key"
TOMORROW_IO_API_KEY="your_tomorrow_io_key"
AGROMONITORING_API_KEY="your_agromonitoring_key"
OPENWEATHERMAP_API_KEY="your_openweather_key"
```

---

## 🚀 Running the Services

### Option A: Interactive Streamlit UI
Launches the full interactive dashboard with farm selector, real-time metric cards, ML risk indicators, and continuous conversational AI:

```bash
streamlit run frontend/app.py
```
👉 Open browser at: **`http://localhost:8501`**

### Option B: Unified FastAPI Backend
Runs the unified REST API with automatic interactive Swagger documentation:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
👉 Open Swagger UI at: **`http://localhost:8000/docs`**

---

## 📡 Core API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/dashboard` | `GET` | Single call for UI: returns live telemetry, 8-day chart trends, ML risk, and quick advice |
| `/api/chat` | `POST` | Stateful Q&A: injects live telemetry and ML risk into RAG for actionable agronomic guidance |
| `/api/health` | `GET` | Aggregated health check for telemetry APIs, ML model, and vector DB |
| `/api/telemetry/*` | `GET` | Granular telemetry routes (`/current`, `/history`, `/ml-payload`) |
| `/api/ml/*` | `POST` | Direct access to ML engine risk prediction |
| `/api/rag/*` | `POST` | Direct access to agricultural advisory generation |

---

## 🧪 Testing

Run the end-to-end integration test verifying the complete pipeline (Telemetry ➔ ML ➔ RAG):

```bash
SARVA_MODEL_PATH=backend/ml_engine/models/sarva_mitra_risk_model.joblib PYTHONPATH=. python backend/tests/test_unified.py
```

---

## ☁️ Deployment on Render

This repository includes a [`render.yaml`](render.yaml) blueprint that automatically provisions:
1. **`sarva-mitra-ui`**: The Streamlit user interface accessible via public HTTPS.
2. **`sarva-mitra-api`**: The unified FastAPI backend.

### How to Deploy via Render Blueprint:
1. Push your branch to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com/), click **New +** ➔ **Blueprint**.
3. Select this repository. Render will automatically parse `render.yaml`.
4. Enter your secret environment variables (`GROQ_API_KEY`, `MONGODB_URI`, `WEATHERAPI_KEY`, etc.).
5. Click **Apply**. Render will build and deploy both services!

---

## 👥 Contributors

* **Sarva Mitra Team — ByteCrunchers-HUB**
