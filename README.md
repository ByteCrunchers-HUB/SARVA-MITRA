# SARVA-MITRA — API-first farm risk and advisory

SARVA-MITRA is a software-only hackathon project. A client submits a farm's place
name or coordinates; the backend gets environmental history from public APIs,
asks the ML service for a risk estimate, then asks the RAG service to explain the
result and suggest actions. The analysis flow does not need an ESP32, COM port, or
live sensor.

```text
Client ── place name / coordinates ──► FastAPI orchestrator
                                          ├─ Open-Meteo Geocoding
                                          ├─ NASA POWER daily climate data
                                          ├─ ML API: risk estimate
                                          └─ RAG API: explanation and actions
```

## What happens for one request

1. The UI sends a place name or both coordinates, a crop, and optional question
   as fields in the `POST /api/process` JSON body. The backend does not silently
   replace missing UI values with defaults.
2. The backend geocodes a place name when coordinates were not supplied.
3. It selects the nearest location supported by the trained ML model, within 250 km.
4. It fetches the seven preceding daily records from NASA POWER for the requested
   coordinates and maps them into the ML API's input schema.
5. It sends the history and model-reference coordinates to the ML `/predict` API.
6. It sends the ML response, climate history, location, crop, and question to the
   RAG `/advisory` API and returns the combined result.

NASA POWER provides daily air temperature, relative humidity, solar radiation,
precipitation, and a surface soil-wetness estimate. The soil-wetness estimate is
not a live soil probe measurement. The backend converts the values to the units
expected by this project's ML model and returns the seven source records with the
analysis response. If the source does not return a complete seven-day history,
the backend reports an error instead of inserting made-up sensor values.

## Run locally

From the repository root:

```powershell
cd backend/iot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## API usage

List the coordinate points available in the current ML model:

```http
GET /api/locations
```

Analyze a named location:

```http
POST /api/process
Content-Type: application/json
```

```json
{
  "location": "Vijayawada, Andhra Pradesh",
  "crop": "tomato",
  "question": "How can I reduce crop disease risk this week?"
}
```

Or supply coordinates directly:

```json
{
  "latitude": 16.51,
  "longitude": 80.52,
  "location": "Vijayawada",
  "crop": "tomato"
}
```

`target_date` is optional. It defaults to the current date in India Standard Time;
the seven input records are the seven days immediately before it. The response
includes `environment_history`, `ml_response`, `rag_response`, and metadata with
the requested coordinates and the ML reference point.

## Location/model limitation

The deployed ML model has static soil features for a finite list of trained
points. `GET /api/locations` exposes that list. Other coordinates are matched to
the nearest trained point if they are within 250 km. Climate history is fetched
for the requested coordinates, while static soil features come from the nearest
trained point; the response identifies this approximation. Locations farther
than 250 km from a trained point are rejected. The model's current training data
is India-specific.

## Services and deployment

| Component | Responsibility |
| --- | --- |
| `backend/iot` | API orchestrator, geocoding, NASA POWER data mapping, ML/RAG calls |
| `backend/ml_engine` | Trained risk model and `/predict` plus `/locations` endpoints |
| `backend/rag_pipeline` | Retrieval-backed advisory API |

The API orchestrator can be deployed as a Render web service with its root
directory set to `backend/iot`. Configure `ML_API_URL` and `RAG_API_URL` in its
environment. The ML service also needs to deploy the `/locations` endpoint from
`backend/ml_engine/backend.py` so the orchestrator can match supported model
points.

Example environment values are in [`backend/iot/.env.example`](backend/iot/.env.example).
NASA POWER and Open-Meteo Geocoding are called without API keys. The optional
`/api/sensors/*` endpoints and ESP32 firmware remain in the repository for older
demos, but they are not part of the main request path.

## Project status

Hackathon prototype. Data-source coverage, model location matching, risk
calibration, and RAG advisories need validation before real farm decisions.
