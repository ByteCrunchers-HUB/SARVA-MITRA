# Sarva Mitra RAG Pipeline

A compact, stateless agricultural advisory pipeline using:

- Existing weather-risk ML engine
- MongoDB Atlas Vector Search
- Hugging Face sentence embeddings
- Groq LLM
- Parent/child agricultural documents

The ML model supplies a risk signal. It does not identify a disease.

## Setup

```bash
.venv/bin/python -m pip install -r backend/rag_pipeline/requirements.txt
```

Required `.env` values:

```dotenv
MONGODB_USERNAME=<username>
MONGODB_PASSWORD=<password>
GROQ_API_KEY=<groq-key>
MONGODB_DATABASE=soil-rag-db
MONGODB_COLLECTION=soil-rag-collection
MONGODB_VECTOR_INDEX=rag_vector_index
ML_ENGINE_URL=https://sarvamitra.onrender.com
```

## Ingest

Place final corpus files in `docs/`, then run:

```bash
.venv/bin/python -m backend.rag_pipeline.ingest
```

Replace production records:

```bash
.venv/bin/python -m backend.rag_pipeline.ingest --apply
```

## Test retrieval

```bash
.venv/bin/python -m backend.rag_pipeline.query \
  "tomato cool humid wet leaves" --k 6
```

## Run API

```bash
.venv/bin/python -m uvicorn backend.rag_pipeline.main:app \
  --host 0.0.0.0 --port 8001
```

Endpoints:

- `GET /health`
- `POST /v1/advisory`
- `POST /advisory` (legacy compatibility alias; deprecated)
- `POST /predict-and-advice` (demo convenience; deprecated)

Example request:

```json
{
  "crop": "tomato",
  "location": "Vijayawada",
  "question": "What should I inspect after heavy rain?",
  "ml_prediction": {
    "prediction": {
      "risk_pct": 67.51,
      "risk_level": "high"
    }
  },
  "readings": {
    "temperature_c": 25.86,
    "humidity_pct": 79.15,
    "rainfall_mm": 35.31,
    "soil_moisture_pct": 57
  },
  "chat_history": []
}
```

Chat history is stateless: the frontend sends the recent messages and receives
the updated history in the response. The API does not store sessions.

## End-to-end flow

```text
Sensor history
  -> Existing ML engine /predict
  -> risk_pct + risk_level
  -> low = ML_OUTPUT 0
  -> moderate/high = ML_OUTPUT 1
  -> MongoDB child-section retrieval
  -> complete parent documents
  -> Groq structured advisory
  -> human answer + JSON + retrieval provenance
```

## Response fields

| Field | Purpose |
|---|---|
| `ml_output` | `0` for healthy/betterment mode; `1` for abnormality/advisory mode |
| `ml_prediction` | Original result from the existing ML engine |
| `answer` | Human-readable farmer advisory |
| `structured` | Machine-readable response for the frontend |
| `retrieval_context.query` | Exact text sent to vector retrieval |
| `retrieval_context.matches` | DOC_ID, section, file, score, and retrieval type |
| `retrieval_context.documents_sent` | Complete parent documents sent to Groq |
| `chat_history` | Updated stateless conversation turns |

## Verified test cases

### 1. Low-risk normal readings

Latest ML history:

```json
{
  "soil_moisture_pct": 26,
  "sunlight_wm2": 220.2546296,
  "rainfall_mm": 0,
  "leaf_wet_days": 0
}
```

RAG readings:

```json
{
  "temperature_c": 24.28,
  "humidity_pct": 60.09,
  "soil_moisture_pct": 26,
  "rainfall_mm": 0,
  "sunlight_wm2": 220.2546296,
  "leaf_wet_days": 0
}
```

ML response:

```json
{
  "risk_pct": 1.06,
  "risk_level": "low",
  "index_type": "weather_based_proxy",
  "validated": false
}
```

RAG response:

```text
No abnormality signal from the model.

Maintain regular deep watering and even soil moisture.
Use mulch to retain moisture.
Maintain good airflow and plant spacing.
Remove debris, clean tools, and scout shaded areas.
```

