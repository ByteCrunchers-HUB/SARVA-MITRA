# ⚙️ Sarva Mitra — Comprehensive Setup Guide

Welcome to **Sarva Mitra** (*Universal Farm Companion*). This document provides detailed, end-to-end instructions for configuring, installing, and running all components of the Sarva Mitra platform across Windows, Linux/macOS, and WSL2 environments.

---

## 📌 Quick Reference Links

* **Official Repository:** [GitHub - ByteCrunchers-HUB/SARVA-MITRA](https://github.com/ByteCrunchers-HUB/SARVA-MITRA)
* **Live Web Application:** [https://sarva-mitra-api.onrender.com/ui/](https://sarva-mitra-api.onrender.com/ui/)
* **Interactive API Documentation:** [https://sarva-mitra-api.onrender.com/docs](https://sarva-mitra-api.onrender.com/docs)
* **Team:** **Team ANVEXA**

---

## 📋 System Prerequisites

Before getting started, ensure you have the following installed on your system:

| Tool | Recommended Version | Purpose |
|---|---|---|
| **Python** | `3.10` – `3.12` | Backend, ML risk engine, RAG pipeline, and Streamlit |
| **Git** | `>= 2.30` | Source control and cloning |
| **Node.js & npm** | `Node >= 18.x`, `npm >= 9.x` | *(Optional)* For the Expo/React Native mobile application |
| **Docker** | `>= 24.x` | *(Optional)* For containerized deployment |

---

## 🚀 1-Step Automated Setup

We provide automated setup scripts to bootstrap your environment in one command:

### On Linux / macOS / WSL:
```bash
chmod +x setup.sh
./setup.sh
```

### On Windows (Command Prompt / PowerShell):
```cmd
setup.bat
```

These scripts verify your Python installation, create a dedicated `.venv` virtual environment, upgrade `pip`, and install all project dependencies from `requirements.txt`.

---

## 🛠️ Manual Step-by-Step Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/ByteCrunchers-HUB/SARVA-MITRA.git
cd SARVA-MITRA
```

### Step 2: Create and Activate Virtual Environment

**Linux / macOS / WSL:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### Step 3: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔑 Environment Configuration (`.env`)

Create a `.env` file in the project root directory. You can copy the template below:

```dotenv
# ===================================================================
# SARVA MITRA CONFIGURATION
# ===================================================================

# --- MongoDB Atlas Vector Search (RAG Knowledge Base) ---
MONGODB_URI="your_mongodb_atlas_connection_string"
MONGODB_DATABASE=soil-rag-db
MONGODB_COLLECTION=soil-rag-collection
MONGODB_VECTOR_INDEX=rag_vector_index

# --- Groq LLM API Keys (Supports Round-Robin Rotation) ---
GROQ_API_KEY="your_primary_groq_api_key"
GROQ_API_KEY_2="your_secondary_groq_api_key"    # Optional fallback
GROQ_API_KEY_3="your_tertiary_groq_api_key"     # Optional fallback
GROQ_MODEL="openai/gpt-oss-120b"

# --- Virtual Telemetry APIs ---
WEATHERAPI_KEY="your_weatherapi_key"
TOMORROW_IO_API_KEY="your_tomorrow_io_key"
AGROMONITORING_API_KEY="your_agromonitoring_key"
OPENWEATHERMAP_API_KEY="your_openweather_key"

# --- Model & Path Settings ---
SARVA_MODEL_PATH=backend/ml_engine/models/sarva_mitra_risk_model.joblib
SARVA_STATIC_PATH=backend/ml_engine/models/static_features.csv
```

> **Note on Telemetry Fallback:** If secondary telemetry API keys are not supplied, the system seamlessly pulls real-time and historical weather/soil data from **Open-Meteo** and **WeatherAPI** without breaking the pipeline.

---

## 🏃 Running the Application Services

You can run Sarva Mitra using any of the following interfaces:

### Option 1: Unified FastAPI Server (Serves Backend & Web UI) — Recommended

The unified backend combines Telemetry, ML Engine, RAG Pipeline, and also serves the modern Web App directly at `/ui/`:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

* 🌐 **Web Application:** Open [http://localhost:8000/ui/](http://localhost:8000/ui/) in your browser.
* 📚 **Interactive Swagger Docs:** Open [http://localhost:8000/docs](http://localhost:8000/docs).
* 📑 **ReDoc Documentation:** Open [http://localhost:8000/redoc](http://localhost:8000/redoc).

---

### Option 2: Interactive Streamlit Dashboard

For quick parameter tweaking and diagnostics:

```bash
streamlit run frontend/app.py
```

* 🖥️ **Streamlit UI:** Open [http://localhost:8501](http://localhost:8501).

---

### Option 3: Mobile Application (Expo / React Native)

To develop or preview the mobile app on iOS/Android:

```bash
cd frontend
npm install
npx expo start
```

* Scan the QR code using the **Expo Go** app on your phone, or press `a` for Android Emulator / `i` for iOS Simulator.

---

## 🧪 Verification and Testing

Run the full end-to-end integration test suite to verify Telemetry, ML, and RAG connectivity:

```bash
SARVA_MODEL_PATH=backend/ml_engine/models/sarva_mitra_risk_model.joblib PYTHONPATH=. python backend/tests/test_unified.py
```

Expected output:
```text
[PASS] Telemetry Service: Fetched current & 8-day history
[PASS] ML Risk Engine: Scored 8-day consecutive sequence
[PASS] RAG Pipeline: Retrieved agronomic documents and generated structured response
```

---

## 🐳 Docker Deployment

To build and run Sarva Mitra inside a Docker container:

```bash
# Build the Docker image
docker build -t sarva-mitra-backend -f backend/Dockerfile .

# Run the container
docker run -d -p 8000:8000 --env-file .env --name sarva-mitra sarva-mitra-backend
```

Access the UI at `http://localhost:8000/ui/`.

---

## 👥 Credits & Team ANVEXA

Developed with ❤️ by **Team ANVEXA**:

* **PRIYANSHU SARMA**
* **LIBERATOR NYADUNDU**
* **RYALI VENKATA SRI VIJAY KARTHIK**
* **Gajulapalli Venkata Raviteja**
* **Sneha Sarma**

**Repository:** [https://github.com/ByteCrunchers-HUB/SARVA-MITRA](https://github.com/ByteCrunchers-HUB/SARVA-MITRA)  
**Live Application:** [https://sarva-mitra-api.onrender.com/ui/](https://sarva-mitra-api.onrender.com/ui/)
