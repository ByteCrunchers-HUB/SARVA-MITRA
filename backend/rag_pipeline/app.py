from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Literal
from uuid import uuid4

import httpx
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

try:
    from .config import (
        CHAT_HISTORY_LIMIT,
        EMBEDDING_CACHE_DIR,
        EMBEDDING_DIMENSION,
        EMBEDDING_MODEL,
        ML_ENGINE_URL,
        RAG_USE_VECTOR_SEARCH,
    )
    from .config import MONGODB_DATABASE, MONGODB_COLLECTION
    from .config import GROQ_API_KEY, mongodb_uri
except ImportError:
    from config import (
        CHAT_HISTORY_LIMIT,
        EMBEDDING_CACHE_DIR,
        EMBEDDING_DIMENSION,
        EMBEDDING_MODEL,
        ML_ENGINE_URL,
        RAG_USE_VECTOR_SEARCH,
    )
    from config import MONGODB_DATABASE, MONGODB_COLLECTION
    from config import GROQ_API_KEY, mongodb_uri


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1)


class HistoryRecord(BaseModel):
    date: date
    soil_moisture_pct: float = Field(ge=0, le=100)
    sunlight_wm2: float | None = Field(default=None, ge=0)
    rainfall_mm: float = Field(ge=0)
    leaf_wet_days: int = Field(default=0, ge=0, le=1)


class AdvisoryRequest(BaseModel):
    device_id: str = "unknown-device"
    location: str = "Karnataka"
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    target_date: date | None = None
    history: list[HistoryRecord] = Field(default_factory=list)
    crop: str = "unknown"
    question: str = ""
    ml_output: int | None = Field(default=None, ge=0, le=1)
    ml_prediction: dict | None = None
    readings: dict = Field(default_factory=dict)
    chat_history: list[ChatMessage] = Field(default_factory=list)
    session_id: str | None = None
    collection_name: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "device_id": "sample-device",
                    "location": "Vijayawada",
                    "lat": 16.51,
                    "lon": 80.52,
                    "target_date": "2000-01-09",
                    "crop": "tomato",
                    "question": "What should I inspect after heavy rain?",
                    "history": [
                        {"date": "2000-01-01", "soil_moisture_pct": 50, "sunlight_wm2": 257.64, "rainfall_mm": 0.71, "leaf_wet_days": 1},
                        {"date": "2000-01-02", "soil_moisture_pct": 49, "sunlight_wm2": 222.80, "rainfall_mm": 0.74, "leaf_wet_days": 1},
                        {"date": "2000-01-03", "soil_moisture_pct": 56, "sunlight_wm2": 204.51, "rainfall_mm": 10.56, "leaf_wet_days": 1},
                        {"date": "2000-01-04", "soil_moisture_pct": 56, "sunlight_wm2": 127.55, "rainfall_mm": 4.44, "leaf_wet_days": 1},
                        {"date": "2000-01-05", "soil_moisture_pct": 51, "sunlight_wm2": 220.25, "rainfall_mm": 1.07, "leaf_wet_days": 1},
                        {"date": "2000-01-06", "soil_moisture_pct": 50, "sunlight_wm2": 242.01, "rainfall_mm": 0.11, "leaf_wet_days": 1},
                        {"date": "2000-01-07", "soil_moisture_pct": 59, "sunlight_wm2": 99.19, "rainfall_mm": 8.90, "leaf_wet_days": 1},
                        {"date": "2000-01-08", "soil_moisture_pct": 57, "sunlight_wm2": 119.10, "rainfall_mm": 35.31, "leaf_wet_days": 1},
                    ],
                    "readings": {
                        "temperature_c": 25.86,
                        "humidity_pct": 79.15
                    },
                    "chat_history": []
                }
            ]
        }
    }

    @field_validator("chat_history")
    @classmethod
    def limit_history(cls, value: list[ChatMessage]) -> list[ChatMessage]:
        return value[-CHAT_HISTORY_LIMIT:]


app = FastAPI(title="Sarva Mitra RAG Advisory API", version="1.0")
origins = [value.strip() for value in os.getenv("CORS_ORIGINS", "*").split(",") if value.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if origins == ["*"] else origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "chat_mode": "stateless",
        "ml_engine_url": ML_ENGINE_URL,
        "embedding": {
            "model": EMBEDDING_MODEL,
            "dimension": EMBEDDING_DIMENSION,
            "cache": EMBEDDING_CACHE_DIR,
        },
    }


@app.get("/ready", include_in_schema=False)
def ready():
    return {"status": "ready", "mode": "stateless"}


