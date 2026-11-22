"""Sarva Mitra Unified Backend API.

Combines Telemetry Service, ML Engine, and RAG Advisory Pipeline into a single,
clean API with high-level endpoints for the UI/Frontend as well as mounted individual
micro-endpoints.

Run:
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

import joblib
from fastapi import APIRouter, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Local module imports
from backend.telemetry_service.service import telemetry_service
from backend.ml_engine.backend import (
    PredictRequest,
    run_prediction,
    load_bundle,
    HistoryError,
    SCHEMA_VERSION as ML_SCHEMA_VERSION,
)
from backend.rag_pipeline.config import (
    CHAT_HISTORY_LIMIT,
    GROQ_MODEL,
    GROQ_API_KEYS,
    MONGODB_DATABASE,
    MONGODB_COLLECTION,
    MONGODB_VECTOR_INDEX,
    mongodb_uri,
    OLLAMA_API_KEY,
    OLLAMA_MODEL,
    LLM_PROVIDER,
)
from backend.rag_pipeline.rag import RAGPipeline
from backend.rag_pipeline.app import AdvisoryRequest, CurrentSensorData, WeatherData, ml_output as parse_ml_output

logger = logging.getLogger("sarva_mitra_unified")
logging.basicConfig(level=logging.INFO)
IST = timezone(timedelta(hours=5, minutes=30))

# ---------------------------------------------------------------------------
# Lifespan: Load ML bundle and warm up services on startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Sarva Mitra Unified Backend...")
    # Load ML Model
    try:
        app.state.ml_bundle = load_bundle()
        logger.info("ML risk model loaded successfully: %s", app.state.ml_bundle.get("selected_model"))
    except Exception as exc:
        logger.error("Failed to load ML risk model: %s", exc)
        app.state.ml_bundle = None

    # Warm up RAG pipeline instance
    try:
        app.state.rag_pipeline = RAGPipeline()
        logger.info("RAG Pipeline initialized successfully.")
    except Exception as exc:
        logger.warning("RAG Pipeline initialization warning: %s", exc)
        app.state.rag_pipeline = None

    yield
    logger.info("Shutting down Sarva Mitra Unified Backend.")


app = FastAPI(
    title="Sarva Mitra Unified API",
    description="Unified Agricultural AI Engine combining Telemetry, ML Risk Prediction, and RAG Advisory",
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend developers (React, Flutter, Vue, mobile apps, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Unified Request / Response Models for UI/UX Frontend
# ---------------------------------------------------------------------------

class ChatHistoryMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1)


class UnifiedChatRequest(BaseModel):
    """Simple high-level request from UI/UX frontend for agricultural advisory."""
    question: str = Field(..., description="Farmer question or concern", min_length=1)
    crop: str = Field(default="tomato", description="Crop name (e.g. tomato, chilli, ragi)")
    lat: float = Field(default=16.51, ge=-90, le=90, description="Farm latitude")
    lon: float = Field(default=80.52, ge=-180, le=180, description="Farm longitude")
    location: str = Field(default="Vijayawada", description="Location name or district")
    chat_history: list[ChatHistoryMessage] = Field(default_factory=list, description="Prior conversation messages")
    session_id: str | None = Field(default=None, description="Optional frontend session ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "Leaves are curling with small yellow spots, what should I inspect and spray?",
                "crop": "tomato",
                "lat": 16.51,
                "lon": 80.52,
                "location": "Vijayawada",
                "chat_history": []
            }
        }
    }


class UnifiedChatResponse(BaseModel):
    schema_version: str = "2.0"
    session_id: str
    crop: str
    location: dict[str, Any]
    answer: str
    structured: dict[str, Any] | None
    risk: dict[str, Any]
    telemetry: dict[str, Any]
    chat_history: list[dict[str, Any]]
    retrieval_context: dict[str, Any] | list[Any] | None = None


# ---------------------------------------------------------------------------
# High-Level Unified Endpoints (Designed for Frontend / UI)
# ---------------------------------------------------------------------------

@app.get("/", tags=["General"])
def root():
    return {
        "service": "Sarva Mitra Unified API",
        "version": "2.0.0",
        "docs_url": "/docs",
        "endpoints": {
            "frontend_dashboard": "GET /api/dashboard",
            "frontend_chat": "POST /api/chat",
            "system_health": "GET /api/health",
            "telemetry": "/api/telemetry/*",
            "ml_engine": "/api/ml/*",
            "rag_pipeline": "/api/rag/*",
        },
    }


@app.get("/api/health", tags=["General"])
def system_health(request: Request):
    """Comprehensive health check across all three core modules."""
    # 1. Telemetry Health
    telemetry_ok = True
    active_providers = []
    if telemetry_service.weatherapi_key:
        active_providers.append("WeatherAPI")
    if telemetry_service.tomorrow_key:
        active_providers.append("Tomorrow.io")
    if telemetry_service.agromonitoring_key:
        active_providers.append("AgroMonitoring")
    active_providers.append("Open-Meteo (Open)")
    active_providers.append("ISRIC-SoilGrids (Open)")

    # 2. ML Engine Health
    bundle = getattr(request.app.state, "ml_bundle", None)
    ml_status = {
        "loaded": bundle is not None,
        "model_name": bundle.get("selected_model") if bundle else None,
        "features_count": len(bundle.get("features", [])) if bundle else 0,
    }

    # 3. RAG Health
    mongo_ok = False
    try:
        mongo_ok = bool(mongodb_uri())
    except Exception:
        mongo_ok = False

    rag_status = {
        "mongodb_configured": mongo_ok,
        "llm_provider": LLM_PROVIDER,
        "ollama_configured": bool(OLLAMA_API_KEY),
        "ollama_model": OLLAMA_MODEL,
        "groq_configured": len(GROQ_API_KEYS) > 0,
        "groq_keys_count": len(GROQ_API_KEYS),
        "groq_model": GROQ_MODEL,
        "vector_index": MONGODB_VECTOR_INDEX,
    }

    return {
        "status": "ok" if (bundle and mongo_ok) else "degraded",
        "timestamp": datetime.now(IST).isoformat(),
        "telemetry": {
            "status": "ok",
            "active_providers": active_providers,
        },
        "ml_engine": ml_status,
        "rag_pipeline": rag_status,
    }


@app.get("/api/dashboard", tags=["Frontend / UI"])
def get_dashboard_data(
    lat: float = Query(default=16.51, ge=-90, le=90, description="Latitude"),
    lon: float = Query(default=80.52, ge=-180, le=180, description="Longitude"),
    location: str = Query(default="Vijayawada", description="Location name"),
    crop: str = Query(default="tomato", description="Current crop"),
    request: Request = None,
):
    """
    **Single unified call to populate the farmer dashboard:**
    - Live real-time telemetry (temp, humidity, soil moisture %, rainfall, sunlight)
    - 8-day historical trends for UI charts
    - ML risk calculation (risk %, risk level, risk label)
    - Quick agronomic summary
    """
    # 1. Fetch live telemetry & 8-day history
    curr = telemetry_service.get_current_readings(lat=lat, lon=lon)
    today = datetime.now(IST).date()
    history = telemetry_service.get_historical_records(lat=lat, lon=lon, target_date=today, days=8)

    # 2. Run ML Prediction
    bundle = getattr(request.app.state, "ml_bundle", None)
    if not bundle:
        bundle = load_bundle()

    ml_req = PredictRequest(
        device_id="virtual-node-01",
        location=location,
        lat=lat,
        lon=lon,
        target_date=today,
        history=history,
    )
    prediction = run_prediction(ml_req, bundle)
    risk_info = prediction.get("prediction", {})
    risk_pct = risk_info.get("risk_pct", 0.0)
    risk_level = risk_info.get("risk_level", "low")

    # 3. Formulate quick summary recommendation
    if risk_level == "high":
        quick_tip = f"High weather proxy risk ({risk_pct}%). Environmental conditions heavily favor fungal or foliar stress in {crop}. Inspect leaves immediately and avoid excess overhead irrigation."
    elif risk_level == "moderate":
        quick_tip = f"Moderate risk ({risk_pct}%). Monitor soil moisture closely. Maintain proper field drainage and check crop stage."
    else:
        quick_tip = f"Low risk ({risk_pct}%). Environmental and soil conditions are optimal. Continue standard fertilizer and irrigation practices."

    return {
        "status": "ok",
        "generated_at": datetime.now(IST).isoformat(),
        "location": {"name": location, "lat": lat, "lon": lon},
        "crop": crop,
        "current_telemetry": {
            "temperature_c": curr["temperature_c"],
            "humidity_pct": curr["humidity_pct"],
            "soil_moisture_pct": curr["soil_moisture_pct"],
            "rainfall_mm": curr["rainfall_mm"],
            "sunlight_wm2": curr["sunlight_wm2"],
            "leaf_wet_days": curr["leaf_wet_days"],
            "source": curr.get("source"),
        },
        "historical_trends": history,
        "ml_risk": {
            "risk_pct": risk_pct,
            "risk_level": risk_level,
            "risk_bands": risk_info.get("risk_bands"),
            "ml_output_code": 1 if risk_level in {"moderate", "high"} else 0,
        },
        "quick_advisory": quick_tip,
    }


@app.post("/api/chat", response_model=UnifiedChatResponse, tags=["Frontend / UI"])
def unified_chat(req: UnifiedChatRequest, request: Request):
    """
    **Single unified endpoint for Farmer Chat / Q&A:**
    1. Fetches live environmental telemetry for the farmer's coordinates.
    2. Runs the ML engine risk evaluation.
    3. Retrieves grounded agronomic advisory from vector search & Groq LLM.
    4. Returns complete text answer, structured actionable cards, and updated chat history.
    """
    today = datetime.now(IST).date()
    curr = telemetry_service.get_current_readings(lat=req.lat, lon=req.lon)
    history = telemetry_service.get_historical_records(lat=req.lat, lon=req.lon, target_date=today, days=8)

    # ML Prediction
    bundle = getattr(request.app.state, "ml_bundle", None)
    if not bundle:
        bundle = load_bundle()

    ml_req = PredictRequest(
        device_id="virtual-node-01",
        location=req.location,
        lat=req.lat,
        lon=req.lon,
        target_date=today,
        history=history,
    )
    prediction = run_prediction(ml_req, bundle)
    risk_info = prediction.get("prediction", {})
    risk_level = risk_info.get("risk_level", "low")
    ml_output_val = 1 if risk_level in {"moderate", "high"} else 0

    # RAG Advisory Generation
    rag: RAGPipeline = getattr(request.app.state, "rag_pipeline", None)
    if not rag:
        rag = RAGPipeline()

    chat_history_dicts = [{"role": msg.role, "content": msg.content} for msg in req.chat_history]

    readings = {
        "temperature_c": curr["temperature_c"],
        "humidity_pct": curr["humidity_pct"],
        "soil_moisture_pct": curr["soil_moisture_pct"],
        "rainfall_mm": curr["rainfall_mm"],
        "sunlight_wm2": curr["sunlight_wm2"],
        "risk_pct": risk_info.get("risk_pct"),
        "risk_level": risk_level,
    }

    try:
        answer, structured = rag.answer(
            readings=readings,
            ml_output=ml_output_val,
            crop=req.crop.strip().lower() or "unknown",
            location=req.location,
            question=req.question.strip(),
            chat_history=chat_history_dicts,
            ml_prediction=prediction,
        )
    except Exception as exc:
        logger.error("RAG pipeline answer generation failed: %s", exc)
        raise HTTPException(503, f"Advisory generation error: {exc}") from exc

    # Updated conversation history
    updated_history = list(chat_history_dicts)
    updated_history.append({"role": "user", "content": req.question.strip()})
    updated_history.append({"role": "assistant", "content": answer})
    updated_history = updated_history[-CHAT_HISTORY_LIMIT:]

    return UnifiedChatResponse(
        schema_version="2.0",
        session_id=req.session_id or str(uuid4()),
        crop=req.crop,
        location={"name": req.location, "lat": req.lat, "lon": req.lon},
        answer=answer,
        structured=structured,
        risk={
            "risk_pct": risk_info.get("risk_pct"),
            "risk_level": risk_level,
            "ml_output": ml_output_val,
        },
        telemetry=readings,
        chat_history=updated_history,
        retrieval_context=getattr(rag, "last_retrieval", None),
    )


# ---------------------------------------------------------------------------
# Individual Sub-Routers (Preserving Granular Micro-Endpoints)
# ---------------------------------------------------------------------------

# 1. Telemetry Router
telemetry_router = APIRouter(prefix="/api/telemetry", tags=["Individual - Telemetry"])

@telemetry_router.get("/current")
def telemetry_current(lat: float = 16.51, lon: float = 80.52):
    return telemetry_service.get_current_readings(lat=lat, lon=lon)

@telemetry_router.get("/history")
def telemetry_history(lat: float = 16.51, lon: float = 80.52, days: int = 8, target_date: date | None = None):
    return telemetry_service.get_historical_records(lat=lat, lon=lon, target_date=target_date, days=days)

@telemetry_router.get("/ml-payload")
def telemetry_ml_payload(lat: float = 16.51, lon: float = 80.52, location: str = "Vijayawada"):
    return telemetry_service.build_ml_payload(lat=lat, lon=lon, location=location)

@telemetry_router.get("/rag-payload")
def telemetry_rag_payload(lat: float = 16.51, lon: float = 80.52, location: str = "Vijayawada", crop: str = "tomato", question: str = "Health check"):
    return telemetry_service.build_rag_payload(crop=crop, question=question, lat=lat, lon=lon, location=location)

app.include_router(telemetry_router)


# 2. ML Engine Router
ml_router = APIRouter(prefix="/api/ml", tags=["Individual - ML Engine"])

@ml_router.get("/health")
def ml_health(request: Request):
    bundle = getattr(request.app.state, "ml_bundle", None) or load_bundle()
    return {
        "status": "ok",
        "model": {"name": bundle["selected_model"], "trained_through": bundle["trained_through"]},
    }

@ml_router.post("/predict")
def ml_predict(req: PredictRequest, request: Request):
    bundle = getattr(request.app.state, "ml_bundle", None) or load_bundle()
    try:
        return run_prediction(req, bundle)
    except HistoryError as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code, "message": exc.message})

app.include_router(ml_router)


# 3. RAG Pipeline Router
rag_router = APIRouter(prefix="/api/rag", tags=["Individual - RAG Pipeline"])

@rag_router.get("/health")
def rag_health():
    return {"status": "ok", "mode": "unified", "schema_version": "1.0"}

@rag_router.get("/diagnostics")
def rag_diagnostics():
    from backend.rag_pipeline.app import diagnostics as rag_diag
    return rag_diag()

@rag_router.post("/advisory")
def rag_advisory(req: AdvisoryRequest, request: Request):
    from backend.rag_pipeline.app import advisory as run_advisory
    return run_advisory(req)

app.include_router(rag_router)