Retrieved documents:

```text
22_healthy_state_betterments
24_field_hygiene
21_soil_moisture_effects_by_disease
19_heat_stress_fruit_set_tomato
20_soil_salinity_ec_tomato
```

Mode: `healthy`

### 2. Moderate-risk leaf-wetness readings

Latest ML history:

```json
{
  "soil_moisture_pct": 24,
  "sunlight_wm2": 204.0509259,
  "rainfall_mm": 0.5,
  "leaf_wet_days": 1
}
```

ML response:

```json
{
  "risk_pct": 37.96,
  "risk_level": "moderate",
  "index_type": "weather_based_proxy",
  "validated": false
}
```

RAG response:

```text
The model flagged an unusual pattern. This is a warning, not a diagnosis.

Possible checks:
1. Fusarium wilt
   Look for sudden wilting, yellowing and brown stem streaks.
2. Bacterial leaf spot
   Look for small water-soaked spots that become brown.

Avoid overwatering, improve drainage, remove symptomatic plants,
clean tools and use disease-free transplants.
```

Retrieved documents:

```text
02_weather_thresholds_by_disease
10_fusarium_wilt_tomato
21_soil_moisture_effects_by_disease
08_tomato_bacterial_leaf_spot
```

Mode: `abnormality`

### 3. High-risk heavy-rain readings

Latest ML history:

```json
{
  "soil_moisture_pct": 57,
  "sunlight_wm2": 119.0972222,
  "rainfall_mm": 35.31,
  "leaf_wet_days": 1
}
```

Additional RAG readings:

```json
{
  "temperature_c": 25.86,
  "humidity_pct": 79.15
}
```

ML response:

```json
{
  "risk_pct": 67.51,
  "risk_level": "high",
  "index_type": "weather_based_proxy",
  "validated": false
}
```

RAG response:

```text
The model flagged an unusual pattern. This is a warning, not a diagnosis.

Possible checks:
1. Bacterial leaf spot
   Look for water-soaked spots on leaves.
2. Fusarium wilt
   Look for sudden yellowing, wilting and stem discoloration.
3. Gray mold
   Look for fuzzy grey growth in damp shaded areas.

Improve drainage and airflow, avoid overhead watering,
remove debris and inspect plants for symptoms.
```

Retrieved documents:

```text
02_weather_thresholds_by_disease
10_fusarium_wilt_tomato
21_soil_moisture_effects_by_disease
08_tomato_bacterial_leaf_spot
```

Mode: `abnormality`

### 4. Low-risk dry-soil readings

Latest ML history:

```json
{
  "soil_moisture_pct": 17,
  "sunlight_wm2": 200.462963,
  "rainfall_mm": 0,
  "leaf_wet_days": 0
}
```

ML response:

```json
{
  "risk_pct": 2.38,
  "risk_level": "low",
  "index_type": "weather_based_proxy",
  "validated": false
}
```

RAG response:

```text
No abnormality signal from the model.

No documented threshold is currently approached.
Water at the base in the late morning.
Avoid overhead irrigation.
Remove debris and control weeds.
Mulch if soil moisture falls further.
```

Retrieved documents:

```text
22_healthy_state_betterments
24_field_hygiene
21_soil_moisture_effects_by_disease
19_heat_stress_fruit_set_tomato
20_soil_salinity_ec_tomato
```

Mode: `healthy`

### 5. Moderate-risk mixed-rain readings

Latest ML history:

```json
{
  "soil_moisture_pct": 50,
  "sunlight_wm2": 257.6388889,
  "rainfall_mm": 0.71,
  "leaf_wet_days": 1
}
```

ML response:

```json
{
  "risk_pct": 27.37,
  "risk_level": "moderate",
  "index_type": "weather_based_proxy",
  "validated": false
}
```

RAG response:

