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

        # 4. Default / General Agronomic Overview
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
class PDFReportRequest(BaseModel):
    crop: str = Field(default="tomato", description="Target crop")
    location: str = Field(default="Vijayawada", description="Farm location name")
    lat: float = Field(default=16.51, description="Farm latitude")
    lon: float = Field(default=80.52, description="Farm longitude")
    stage: str = Field(default="🌸 Flowering & Fruit Set (50-80 days)", description="Growth stage")
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

    # Resolve official Sarva Mitra logo (SVG preferred, then JPG)
    project_root = Path(__file__).resolve().parent.parent
    logo_svg = project_root / "frontend" / "assets" / "logo.svg"
    logo_web_svg = project_root / "frontend" / "web" / "assets" / "logo.svg"
    logo_jpg = project_root / "frontend" / "assets" / "logo.jpg"
    logo_path = logo_svg if logo_svg.exists() else (logo_web_svg if logo_web_svg.exists() else (logo_jpg if logo_jpg.exists() else None))

    # Generate PDF bytes with official logo
    clean_adv = clean_advisory_text(req.advisory_text or "Official agronomic advisory report.")
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
