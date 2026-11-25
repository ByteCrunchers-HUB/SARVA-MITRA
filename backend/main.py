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
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

import joblib
from fastapi import APIRouter, FastAPI, HTTPException, Query, Request, UploadFile, File
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
from backend.rag_pipeline.rag import RAGPipeline, clean_advisory_text
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

# Enable CORS for frontend developers and local environments (including file:// null origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=".*",
    allow_credentials=False,
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
    stage: str | None = Field(default=None, description="Optional crop growth stage")
    chat_history: list[ChatHistoryMessage] = Field(default_factory=list, description="Prior conversation messages")
    session_id: str | None = Field(default=None, description="Optional frontend session ID")
    mode: str = Field(default="chat", description="'report' for initial telemetry assessment or 'chat' for conversational Q&A")

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

    chat_history_dicts = [
        {"role": msg.role, "content": msg.content}
        for msg in req.chat_history
        if msg.content.strip() != req.question.strip()
    ]

    readings = {
        "temperature_c": curr["temperature_c"],
        "humidity_pct": curr["humidity_pct"],
        "soil_moisture_pct": curr["soil_moisture_pct"],
        "rainfall_mm": curr["rainfall_mm"],
        "sunlight_wm2": curr["sunlight_wm2"],
        "risk_pct": risk_info.get("risk_pct"),
        "risk_level": risk_level,
    }

    # RAG Advisory Generation (safely handled to avoid 500 when keys are missing or rate-limited)
    answer = None
    structured = None
    retrieval_context = None

    try:
        rag: RAGPipeline | None = getattr(request.app.state, "rag_pipeline", None)
        if not rag and (GROQ_API_KEYS or os.getenv("OLLAMA_API_KEY")):
            try:
                rag = RAGPipeline()
                request.app.state.rag_pipeline = rag
            except Exception as init_exc:
                logger.warning("Could not initialize RAGPipeline on-demand: %s", init_exc)
                rag = None

        if rag:
            mode_val = req.mode if req.mode in ("report", "chat") else (
                "report" if len(chat_history_dicts) == 0 and "complete agronomic status assessment" in req.question.lower() else "chat"
            )
            answer, structured = rag.answer(
                readings=readings,
                ml_output=ml_output_val,
                crop=req.crop.strip().lower() or "unknown",
                location=req.location,
                question=req.question.strip(),
                chat_history=chat_history_dicts,
                ml_prediction=prediction,
                mode=mode_val,
            )
            answer = clean_advisory_text(answer)
            retrieval_context = getattr(rag, "last_retrieval", None)
    except Exception as exc:
        logger.error("RAG pipeline execution encountered an error: %s", exc)

    # Graceful fallback: synthesize grounded agronomic advisory from live sensors & ML prediction
    if not answer:
        crop_title = req.crop.strip().title() or "Crop"
        loc_title = req.location or "your field"
        temp_val = curr.get("temperature_c", 28.0)
        hum_val = curr.get("humidity_pct", 65.0)
        sm_val = curr.get("soil_moisture_pct", 22.0)
        rain_val = curr.get("rainfall_mm", 0.0)
        risk_pct_val = risk_info.get("risk_pct", 35.0)
        q_lower = req.question.lower()

        # 1. Topic: Fertilizer / Calcium / Nutrition / Flower drop
        if any(w in q_lower for w in ("fertiliz", "calcium", "nutrient", "npk", "spray", "flower drop")):
            answer = (
                f"**Nutrient & Spray Guidance for {crop_title} ({loc_title})**:\n\n"
                f"• **Flowering Stage Nutrition**: High nitrogen promotes excessive vegetative foliage at the expense of reproductive bloom. At flowering, shift toward balanced potassium (K), calcium (Ca), and boron (B) to stabilize flower retention.\n"
                f"• **Foliar Calcium & Boron Application**: Apply foliar **Calcium Nitrate @ 0.5% (5g/L)** combined with **Boron (Solubor @ 1g/L)** during cool morning hours. Repeat after 10–12 days during active fruit set.\n"
                f"• **Basal / Drip Schedule**: Maintain root-zone moisture above 18% so root hairs can absorb soluble calcium. Avoid applying urea right before peak heat.\n"
                f"• **Live Sensors**: Temperature: {temp_val:.1f}°C | Humidity: {hum_val:.0f}% | Soil Moisture: {sm_val:.1f}%\n"
                f"• **Safety Note**: Spray early morning (07:00–09:00) before temperatures exceed 30°C to protect delicate flower petals.\n\n"
                f"### 💡 Suggested Follow‑Up Questions\n"
                f"- What are the visual deficiency symptoms of calcium vs boron on leaves?\n"
                f"- What organic preventive spray helps against flower drop?"
            )
            structured = {
                "response_mode": "chat",
                "overview": f"Nutrient and spray recommendations for {crop_title}.",
                "model_interpretation": "Flowering stage demands balanced calcium and potassium management.",
                "recommendations": [
                    {"step": 1, "action": "Foliar spray Calcium Nitrate 0.5% + Boron 1g/L in morning hours."},
                    {"step": 2, "action": "Maintain soil moisture above 18% to support calcium uptake through roots."}
                ]
            }

        # 2. Topic: Irrigation / Soil Moisture Bands / Watering
        elif any(w in q_lower for w in ("irrigat", "water", "moist", "band")):
            is_dry = sm_val < 18.0
            is_wet = sm_val > 35.0
            status_text = "below optimal threshold (water stress)" if is_dry else ("elevated moisture (hypoxia risk)" if is_wet else "in the ideal vegetative-flowering moisture window")
            irr_action = (
                f"Schedule light, frequent pulse irrigation (2–3 L/m² daily) via drip lines in the morning (06:00–08:30) to bring root zone to 24%."
                if is_dry else
                ("Pause watering and inspect furrow drainage to prevent collar rot." if is_wet else "Maintain standard 2-day irrigation cycles.")
            )

            answer = (
                f"**Irrigation & Soil Moisture Management for {crop_title} ({loc_title})**:\n\n"
                f"• **Target Soil Moisture Band**: For {crop_title} during flowering, the recommended root-zone soil moisture is **22% – 32% VWC** (60–80% available water capacity).\n"
                f"• **Current Soil Moisture**: Sensor reports **{sm_val:.1f}%**, which is {status_text}.\n"
                f"• **Irrigation Action**: {irr_action}\n"
                f"• **Evapotranspiration Correlates**: Ambient temperature ({temp_val:.1f}°C) and relative humidity ({hum_val:.0f}%) drive steady surface drying.\n\n"
                f"### 💡 Suggested Follow‑Up Questions\n"
                f"- Should I irrigate early in the morning or evening?\n"
                f"- What are the signs of over-watering vs drought stress in {crop_title}?"
            )
            structured = {
                "response_mode": "chat",
                "overview": f"Soil moisture and irrigation guidance for {crop_title}.",
                "model_interpretation": f"Current soil moisture is {sm_val:.1f}%.",
                "recommendations": [
                    {"step": 1, "action": f"Target 22–30% soil moisture band for {crop_title} flowering stage."},
                    {"step": 2, "action": irr_action}
                ]
            }

        # 3. Topic: Diseases / Pests / Blight / Yellowing / Leaf curl / Insects
        elif any(w in q_lower for w in ("disease", "pest", "blight", "spot", "curl", "yellow", "wilt", "rot", "whitefly", "thrip", "insect")):
            answer = (
                f"**Pest & Disease Management for {crop_title} ({loc_title})**:\n\n"
                f"• **AI Pathogen Risk Index**: **{risk_pct_val:.1f}% ({risk_level.upper()})** based on temperature {temp_val:.1f}°C and humidity {hum_val:.0f}%.\n"
                f"• **Primary Risks to Inspect Today**:\n"
                f"  - **Sucking Pests (Thrips / Whiteflies)**: Inspect leaf undersides; thrips cause upward leaf curling and silvery sheen, while whiteflies transmit Leaf Curl Virus.\n"
                f"  - **Foliar Blight & Leaf Spots**: Check lower canopy leaves for concentric brown rings or water-soaked lesions.\n"
                f"• **Preventive Protection Steps**:\n"
                f"  1. Install yellow and blue sticky traps (5–8 per acre) to monitor insect activity.\n"
                f"  2. Apply preventive Neem Oil spray (3–5 ml/L with soap emulsifier) during cool evening hours.\n"
                f"  3. If fungal spots are spotted, consult local KVK for certified copper hydroxide (2g/L) or biological Trichoderma application.\n\n"
                f"### 💡 Suggested Follow‑Up Questions\n"
                f"- What organic spray is effective against thrips and aphids?\n"
                f"- How do I distinguish viral leaf curl from moisture stress?"
            )
            structured = {
                "response_mode": "chat",
                "overview": f"Pest and disease diagnosis for {crop_title}.",
                "model_interpretation": f"Pathogen risk index is {risk_pct_val:.1f}% ({risk_level}).",
                "recommendations": [
                    {"step": 1, "action": "Inspect lower canopy and leaf undersides for thrips or lesions."},
                    {"step": 2, "action": "Apply preventive neem formulation (3ml/L) and install sticky traps."}
                ]
            }

        # 4. Default / General Agronomic Overview or Comprehensive Assessment
        else:
            if mode_val == "report":
                stage_val = getattr(req, "stage", None) or "Flowering Stage"
                answer = generate_comprehensive_advisory(
                    crop=req.crop,
                    stage=stage_val,
                    location=req.location,
                    telemetry=readings,
                    prediction=prediction,
                )
                structured = {
                    "response_mode": "report",
                    "overview": f"Comprehensive agronomic telemetry assessment for {crop_title}.",
                    "model_interpretation": f"ML risk index: {risk_pct_val:.1f}% ({risk_level}).",
                    "recommendations": [
                        {"step": 1, "action": "Follow targeted field scouting checklist for fungal and foliar pathogens."},
                        {"step": 2, "action": "Adjust irrigation to maintain optimal root zone moisture band."}
                    ]
                }
            else:
                if sm_val < 18.0:
                    irrigation_note = f"Root-zone soil moisture is low ({sm_val:.1f}%). Initiate scheduled drip irrigation (2–3 L/m²) early morning to protect against blossom drop and moisture stress."
                elif sm_val > 35.0:
                    irrigation_note = f"Soil moisture is elevated ({sm_val:.1f}%). Pause irrigation and ensure surface furrows drain rapidly to prevent root rot."
                else:
                    irrigation_note = f"Soil moisture ({sm_val:.1f}%) is within optimal crop tolerance. Maintain regular morning hydration intervals."

                if risk_level == "high":
                    protection_note = f"Under ambient {temp_val:.1f}°C and {hum_val:.0f}% RH, pathogen stress index is elevated ({risk_pct_val:.1f}%). Prune senescent lower leaves, inspect undersides for fungal spots, and apply certified biocontrol spray (Trichoderma or copper hydroxide)."
                elif risk_level == "moderate":
                    protection_note = f"Ambient conditions ({temp_val:.1f}°C, {hum_val:.0f}% RH) represent moderate disease favorability ({risk_pct_val:.1f}%). Inspect lower canopy twice weekly and spray preventive neem formulation (3ml/L) if humidity exceeds 70%."
                else:
                    protection_note = f"Environmental pathogen favorability is low ({risk_pct_val:.1f}%). Focus on balanced NPK fertilizer application and standard field sanitation."

                answer = (
                    f"**Agronomic Assessment for {crop_title} ({loc_title})**:\n\n"
                    f"• **Live Sensors**: Temperature: {temp_val:.1f}°C | Humidity: {hum_val:.0f}% | Soil Moisture: {sm_val:.1f}% | Rain: {rain_val:.1f}mm\n"
                    f"• **AI Pathogen Risk Index**: {risk_pct_val:.1f}% ({risk_level.upper()})\n\n"
                    f"**Action Steps**:\n"
                    f"1. **Irrigation**: {irrigation_note}\n"
                    f"2. **Canopy & Protection**: {protection_note}\n"
                    f"3. **Field Confirmation**: Inspect flowers and leaf nodes during morning hours before spraying.\n\n"
                    f"### 💡 Suggested Follow‑Up Questions\n"
                    f"- What fertilizer or calcium spray should I apply during flowering?\n"
                    f"- What are the recommended fertilizer practices and soil moisture bands for my crop?"
                )
                structured = {
                    "response_mode": "chat",
                    "overview": f"Agronomic telemetry status for {crop_title}.",
                    "model_interpretation": f"ML risk index: {risk_pct_val:.1f}% ({risk_level}).",
                    "recommendations": [
                        {"step": 1, "action": irrigation_note},
                        {"step": 2, "action": protection_note}
                    ]
                }

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