```text
The model flagged an unusual pattern. This is a warning, not a diagnosis.

Possible checks:
1. Bacterial leaf spot
   Look for water-soaked lower-leaf spots that become brown.
2. Fusarium wilt
   Look for sudden yellowing and wilting of older leaves.
3. Damping-off
   Look for soft waterlogged stems near the soil line.

Keep soil from remaining unnecessarily wet.
Improve drainage and airflow.
Inspect seedlings and remove affected plants.
```

Retrieved documents:

```text
02_weather_thresholds_by_disease
10_fusarium_wilt_tomato
21_soil_moisture_effects_by_disease
08_tomato_bacterial_leaf_spot
```

Mode: `abnormality`

## Final behavior

- A low ML risk produces crop-health and betterment advice.
- A moderate or high ML risk produces evidence-based possible-condition checks.
- The ML output does not name a disease.
- Sensors do not confirm a disease.
- Every disease possibility is linked to retrieved corpus DOC_IDs.
- The API remains stateless; no server-side chat database is used.

## Render deployment

The repository includes `render.yaml` for two web services:

1. `sarva-mitra-ml` from `backend/ml_engine/Dockerfile`
2. `sarva-mitra-rag` from `backend/rag_pipeline/Dockerfile`

Set these RAG environment values in Render:

```dotenv
MONGODB_URI=<mongodb-atlas-uri>
GROQ_API_KEY=<groq-api-key>
ML_ENGINE_URL=https://<sarva-mitra-ml>.onrender.com
MONGODB_DATABASE=soil-rag-db
MONGODB_COLLECTION=soil-rag-collection
MONGODB_VECTOR_INDEX=rag_vector_index
RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RAG_EMBEDDING_DIMENSION=384
FASTEMBED_CACHE_PATH=/app/.fastembed-cache
GROQ_MODEL=openai/gpt-oss-120b
CHAT_HISTORY_LIMIT=12
```

Swagger testing:

- ML: `https://<sarva-mitra-ml>.onrender.com/docs`
- RAG: `https://<sarva-mitra-rag>.onrender.com/docs`

The RAG Swagger `/predict-and-advice` request includes a valid eight-day
history example. The endpoint calls `/predict` on the ML service and then
calls RAG retrieval and Groq before returning one combined response.

## Swagger and demo endpoints

When deployed, open:

- RAG Swagger: `https://<rag-service>.onrender.com/docs`
- RAG health: `https://<rag-service>.onrender.com/health`
- ML Swagger: `https://<ml-service>.onrender.com/docs`
- ML health: `https://<ml-service>.onrender.com/health`

Use `/predict-and-advice` for the simplest demo. It accepts ML history and
calls both services internally:

```json
{
  "device_id": "sample-device",
  "location": "Vijayawada",
  "lat": 16.51,
  "lon": 80.52,
  "target_date": "2000-01-09",
  "crop": "tomato",
  "question": "What should I inspect after heavy rain?",
  "history": [
    {
      "date": "2000-01-01",
      "soil_moisture_pct": 50,
      "sunlight_wm2": 257.64,
      "rainfall_mm": 0.71,
      "leaf_wet_days": 1
    }
  ],
  "readings": {
    "temperature_c": 25.86,
    "humidity_pct": 79.15
  }
}
```

For `/predict-and-advice`, the history must contain at least eight consecutive
daily records. The target date must be one day after the final history date.
The RAG endpoint can still accept an already-computed `ml_prediction` through
`/v1/advisory` or `/advisory`.

## Render environment variables

ML service:

```dotenv
SARVA_MODEL_PATH=models/sarva_mitra_risk_model.joblib
```

RAG service:

```dotenv
MONGODB_URI=mongodb+srv://<username>:<password>@<host>/<database>
MONGODB_DATABASE=soil-rag-db
MONGODB_COLLECTION=soil-rag-collection
MONGODB_VECTOR_INDEX=rag_vector_index
GROQ_API_KEY=<groq-key>
GROQ_MODEL=openai/gpt-oss-120b
RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
ML_ENGINE_URL=https://<ml-service>.onrender.com
CHAT_HISTORY_LIMIT=12
CORS_ORIGINS=*
```
