# SARVA-MITRA API Orchestrator

This FastAPI service is the software-only integration layer for the SARVA-MITRA
farm-risk project. It accepts a farm location and crop from an API client, fetches
daily environmental history, calls the independent ML prediction API, then sends
the prediction and source data to the RAG advisory API. The main flow does not
require an ESP32 or serial port.

```text
API client (place name or coordinates)
          │
          ▼
FastAPI ── Open-Meteo Geocoding (place name → coordinates)
   │
   ├────── NASA POWER Daily API (7 days of climate/soil-wetness data)
   │
   ├────── ML API /predict (risk estimate)
   │
   └────── RAG API /advisory (explanation and actions)
```

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open API documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Run an analysis

Send a place name; the service geocodes it:

```json
{
  "location": "Vijayawada, Andhra Pradesh",
  "crop": "tomato",
  "question": "How should I reduce disease risk this week?"
}
```

Or send coordinates directly:

```json
{
  "latitude": 16.51,
  "longitude": 80.52,
  "location": "Vijayawada",
  "crop": "tomato"
}
```

`POST /api/process` requires a place name or both coordinates and a crop from the
UI request body; it does not substitute server-default location or crop values.
The backend resolves the coordinates, fetches seven consecutive daily
records from NASA POWER, converts them to the ML request schema, calls ML, then
calls RAG. You can set `target_date` to analyze a specific date. If omitted, it
uses the current date in India Standard Time and fetches the seven preceding days.

The fetched inputs include daily temperature (`T2M`), relative humidity (`RH2M`),
solar radiation (`ALLSKY_SFC_SW_DWN`), precipitation (`PRECTOTCORR`), and surface
soil wetness (`GWETTOP`). The soil-wetness value is a NASA model estimate, not a
live soil probe measurement. Solar energy is converted to mean W/m² and wetness
fraction to percent. NASA POWER daily data may be delayed; the API returns an
error if it cannot supply a complete 7-day window rather than inventing readings.

## Model locations

The deployed ML model has static soil features for a finite set of trained points.
Use `GET /api/locations` to retrieve them. For a submitted place or coordinate,
the backend selects the nearest trained point within 250 km. It fetches weather
at the requested coordinates but uses the nearest trained point for the model's
static soil features. The response metadata reports both coordinate pairs and
the distance. A request farther than 250 km from every trained point is rejected.

## Configuration

Set these values in `.env` locally or in the Render service environment:

```text
ML_API_URL=https://sarva-mitra-ml.onrender.com/predict
RAG_API_URL=https://sarva-mitra-rag.onrender.com/advisory
LATITUDE=16.51
LONGITUDE=80.52
LOCATION_NAME=Vijayawada
ENABLE_SERIAL=false
```

`NASA_POWER_DAILY_URL` and `GEOCODING_URL` have public defaults. No API key is
required for these data requests. The service caches external data briefly to
reduce repeated calls.

## Main endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Backend health |
| `GET` | `/api/locations` | Coordinates supported by the ML model |
| `POST` | `/api/process` | Fetch API data, call ML, then call RAG |
| `GET` | `/api/weather` | Daily weather query |
| `GET` | `/api/history` | Legacy local history records |

The `/api/sensors/*` routes and firmware remain only for legacy hardware demos;
they are not used by `/api/process`.