@app.post("/api/transcribe", tags=["Voice / Audio"])
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    """Transcribes farmer spoken audio payload using Groq Whisper Turbo."""
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty audio recording payload")

    import io
    from groq import Groq

    for key in reversed(GROQ_API_KEYS):
        try:
            client = Groq(api_key=key)
            audio_io = io.BytesIO(contents)
            audio_io.name = file.filename or "recording.webm"
            res = client.audio.transcriptions.create(
                file=audio_io,
                model="whisper-large-v3-turbo",
                response_format="text",
            )
            text = str(res).strip()
            if text:
                return {"text": text, "status": "ok"}
        except Exception as exc:
            logger.warning("Groq Whisper transcription attempt failed: %s", exc)
            continue

    raise HTTPException(status_code=502, detail="Speech transcription service temporarily unavailable")


# ---------------------------------------------------------------------------
# PDF Report Generation Endpoint
# ---------------------------------------------------------------------------
def generate_comprehensive_advisory(
    crop: str,
    stage: str,
    location: str,
    telemetry: dict,
    prediction: dict,
) -> str:
    """Generates an exhaustive, multi-section agronomic assessment grounded in live telemetry and ML pathogen risk."""
    crop_title = crop.strip().title() or "Crop"
    loc_title = location or "Monitored Field"
    stage_title = stage or "Active Growth"

    temp = telemetry.get("temperature_c", 28.0)
    hum = telemetry.get("humidity_pct", 65.0)
    sm = telemetry.get("soil_moisture_pct", 22.0)
    rain = telemetry.get("rainfall_mm", 0.0)
    sun = telemetry.get("sunlight_wm2", 500.0)

    risk_info = prediction.get("prediction", {}) if isinstance(prediction, dict) else {}
    risk_pct = risk_info.get("risk_pct", 29.8)
    risk_level = str(risk_info.get("risk_level", "moderate")).lower()

    # Crop-specific pathogen vulnerabilities
    crop_key = crop.strip().lower()
    if "chilli" in crop_key:
        diseases = [
            ("Anthracnose / Fruit Rot (Colletotrichum capsici)", "Dark sunken circular lesions on maturing pods with concentric rings of acervuli. High humidity (>75%) with warm nights accelerate fruit rot."),
            ("Powdery Mildew (Leveillula taurica)", "White powdery patches on leaf undersides with corresponding yellow chlorotic blotches on upper leaf surfaces; causes premature defoliation under dry soil and high atmospheric humidity."),
            ("Bacterial Leaf Spot & Wilt (Xanthomonas / Ralstonia)", "Water-soaked dark angular spots on leaves and sudden midday wilting with vascular browning under elevated root-zone moisture."),
            ("Thrips & Mite Vector Pressure", "Silvery feeding scars, upward boat-shaped leaf curling, and stunted shoot terminals transmitting Chilli Leaf Curl / Peanut Bud Necrosis virus.")
        ]
        soil_min, soil_max = 18.0, 26.0
        special_nutrients = "Foliar Calcium Nitrate @ 0.5% (5g/L) combined with Boron (Solubor @ 1g/L) during active fruit set to prevent blossom-end rot and fruit shedding."
    elif "ragi" in crop_key or "millet" in crop_key:
        diseases = [
            ("Finger / Neck Blast (Magnaporthe grisea)", "Spindle-shaped elliptical lesions with gray centers and brown margins on leaves; blackening of neck node causing lodging and chaffy earheads."),
            ("Foot Rot / Seedling Blight (Sclerotium rolfsii)", "Basal collar rotting with white mycelial cottony growth and brown mustard-seed-like sclerotia under stagnant moisture."),
            ("Banded Leaf & Sheath Blight (Rhizoctonia solani)", "Irregular bleached patches with dark purple borders on leaf sheaths progressing upward into the canopy.")
        ]
        soil_min, soil_max = 16.0, 24.0
        special_nutrients = "Balanced top dressing of Potassium (MOP) to strengthen culm strength and prevent neck lodging; avoid excess urea in overcast weather."
    else:  # Default to Tomato
        diseases = [
            ("Early Blight (Alternaria solani)", "Target-like concentric brown rings on older lower leaves progressing upward; stems show dark sunken collar cankers. Favored by warm temperatures (24–29°C) and alternating wet/dry periods."),
            ("Late Blight (Phytophthora infestans)", "Rapidly enlarging water-soaked pale-green lesions that turn purplish-black with white downy mold on leaf margins under cool, saturated humidity (>80%)."),
            ("Septoria Leaf Spot (Septoria lycopersici)", "Numerous small circular spots (1–3 mm) with dark brown margins and sunken gray centers sprinkled with tiny black pycnidia; causes severe lower defoliation."),
            ("Blossom-End Rot & Calcium Disorder", "Water-soaked dark leathering at the blossom end of green fruits caused by irregular soil moisture hindering root calcium transport.")
        ]
        soil_min, soil_max = 20.0, 28.0
        special_nutrients = "Foliar spray of water-soluble Calcium Nitrate (5g/L) + Boron 20% (1g/L) applied at 10-day intervals during flowering and pea-sized fruit stage."

    # Soil moisture status & irrigation guidance
    if sm < soil_min:
        sm_status = f"Deficit ({sm:.1f}% vs optimal {soil_min:.0f}–{soil_max:.0f}%)"
        irr_action = f"Initiate light, frequent drip hydration (2–3 hours in early morning, 06:00–08:30). Root moisture is below the {soil_min:.0f}% threshold, threatening flower drop and poor fruit expansion. Avoid heavy flood irrigation which causes fruit cracking."
    elif sm > soil_max:
        sm_status = f"Excess / Saturated ({sm:.1f}% vs optimal {soil_min:.0f}–{soil_max:.0f}%)"
        irr_action = f"Immediately withhold irrigation and clear furrow tail-drains. High soil moisture ({sm:.1f}%) combined with warm ambient temperature induces root hypoxia and greatly heightens collar rot and bacterial wilt susceptibility."
    else:
        sm_status = f"Optimal ({sm:.1f}% within {soil_min:.0f}–{soil_max:.0f}% band)"
        irr_action = f"Maintain the current 2-day pulse irrigation interval. Root-zone volumetric water content ({sm:.1f}%) is in the prime metabolic window for nutrient uptake and transpiration."

    # Environmental risk interpretation
    if risk_level == "high":
        risk_interp = f"The XGBoost field risk model evaluates an elevated pathogen favorability index of **{risk_pct:.1f}% (HIGH RISK)**. Atmospheric relative humidity ({hum:.0f}%) and canopy temperatures ({temp:.1f}°C) create a sustained microclimate window conducive to fungal spore germination and secondary foliar infection."
        urgency = "IMMEDIATE FIELD INSPECTION & PREVENTIVE SANITATION REQUIRED WITHIN 24 HOURS."
    elif risk_level == "moderate":
        risk_interp = f"The XGBoost field risk model computes an active pathogen favorability index of **{risk_pct:.1f}% (MODERATE RISK)**. While acute infection pressure is currently constrained, relative humidity ({hum:.0f}%) and ambient temperature ({temp:.1f}°C) support early fungal incubation, especially in dense or shaded canopy pockets."
        urgency = "ACTIVE SCOUTING & PREVENTIVE CANOPY MANAGEMENT ADVISED OVER THE NEXT 48 HOURS."
    else:
        risk_interp = f"The field risk evaluation indicates **{risk_pct:.1f}% (LOW RISK)**. Ambient microclimate factors (temperature {temp:.1f}°C, RH {hum:.0f}%) are currently hostile to widespread fungal sporulation."
        urgency = "ROUTINE SCOUTING & BALANCED AGRONOMIC MAINTENANCE."

    # Disease checklist markdown table
    disease_rows = "\n".join(
        f"| **{name}** | {desc} | High |" for name, desc in diseases
    )
    disease_table = (
        "| Crop Disease / Suspect Pathogen | Diagnostic Symptoms in Field | Priority Level |\n"
        "|---|---|---|\n"
        f"{disease_rows}"
    )

    # Interventions markdown table
    interventions_table = (
        "| Management Area | Recommended Field Action | Operational Timing |\n"
        "|---|---|---|\n"
        f"| **Irrigation & Hydration** | {irr_action} | Early morning (06:00–08:30) |\n"
        "| **Canopy Hygiene** | Prune senescent lower leaves up to 20 cm from ground; maintain clean weed-free row margins. | Dry sunny midday |\n"
        "| **Biological Protection** | Spray Neem Oil emulsion (5 ml/L + surfactant) or Trichoderma viride / Pseudomonas fluorescens (5g/L). | Calm evening hours |\n"
        f"| **Targeted Nutrition** | {special_nutrients} | Active growth stage |\n"
    )

    advisory = f"""### 1. Executive Microclimate & Pathogen Risk Assessment
- **Field Microclimate**: Ambient Air Temperature is **{temp:.1f}°C**, Relative Humidity is **{hum:.0f}%**, Volumetric Soil Moisture is **{sm:.1f}%** ({sm_status}), Daily Rainfall is **{rain:.1f} mm**, and Solar Irradiance is **{sun:.0f} W/m²**.
- **ML Pathogen Risk Status**: **{risk_pct:.2f}% ({risk_level.upper()})** | Signal Code: **{'1 (Active)' if risk_level in {'moderate', 'high'} else '0 (Nominal)'}**.
- **Model Diagnostic Note**: {risk_interp}
- **Action Urgency**: {urgency}

### 2. High-Priority Field Scouting & Disease Checklist
Walk the crop rows in an inverted 'W' pattern during morning hours (07:30–10:00). Closely check the following priority issues for **{crop_title} ({stage_title})**:

{disease_table}

### 3. Practical Agronomic Field Interventions
{interventions_table}

### 4. Critical Boundaries & Official Agricultural Notice
- **Telemetry Boundaries**: Sarva Mitra weather and soil telemetry detects microclimate favorability and disease vulnerability windows. It does not replace laboratory culture or physical plant pathology examination.
- **KVK Extension Mandate**: Dosing, chemical brand names, and systemic fungicides/insecticides are strictly regulated. Farmers should carry any suspect leaf or pod samples to the nearest **Krishi Vigyan Kendra (KVK)** or consult their local Agricultural Extension Officer prior to chemical tank-mixing.
"""
    return advisory.strip()


