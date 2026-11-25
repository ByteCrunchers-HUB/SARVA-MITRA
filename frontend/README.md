# 🌱 Sarva Mitra - Streamlit Frontend UI

An interactive web dashboard and continuous AI assistant for testing Sarva Mitra without physical IoT hardware.

This folder also contains the Expo/React Native mobile app (`src/app/`). It uses the unified FastAPI service, not the Python modules directly.

---

## 📱 Mobile App (Expo)

From `frontend/`:

```bash
npm install
npx expo start
```

Set the unified API URL in `frontend/.env` (copy from `.env.example`):

```bash
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
```

Use `http://10.0.2.2:8000` for an Android emulator or `http://<your-computer-lan-ip>:8000` for a physical device on the same Wi-Fi. Start the API from the repo root with:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Checks:

```bash
npx tsc --noEmit
npx expo lint
npx expo-doctor
```

---

## 🚀 Running Locally

From the project root:

```bash
# Launch Streamlit with virtual environment
.venv/bin/streamlit run frontend/app.py
```

Open your browser at:
👉 **`http://localhost:8501`**

---

## ☁️ Deploying & Accessing on Render

When deployed on Render, Streamlit runs as a cloud Web Service and can be accessed from any phone, tablet, or PC browser via a public HTTPS URL.

### Deployment Steps on Render

1. **Option A: Via Blueprint (`render.yaml`)**
   * Connect your GitHub repo to Render and choose **New Blueprint Instance**.
   * Render automatically configures `sarva-mitra-ui` using `frontend/Dockerfile`.
   * Add your secret environment variables (`GROQ_API_KEY`, `MONGODB_URI`, `WEATHERAPI_KEY`, etc.).

2. **Option B: Manual Web Service Setup**
   * In Render, click **New +** ➔ **Web Service**.
   * Connect your repository: `ByteCrunchers-HUB/SARVA-MITRA`.
   * **Language / Environment:** `Docker` (Dockerfile Path: `frontend/Dockerfile`, Context: `.`)
     * *OR* if using native Python:
       * **Build Command:** `pip install -r requirements.txt`
       * **Start Command:** `streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false`
   * **Plan:** Free
   * **Environment Variables:** Add keys from `.env` (`MONGODB_URI`, `GROQ_API_KEY`, `WEATHERAPI_KEY`, `SARVA_MODEL_PATH=backend/ml_engine/models/sarva_mitra_risk_model.joblib`).
   * Click **Create Web Service**.

### How to Access:
Once Render completes building:
* Render assigns a public URL such as `https://sarva-mitra-ui.onrender.com`.
* Open that URL in any browser to interact with the live telemetry cards, ML model, and AI assistant!

---

## ✨ Features

1. **📍 Location & Crop Selector:**
   * Select from presets (**Vijayawada**, **Bengaluru**, **Guntur**, **Kurnool**, **Anantapur**, **Hyderabad**) or enter custom coordinates.
   * Supported crops: **Tomato 🍅**, **Chilli 🌶️**, **Ragi 🌾**.

2. **📡 Real-Time Telemetry Cards:**
   * Air Temperature (°C), Relative Humidity (%), Soil Moisture (%), Rainfall (mm), and Solar Radiation (W/m²).

3. **🧠 ML Risk Status Banner:**
   * Displays the risk percentage and color-coded risk alert (Low 🟢 / Moderate 🟡 / High 🔴).

4. **💬 Continuous AI Agronomic Chat (RAG):**
   * Pre-loads the initial proactive diagnosis as the first assistant message.
   * Full continuous conversation with persistent memory.
   * Quick question chips for testing common field scenarios.