@app.get("/diagnostics")
def diagnostics():
    mongo_configured = False
    try:
        mongo_configured = bool(mongodb_uri())
    except RuntimeError:
        mongo_configured = False
    ml_status = "unknown"
    try:
        response = httpx.get(f"{ML_ENGINE_URL}/health", timeout=8)
        ml_status = f"reachable:{response.status_code}"
    except httpx.RequestError as exc:
        ml_status = f"unreachable:{type(exc).__name__}"
    return {
        "vector_search": RAG_USE_VECTOR_SEARCH,
        "mongodb_configured": mongo_configured,
        "groq_configured": bool(GROQ_API_KEY),
        "ml_engine_url": ML_ENGINE_URL,
        "ml_status": ml_status,
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dimension": EMBEDDING_DIMENSION,
        "mongodb_database": MONGODB_DATABASE,
        "mongodb_collection": MONGODB_COLLECTION,
    }


def ml_output(prediction: dict | None, explicit: int | None) -> int:
    if explicit in (0, 1):
        return explicit
    if not prediction:
        raise HTTPException(400, "ml_prediction is required")
    if prediction.get("ml_output") in (0, 1):
        return prediction["ml_output"]
    nested = prediction.get("prediction", {})
    level = str(nested.get("risk_level", "")).lower()
    if level in {"moderate", "high"}:
        return 1
    if level == "low":
        return 0
    pct = nested.get("risk_pct")
    if isinstance(pct, (int, float)):
        return 1 if pct >= 20 else 0
    raise HTTPException(422, "ML prediction has no supported risk value")


def call_ml_engine(request: AdvisoryRequest) -> dict:
    if not request.history:
        raise HTTPException(422, "Provide ml_prediction or history")
    if request.lat is None or request.lon is None:
        raise HTTPException(422, "lat and lon are required")
    target = request.target_date
    if target is None:
        target = max(row.date for row in request.history) + timedelta(days=1)
    payload = {
        "device_id": request.device_id,
        "location": request.location,
        "lat": request.lat,
        "lon": request.lon,
        "target_date": target.isoformat(),
        "history": [
            row.model_dump(mode="json")
            for row in sorted(request.history, key=lambda row: row.date)
        ],
    }
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            response = httpx.post(f"{ML_ENGINE_URL}/predict", json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as exc:
            last_error = exc
        except httpx.RequestError as exc:
            last_error = exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                502,
                {
                    "message": "ML engine returned an error",
                    "status_code": exc.response.status_code,
                    "detail": exc.response.text,
                },
            ) from exc
        if attempt == 0:
            time.sleep(2)
    raise HTTPException(504, f"ML engine timed out after retry: {last_error}")


@app.post("/v1/advisory")
def advisory(request: AdvisoryRequest):
    prediction = request.ml_prediction or call_ml_engine(request)
    output = ml_output(prediction, request.ml_output)
    readings = dict(request.readings)
    if request.history:
        latest = max(request.history, key=lambda row: row.date)
        readings.update({
            "soil_moisture_pct": latest.soil_moisture_pct,
            "sunlight_wm2": latest.sunlight_wm2,
            "rainfall_mm": latest.rainfall_mm,
            "leaf_wet_days": latest.leaf_wet_days,
        })
    nested = prediction.get("prediction", {})
    if isinstance(nested, dict):
        readings.update({
            "risk_pct": nested.get("risk_pct"),
            "risk_level": nested.get("risk_level"),
        })

    chat_history = [{"role": item.role, "content": item.content} for item in request.chat_history]
    try:
        try:
            from .rag import RAGPipeline
        except ImportError:
            from rag import RAGPipeline
        pipeline = RAGPipeline(request.collection_name)
        answer, structured = pipeline.answer(
            readings=readings,
            ml_output=output,
            crop=request.crop.strip() or "unknown",
            location=request.location.strip() or "unknown",
            question=request.question.strip(),
            chat_history=chat_history,
            ml_prediction=prediction,
        )
    except (RuntimeError, TimeoutError) as exc:
        raise HTTPException(503, f"RAG advisory service unavailable: {exc}") from exc

    updated = chat_history.copy()
    if request.question.strip():
        updated.append({"role": "user", "content": request.question.strip()})
    updated.append({"role": "assistant", "content": answer})
    updated = updated[-CHAT_HISTORY_LIMIT:]
    return {
        "schema_version": "1.0",
        "session_id": request.session_id or str(uuid4()),
        "ml_output": output,
        "ml_prediction": prediction,
        "answer": answer,
        "structured": structured,
        "retrieval_context": pipeline.last_retrieval,
        "chat_history": updated,
    }


@app.post("/advisory", deprecated=True)
def advisory_alias(request: AdvisoryRequest):
    return advisory(request)


@app.post("/predict-and-advice", deprecated=True)
def predict_and_advice(request: AdvisoryRequest):
    if request.ml_prediction is not None:
        return advisory(request)
    prediction = call_ml_engine(request)
    combined = request.model_copy(update={"ml_prediction": prediction})
    return advisory(combined)