class PDFReportRequest(BaseModel):
    crop: str = Field(default="tomato", description="Target crop")
    location: str = Field(default="Vijayawada", description="Farm location name")
    lat: float = Field(default=16.51, description="Farm latitude")
    lon: float = Field(default=80.52, description="Farm longitude")
    stage: str = Field(default="Flowering & Fruit Set (50-80 days)", description="Growth stage")
    advisory_text: str | None = Field(default=None, description="Advisory text content")


@app.post("/api/report/pdf", tags=["Reports / PDF"])
def generate_pdf_report_endpoint(req: PDFReportRequest):
    """Generates an official PDF agronomic advisory report without logo as requested."""
    from fastapi.responses import Response
    from frontend.pdf_generator import generate_advisory_pdf

    telemetry = telemetry_service.get_current_readings(lat=req.lat, lon=req.lon)
    today = datetime.now(IST).date()
    history = telemetry_service.get_historical_records(lat=req.lat, lon=req.lon, target_date=today, days=8)

    bundle = getattr(app.state, "ml_bundle", None) or load_bundle()
    ml_req = PredictRequest(
        device_id="virtual-node-01",
        location=req.location,
        lat=req.lat,
        lon=req.lon,
        target_date=today,
        history=history,
    )
    prediction = run_prediction(ml_req, bundle)

    farm_cfg = {
        "name": req.location,
        "lat": req.lat,
        "lon": req.lon,
        "crop": req.crop,
        "stage": req.stage,
    }

    # Resolve official Sarva Mitra logo (SVG vector or transparent PNG preferred for native ReportLab rendering)
    project_root = Path(__file__).resolve().parent.parent
    logo_report_svg = project_root / "frontend" / "assets" / "logo-report.svg"
    emblem_png = project_root / "frontend" / "assets" / "logo-emblem.png"
    icon_png = project_root / "frontend" / "assets" / "icon.png"
    logo_path = logo_report_svg if logo_report_svg.exists() else (emblem_png if emblem_png.exists() else (icon_png if icon_png.exists() else None))

    # Clean advisory text or generate complete comprehensive diagnostic report if missing/short
    clean_adv = clean_advisory_text(req.advisory_text or "")
    is_short = (
        not clean_adv
        or len(clean_adv) < 200
        or (
            len(clean_adv) < 400
            and any(
                clean_adv.startswith(p)
                for p in (
                    "Moderate risk",
                    "Low risk",
                    "High weather proxy risk",
                    "Risk Level:",
                )
            )
        )
    )

    if is_short:
        clean_adv = ""  # Reset short text so fallback is guaranteed if RAG is unavailable or fails
        rag: RAGPipeline | None = getattr(app.state, "rag_pipeline", None)
        if not rag and (GROQ_API_KEYS or os.getenv("OLLAMA_API_KEY")):
            try:
                rag = RAGPipeline()
                app.state.rag_pipeline = rag
            except Exception:
                rag = None

        if rag:
            try:
                risk_info = prediction.get("prediction", {})
                risk_level = risk_info.get("risk_level", "low")
                ml_out = 1 if risk_level in {"moderate", "high"} else 0
                rag_readings = {
                    "temperature_c": telemetry.get("temperature_c", 0.0),
                    "humidity_pct": telemetry.get("humidity_pct", 0.0),
                    "soil_moisture_pct": telemetry.get("soil_moisture_pct", 0.0),
                    "rainfall_mm": telemetry.get("rainfall_mm", 0.0),
                    "sunlight_wm2": telemetry.get("sunlight_wm2", 0.0),
                    "risk_pct": risk_info.get("risk_pct"),
                    "risk_level": risk_level,
                }
                generated_ans, _ = rag.answer(
                    readings=rag_readings,
                    ml_output=ml_out,
                    crop=req.crop.strip().lower() or "unknown",
                    location=req.location,
                    question=f"Provide a complete, comprehensive agronomic status assessment and recommendations for {req.crop} ({req.stage}) based on current field conditions.",
                    chat_history=[],
                    ml_prediction=prediction,
                    mode="report",
                )
                if generated_ans:
                    candidate = clean_advisory_text(generated_ans)
                    if len(candidate) >= 400:
                        clean_adv = candidate
            except Exception as rag_err:
                logger.warning("RAG report generation in PDF endpoint fell back: %s", rag_err)

        if not clean_adv or len(clean_adv) < 400:
            clean_adv = generate_comprehensive_advisory(
                crop=req.crop,
                stage=req.stage,
                location=req.location,
                telemetry=telemetry,
                prediction=prediction,
            )

    pdf_bytes = generate_advisory_pdf(
        farm_config=farm_cfg,
        telemetry=telemetry,
        ml_prediction=prediction,
        advisory_text=clean_adv,
        logo_path=logo_path,
    )

    filename = f"sarva_mitra_{req.crop}_report_{datetime.now(IST).strftime('%Y%m%d_%H%M')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/report/pdf", tags=["Reports / PDF"])
def generate_pdf_report_get_endpoint(
    crop: str = "Tomato",
    location: str = "Vijayawada, AP",
    lat: float = 16.51,
    lon: float = 80.52,
    stage: str = "Flowering & Fruit Set (50-80 days)",
    advisory_text: str | None = None,
):
    """GET endpoint enabling direct mobile/browser downloads of the advisory PDF report."""
    req = PDFReportRequest(
        crop=crop,
        location=location,
        lat=lat,
        lon=lon,
        stage=stage,
        advisory_text=advisory_text,
    )
    return generate_pdf_report_endpoint(req)


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

# ---------------------------------------------------------------------------
# Mount Modern Web UI (HTML/CSS/JS)
# ---------------------------------------------------------------------------
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

WEB_DIR = Path(__file__).resolve().parent.parent / "frontend" / "web"
if WEB_DIR.exists():
    app.mount("/ui", StaticFiles(directory=str(WEB_DIR), html=True), name="web_ui")

@app.get("/app", include_in_schema=False)
def app_redirect():
    return RedirectResponse(url="/ui/")
