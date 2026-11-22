# SARVA-MITRA - IoT & Hardware Subsystem (`backend/iot`)

The **IoT & Hardware Subsystem** is the real-time physical telemetry gateway for **SARVA-MITRA**. It handles non-blocking Serial communications with the **ESP32 microcontroller**, ingests physical sensor data (Air Temperature, Relative Humidity, Soil Moisture), persists readings into SQLite, integrates with Open-Meteo external weather data, and triggers the ML Engine & RAG pipelines.

---

## Architecture Overview

```
 [ESP32 NodeMCU]
  ├── DHT11 (GPIO 27) ---------> [USB Serial @ 115200]
  └── Soil Sensor (GPIO 35)              │
                                         ▼
                             [FastAPI IoT Gateway]
                                         │
                 ┌───────────────────────┼────────────────────────┐
                 ▼                       ▼                        ▼
         [SQLite Storage]      [Open-Meteo Weather]      [ML Engine & RAG]
          (Historical DB)       (Rainfall, Sunlight)     (sarva-mitra.onrender)
```

---

## Hardware Specifications & Pinout

| Component | ESP32 Pin | Interface | Description |
| :--- | :--- | :--- | :--- |
| **DHT11 Data** | `GPIO 27` | 1-Wire Digital | Measures Ambient Air Temperature (°C) & Humidity (%) |
| **Soil Moisture AO** | `GPIO 35` (ADC1_CH7) | 12-Bit Analog | Measures Volumetric Soil Water Content |
| **DHT11 VCC / GND** | `3.3V` / `GND` | Power | 3.3V Supply Rail |
| **Soil Sensor VCC / GND** | `3.3V` or `VIN (5V)` / `GND` | Power | Ground & Power Rail |
| **Heartbeat LED** | `GPIO 2` | Onboard LED | Blinks briefly on each valid JSON transmission |

> **Firmware Location**: [`firmware/esp32_sensor_node/esp32_sensor_node.ino`](./firmware/esp32_sensor_node/esp32_sensor_node.ino)

### ESP32 Telemetry Format (USB Serial)
The firmware transmits single-line JSON frames every 5 seconds:
```json
{"device_id":"ESP32_01","temperature":27.4,"humidity":65.2,"soil_moisture":48}
```

---

## Directory Structure

```
backend/iot/
├── api/                   # FastAPI route handlers
│   ├── health.py          # /api/health endpoint
│   ├── history.py         # /api/history query & export endpoints
│   ├── process.py         # /api/process end-to-end integration orchestrator
│   ├── sensors.py         # /api/sensors/latest & /status endpoints
│   └── weather.py         # /api/weather endpoint
├── database/              # SQLite persistent storage
│   ├── database.py        # Async SQLite database initializer
│   └── sensor_repository.py # Repository CRUD operations
├── firmware/              # ESP32 Arduino C++ firmware
│   └── esp32_sensor_node/
│       └── esp32_sensor_node.ino
├── hardware/              # Hardware communication layer
│   └── serial_receiver.py # Asynchronous PySerial background worker
├── schemas/               # Pydantic data validation schemas
│   ├── ml_schema.py       # ML request/response contracts
│   ├── rag_schema.py      # RAG request/response contracts
│   └── sensor_schema.py   # Hardware & weather sensor contracts
├── services/              # Business logic & external API clients
│   ├── data_integration.py # 8-day payload compilation
│   ├── history_service.py # Historical record aggregation
│   ├── ml_service.py      # ML Engine HTTP client
│   ├── rag_service.py     # RAG Pipeline HTTP client
│   └── weather_service.py # Open-Meteo Weather API client
├── utils/                 # Helpers and validators
│   └── validation.py
├── .dockerignore
├── .env.example           # Template environment configuration
├── .gitignore
├── config.py              # Pydantic-settings centralized config
├── Dockerfile             # Container definition
├── main.py                # FastAPI ASGI application entrypoint
└── requirements.txt       # Python dependencies
```

---

## Quickstart Guide

### 1. Setup Python Virtual Environment
```powershell
cd backend/iot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env`:
```powershell
cp .env.example .env
```
Ensure your ESP32 COM port is set in `.env`:
```ini
SERIAL_PORT=COM9
SERIAL_BAUDRATE=115200
DEVICE_ID=ESP32_01
ML_API_URL=http://sarva-mitra.onrender.com/predict
RAG_API_URL=http://localhost:8002/rag/query
```

> **Important**: Ensure Arduino IDE's Serial Monitor is **CLOSED** when running the backend, as only one process can bind to the COM port simultaneously.

### 3. Run the Backend Server
```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- Live Telemetry: [http://127.0.0.1:8000/api/sensors/latest](http://127.0.0.1:8000/api/sensors/latest)

### Use the ESP32 with the Render deployment

Render cannot read `COM9` on your Windows computer. The deployed API returns `503`
from `GET /api/sensors/latest` until it receives a reading. Keep the backend
deployed, connect the ESP32 to your computer, and run this forwarder from the
`backend/iot` directory on that computer:

```powershell
python -m pip install -r requirements.txt
python tools/serial_forwarder.py --port COM9 --baud 115200 --url https://sarva-mitra-0k9a.onrender.com/api/sensors/data
```

Keep the command window open while you want live readings. Close Arduino Serial
Monitor and any locally running backend first, since they can hold COM9 and stop
the forwarder from opening it. The forwarder prints `[OK]` when Render accepts a
reading. Then `/api/sensors/latest` returns the latest forwarded reading. If your
Render service URL changes, replace it in the command.

For the Render service environment, set `ENABLE_SERIAL=false`; the local
forwarder owns COM9 and sends readings over HTTPS. This setting disables the
cloud server's hardware polling; it does not disable `POST /api/sensors/data`.

---

## Key API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status and component checks |
| `GET` | `/api/sensors/latest` | Latest validated ESP32 telemetry (Temp, Humidity, Soil Moisture) |
| `GET` | `/api/sensors/status` | Serial port connection state |
| `POST` | `/api/sensors/simulate` | Inject mock readings (for testing without physical hardware) |
| `GET` | `/api/weather/daily` | Environmental weather data for target coordinates |
| `GET` | `/api/history` | Historical database records query |
| `POST` | `/api/process` | **Main Orchestrator**: Collects sensor + weather -> builds 8-day history -> invokes ML engine -> invokes RAG pipeline |
