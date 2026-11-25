# ML and RAG Sample Records Tested

> **Project Repository:** [https://github.com/ByteCrunchers-HUB/SARVA-MITRA](https://github.com/ByteCrunchers-HUB/SARVA-MITRA)  
> **Live Web Application:** [https://sarva-mitra-api.onrender.com/ui/](https://sarva-mitra-api.onrender.com/ui/)  
> **Engineered by:** **Team ANVEXA**

**Tested:** 2026-11-22
**Environment:** Local ML engine and local RAG API  
**Result:** PASS - 5 of 5 ML predictions and 5 of 5 RAG advisories succeeded

## Test method

1. Send an eight-day history payload to local `POST /predict`.
2. Verify that the ML engine returned HTTP 200 and a schema 1.0 prediction.
3. Send the actual ML response to local `POST /advisory` with the backend-compatible location, sensor, weather, and crop fields.
4. Verify that RAG returned HTTP 200, mapped the risk correctly, and produced a healthy or abnormality structured response.

The local services were started with:

```bash
.venv/bin/python -m uvicorn backend:app --host 127.0.0.1 --port 8000
.venv/bin/python -m uvicorn backend.rag_pipeline.main:app --host 127.0.0.1 --port 8002
```

## Result summary

| Case | Crop / location | Sensor conditions | ML risk | ML label | RAG output | RAG mode | Verdict |
|---|---|---|---:|---|---:|---|---|
| 1 | Tomato / Vijayawada | 24.3 C, 60.1% humidity, 26% soil moisture, no rain | 2.48% | low | 0 | healthy | PASS |
| 2 | Chilli / Guntur | 27.8 C, 82% humidity, 54% soil moisture, 18 mm rain | 66.16% | high | 1 | abnormality | PASS |
| 3 | Tomato / Kurnool | 29.5 C, 88% humidity, 91% soil moisture, 55 mm rain | 89.57% | high | 1 | abnormality | PASS |
| 4 | Ragi / Bengaluru | 23 C, 45% humidity, 18% soil moisture, no rain | 4.90% | low | 0 | healthy | PASS |
| 5 | Chilli / Anantapur | 26.4 C, 72% humidity, 38% soil moisture, 6.5 mm rain | 54.47% | moderate | 1 | abnormality | PASS |

## Shared backend-compatible envelope

Each RAG request used this structure:

```json
{
  "device_id": "ESP32_SAMPLE",
  "location": {
    "name": "LOCATION",
    "lat": 16.51,
    "lon": 80.65
  },
  "target_date": "2026-11-23",
  "crop": "tomato",
  "question": "What should I inspect and do for this crop?",
  "current_sensor_data": {
    "temperature": 29.5,
    "humidity": 68.0,
    "soil_moisture": 86.0
  },
  "weather_data": {
    "rainfall_mm": 26.0,
    "sunlight_wm2": 132.0
  },
  "ml_response": {}
}
```

## 1. Low-risk normal tomato

**ML output**

```json
{
  "risk_pct": 2.48,
  "risk_level": "low",
  "risk_bands": {"low_max": 20, "moderate_max": 60},
  "index_type": "weather_based_proxy",
  "validated": false
}
```

**RAG output**

- HTTP status: `200`
- `ml_output`: `0`
- `response_mode`: `healthy`
- Overview: No abnormality signal for tomato under the supplied normal sensor conditions.
- Key recommendations: Maintain base watering, remove debris and weeds, improve drainage, and monitor leaf wetness.
- Retrieved documents: `22_healthy_state_betterments`, `24_field_hygiene`, `21_soil_moisture_effects_by_disease`, `19_heat_stress_fruit_set_tomato`, tomato field and irrigation documents.

**Verdict:** PASS

## Groq key rotation

The RAG service supports three keys configured in `.env`:

- `GROQ_API_KEY`
- `GROQ_API_KEY_2`
- `GROQ_API_KEY_3`

Keys are selected round-robin for each LLM invocation. If an invocation fails with a Groq API error, the service tries the remaining configured keys once each before returning a 503 advisory-service error.

## Six-request live Groq load check

**Tested:** 2026-11-22
**Method:** Six sequential real `/advisory` requests, each using a Groq LLM invocation.

| Request | Device | RAG mode | HTTP status | Answer generated |
|---:|---|---|---:|---|
| 1 | LOAD_TEST_1 | healthy | 200 | Yes |
| 2 | LOAD_TEST_2 | abnormality | 200 | Yes |
| 3 | LOAD_TEST_3 | abnormality | 200 | Yes |
| 4 | LOAD_TEST_4 | healthy | 200 | Yes |
| 5 | LOAD_TEST_5 | abnormality | 200 | Yes |
| 6 | LOAD_TEST_6 | abnormality | 200 | Yes |

**Result:** PASS - 6 of 6 live requests returned HTTP 200. No Groq rate-limit error was observed across the check.

## 2. Moderate-risk wet chilli

**ML output**

```json
{
  "risk_pct": 66.16,
  "risk_level": "high",
  "risk_bands": {"low_max": 20, "moderate_max": 60},
  "index_type": "weather_based_proxy",
  "validated": false
}
```

**RAG output**

- HTTP status: `200`
- `ml_output`: `1`
- `response_mode`: `abnormality`
- Possible conditions: fungal leaf spot/mildew, bacterial wilt, and heat-related flower drop.
- Key recommendations: Inspect spots or wilting, improve airflow, mulch, provide rain shelter, and contact the local KVK.
- Retrieved documents: `02_weather_thresholds_by_disease`, chilli crop-stage, field-checklist, soil-moisture, heat, and disease documents.

**Verdict:** PASS

## 3. High-risk heavy-rain tomato

**ML output**

```json
{
  "risk_pct": 89.57,
  "risk_level": "high",
  "risk_bands": {"low_max": 20, "moderate_max": 60},
  "index_type": "weather_based_proxy",
  "validated": false
}
```

**RAG output**

- HTTP status: `200`
- `ml_output`: `1`
- `response_mode`: `abnormality`
- Possible conditions: late blight, root rot/Phytophthora, and water-logging stress.
- Key recommendations: Improve drainage, remove symptomatic leaves, use mulch, and maintain canopy airflow.
- Retrieved documents: `02_weather_thresholds_by_disease`, tomato crop-stage, field-checklist, soil-moisture, blight, and irrigation documents.

**Verdict:** PASS

## 4. Low-risk dry ragi

**ML output**

```json
{
  "risk_pct": 4.90,
  "risk_level": "low",
  "risk_bands": {"low_max": 20, "moderate_max": 60},
  "index_type": "weather_based_proxy",
  "validated": false
}
```

**RAG output**

- HTTP status: `200`
- `ml_output`: `0`
- `response_mode`: `healthy`
- Watch item: soil moisture of 18% is on the dry side.
- Key recommendations: Retain moisture with mulch, remove debris and weeds, water at the base, and inspect for visual symptoms.
- Retrieved documents: `22_healthy_state_betterments`, `24_field_hygiene`, `21_soil_moisture_effects_by_disease`, ragi field checklist, soil-moisture, irrigation, and crop-stage documents.

**Verdict:** PASS

## 5. Moderate mixed-rain chilli

**ML output**

```json
{
  "risk_pct": 54.47,
  "risk_level": "moderate",
  "risk_bands": {"low_max": 20, "moderate_max": 60},
  "index_type": "weather_based_proxy",
  "validated": false
}
```

**RAG output**

- HTTP status: `200`
- `ml_output`: `1`
- `response_mode`: `abnormality`
- Possible conditions: fungal leaf spot, bacterial wilt, and nutrient uptake stress.
- Key recommendations: Improve airflow, avoid overhead irrigation, remove symptomatic plants or leaves, and maintain soil moisture around 40-50%.
- Retrieved documents: `02_weather_thresholds_by_disease`, chilli crop-stage, field-checklist, soil-moisture, heat, nutrient, and disease documents.

**Verdict:** PASS

---

## 👥 Credits — Team ANVEXA

* **PRIYANSHU SARMA**
* **LIBERATOR NYADUNDU**
* **RYALI VENKATA SRI VIJAY KARTHIK**
* **Gajulapalli Venkata Raviteja**
* **Sneha Sarma**