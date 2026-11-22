"""Sarva Mitra — Universal Farm Companion.

Streamlit Frontend featuring:
1. 🎨 Dynamic Light & Dark Mode theme switcher with true high-contrast agronomic palettes.
2. 🏷️ HTML Elements with embedded vector logo (logo.svg) and glassmorphic UI components.
3. 📊 Farm Monitoring Page (Live Virtual Telemetry, ML Risk Gauge 0-100%, Soil/Terrain Properties, 8-day Historical Charts, Interactive What-If Farm Simulator).
4. 📄 One-Click Downloadable Official PDF Advisory Report (built with ReportLab + logo.svg).
5. 💬 Continuous AI Agronomic Chat with Dual RAG Prompts:
   - Turn 1: Comprehensive Initial Diagnostic Report (Field Assessment & PDF Export).
   - Turn 2+: Conversational Q&A (Direct explanation, intent clarification, document citations, and 2-3 suggested follow-up queries).
6. 🎙️ Dual Voice Support (Groq Whisper Turbo STT + gTTS Audio Playback).

Run:
    streamlit run frontend/app.py
"""
from __future__ import annotations

import base64
import io
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from frontend.pdf_generator import generate_advisory_pdf

load_dotenv(PROJECT_ROOT / ".env")

IST = timezone(timedelta(hours=5, minutes=30))
LOGO_SVG_PATH = PROJECT_ROOT / "frontend" / "assets" / "logo.svg"
LOGO_JPG_PATH = PROJECT_ROOT / "frontend" / "assets" / "logo.jpg"

# Cache SVG Base64 encoding for HTML embedding
@st.cache_data
def get_logo_b64() -> str:
    if LOGO_SVG_PATH.exists():
        return base64.b64encode(LOGO_SVG_PATH.read_bytes()).decode("utf-8")
    return ""

LOGO_B64 = get_logo_b64()

# Trained location presets from static_features.csv
LOCATIONS = {
    "Vijayawada (Andhra Pradesh)": {"lat": 16.51, "lon": 80.52, "name": "Vijayawada"},
    "Bengaluru (Karnataka)": {"lat": 12.97, "lon": 77.59, "name": "Bengaluru"},
    "Hyderabad (Telangana)": {"lat": 17.39, "lon": 78.49, "name": "Hyderabad"},
    "Chennai (Tamil Nadu)": {"lat": 13.08, "lon": 80.27, "name": "Chennai"},
    "Nagpur (Maharashtra)": {"lat": 21.15, "lon": 79.09, "name": "Nagpur"},
    "Bhubaneswar (Odisha)": {"lat": 20.30, "lon": 85.82, "name": "Bhubaneswar"},
    "Lucknow (Uttar Pradesh)": {"lat": 26.85, "lon": 80.95, "name": "Lucknow"},
    "Jaipur (Rajasthan)": {"lat": 26.91, "lon": 75.79, "name": "Jaipur"},
    "Kolkata (West Bengal)": {"lat": 22.57, "lon": 88.36, "name": "Kolkata"},
    "Patna (Bihar)": {"lat": 25.61, "lon": 85.14, "name": "Patna"},
    "Custom Location (Enter Coordinates)": {"lat": 16.51, "lon": 80.52, "name": "Custom Farm"},
}

CROPS = {
    "Tomato 🍅": "tomato",
    "Chilli 🌶️": "chilli",
    "Ragi (Finger Millet) 🌾": "ragi",
}

CROP_STAGES = [
    "🌱 Seedling / Nursery Stage (0-25 days)",
    "🌿 Vegetative Canopy Growth (25-50 days)",
    "🌸 Flowering & Fruit Set (50-80 days)",
    "🍅 Fruit Maturation & Harvesting (80+ days)",
]

st.set_page_config(
    page_title="Sarva Mitra — Universal Farm Companion",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Theme Management (High-Contrast Agronomic Light & Dark Palettes)
# ---------------------------------------------------------------------------
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "🌙 Agronomic Dark"


def apply_theme_css(is_dark: bool):
    """Injects comprehensive CSS overrides guaranteeing true visual distinction between Dark & Light modes."""
    if is_dark:
        st.markdown("""
        <style>
            /* ============================================================ */
            /* TRUE AGRONOMIC DARK MODE                                     */
            /* ============================================================ */
            :root {
                --bg-primary: #0a110d;
                --bg-secondary: #0f1a13;
                --bg-card: #132219;
                --border-color: #203829;
                --accent-green: #10b981;
                --accent-glow: rgba(16, 185, 129, 0.25);
                --text-main: #e6efe9;
                --text-sub: #96b2a0;
                --text-title: #ffffff;
            }

            html, body, .stApp {
                background-color: var(--bg-primary) !important;
                color: var(--text-main) !important;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            }

            header[data-testid="stHeader"] {
                background-color: transparent !important;
            }

            [data-testid="stSidebar"] {
                background-color: var(--bg-secondary) !important;
                border-right: 1px solid var(--border-color) !important;
            }

            [data-testid="stSidebar"] * {
                color: var(--text-main) !important;
            }

            .main .block-container {
                padding-top: 1.8rem;
                padding-bottom: 2rem;
                max-width: 1200px;
            }

            /* Custom HTML Cards */
            .hero-header-box {
                background: linear-gradient(135deg, #111e16 0%, #172a1e 100%);
                border: 1px solid #244130;
                border-radius: 14px;
                padding: 1.4rem 1.6rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
            }

            .telemetry-card {
                background: linear-gradient(145deg, #14241b, #0f1b14) !important;
                border: 1px solid #233b2c !important;
                border-radius: 12px;
                padding: 1.1rem;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            .telemetry-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(16, 185, 129, 0.15);
                border-color: #2f533e !important;
            }

            .status-chip {
                display: inline-block;
                padding: 0.2rem 0.6rem;
                border-radius: 12px;
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                margin-top: 0.4rem;
            }
            .chip-optimal { background: #133323; color: #34d399; border: 1px solid #1c5237; }
            .chip-warning { background: #382d12; color: #fbbf24; border: 1px solid #574418; }
            .chip-danger { background: #3d1418; color: #f87171; border: 1px solid #631f26; }

            .pdf-download-card {
                background: linear-gradient(135deg, #13271d, #1a3828);
                border: 1px solid #2b563d;
                border-radius: 12px;
                padding: 1.2rem;
                margin: 1rem 0;
                box-shadow: 0 4px 16px rgba(16, 185, 129, 0.15);
            }

            [data-testid="stChatMessage"] {
                background-color: #122018 !important;
                border: 1px solid #1f3527 !important;
                border-radius: 12px !important;
                margin-bottom: 0.85rem;
                color: #e6efe9 !important;
            }

            [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
                color: #e6efe9 !important;
            }

            [data-testid="stMetricValue"] {
                font-size: 1.8rem !important;
                font-weight: 700 !important;
                color: #10b981 !important;
            }
            [data-testid="stMetricLabel"] {
                color: #9cb8a5 !important;
                font-weight: 500 !important;
            }

            /* Streamlit Inputs */
            div[data-baseweb="select"] > div, input, textarea {
                background-color: #121f17 !important;
                color: #e6efe9 !important;
                border-color: #233b2c !important;
            }

            /* Buttons */
            .stButton>button {
                border-radius: 8px;
                background-color: #15271d;
                color: #e6efe9;
                border: 1px solid #284734;
                transition: all 0.2s ease-in-out;
            }
            .stButton>button:hover {
                background-color: #1b3527;
                border-color: #10b981;
                box-shadow: 0 4px 14px rgba(16, 185, 129, 0.25);
                transform: translateY(-1px);
            }
            .stButton>button[kind="primary"] {
                background-color: #10b981 !important;
                color: #062112 !important;
                font-weight: 600 !important;
                border: none !important;
            }

            /* Expanders */
            [data-testid="stExpander"] {
                background-color: #111d16 !important;
                border: 1px solid #1e3526 !important;
                border-radius: 10px !important;
            }

            .voice-badge {
                display: inline-block;
                background: #143324;
                color: #34d399;
                padding: 0.25rem 0.65rem;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 600;
                border: 1px solid #1e4e36;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
            /* ============================================================ */
            /* CLEAN AGRONOMIC LIGHT MODE                                   */
            /* ============================================================ */
            :root {
                --bg-primary: #f8faf8;
                --bg-secondary: #edf3ee;
                --bg-card: #ffffff;
                --border-color: #d6e2d8;
                --accent-green: #1b7a42;
                --text-main: #18281d;
                --text-sub: #496352;
                --text-title: #0e1c12;
            }

            html, body, .stApp {
                background-color: var(--bg-primary) !important;
                color: var(--text-main) !important;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            }

            header[data-testid="stHeader"] {
                background-color: transparent !important;
            }

            [data-testid="stSidebar"] {
                background-color: var(--bg-secondary) !important;
                border-right: 1px solid var(--border-color) !important;
            }

            [data-testid="stSidebar"] * {
                color: var(--text-main) !important;
            }

            .main .block-container {
                padding-top: 1.8rem;
                padding-bottom: 2rem;
                max-width: 1200px;
            }

            /* Custom HTML Cards */
            .hero-header-box {
                background: linear-gradient(135deg, #ffffff 0%, #f1f7f2 100%);
                border: 1px solid #cfe0d2;
                border-radius: 14px;
                padding: 1.4rem 1.6rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 18px rgba(46, 125, 50, 0.08);
            }

            .telemetry-card {
                background: #ffffff !important;
                border: 1px solid #dbe6dd !important;
                border-radius: 12px;
                padding: 1.1rem;
                box-shadow: 0 2px 12px rgba(46, 125, 50, 0.06);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            .telemetry-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 18px rgba(46, 125, 50, 0.12);
                border-color: #b8d4be !important;
            }

            .status-chip {
                display: inline-block;
                padding: 0.2rem 0.6rem;
                border-radius: 12px;
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                margin-top: 0.4rem;
            }
            .chip-optimal { background: #e8f5e9; color: #1b5e20; border: 1px solid #c8e6c9; }
            .chip-warning { background: #fff8e1; color: #b78103; border: 1px solid #ffecb3; }
            .chip-danger { background: #ffebee; color: #c62828; border: 1px solid #ffcdd2; }

            .pdf-download-card {
                background: linear-gradient(135deg, #edf7ef, #e2f1e6);
                border: 1px solid #bddbc3;
                border-radius: 12px;
                padding: 1.2rem;
                margin: 1rem 0;
                box-shadow: 0 2px 12px rgba(46, 125, 50, 0.08);
            }

            [data-testid="stChatMessage"] {
                background-color: #ffffff !important;
                border: 1px solid #dbe6dd !important;
                border-radius: 12px !important;
                margin-bottom: 0.85rem;
                color: #18281d !important;
            }

            [data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
                color: #18281d !important;
            }

            [data-testid="stMetricValue"] {
                font-size: 1.8rem !important;
                font-weight: 700 !important;
                color: #1b7a42 !important;
            }
            [data-testid="stMetricLabel"] {
                color: #496352 !important;
                font-weight: 500 !important;
            }

            div[data-baseweb="select"] > div, input, textarea {
                background-color: #ffffff !important;
                color: #18281d !important;
                border-color: #dbe6dd !important;
            }

            .stButton>button {
                border-radius: 8px;
                background-color: #ffffff;
                color: #18281d;
                border: 1px solid #cfe0d2;
                transition: all 0.2s ease-in-out;
            }
            .stButton>button:hover {
                background-color: #f2f8f4;
                border-color: #1b7a42;
                box-shadow: 0 4px 12px rgba(46, 125, 50, 0.15);
                transform: translateY(-1px);
            }
            .stButton>button[kind="primary"] {
                background-color: #1b7a42 !important;
                color: #ffffff !important;
                font-weight: 600 !important;
                border: none !important;
            }

            [data-testid="stExpander"] {
                background-color: #ffffff !important;
                border: 1px solid #dbe6dd !important;
                border-radius: 10px !important;
            }

            .voice-badge {
                display: inline-block;
                background: #e8f5e9;
                color: #1b5e20;
                padding: 0.25rem 0.65rem;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 600;
                border: 1px solid #c8e6c9;
            }
        </style>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Lazy Load Backend Modules
# ---------------------------------------------------------------------------
@st.cache_resource
def get_services():
    from backend.telemetry_service.service import telemetry_service
    from backend.ml_engine.backend import load_bundle, load_static, run_prediction, PredictRequest
    from backend.rag_pipeline.rag import RAGPipeline

    bundle = load_bundle()
    static = load_static()
    rag = RAGPipeline()
    return telemetry_service, bundle, static, run_prediction, PredictRequest, rag

try:
    telemetry_service, ml_bundle, ml_static, run_prediction, PredictRequest, rag_pipeline = get_services()
    backend_ready = True
except Exception as exc:
    backend_ready = False
    init_error = exc


# ---------------------------------------------------------------------------
# Voice Utilities: STT (Groq Whisper) & TTS (gTTS)
# ---------------------------------------------------------------------------
def transcribe_voice(audio_bytes: bytes, filename: str = "query.wav") -> str:
    """Transcribes farmer spoken query via Groq Whisper API (whisper-large-v3-turbo)."""
    if not audio_bytes:
        return ""
    try:
        from groq import Groq
        from backend.rag_pipeline.config import GROQ_API_KEYS
        for key in reversed(GROQ_API_KEYS):
            try:
                client = Groq(api_key=key)
                audio_file = io.BytesIO(audio_bytes)
                audio_file.name = filename
                transcription = client.audio.transcriptions.create(
                    file=audio_file,
                    model="whisper-large-v3-turbo",
                    response_format="text",
                )
                text = str(transcription).strip()
                if text:
                    return text
            except Exception:
                continue
    except Exception as exc:
        st.warning(f"Voice transcription note: {exc}")
    return ""


@st.cache_data(show_spinner=False)
def generate_audio_speech(text: str, lang: str = "en") -> bytes:
    """Generates audio voice bytes from advisory text using gTTS."""
    clean = re.sub(r"\[.*?\]|\(.*?\)|#+|\*+|_|`", " ", text)
    clean = re.sub(r"BEGIN_STRUCTURED_JSON[\s\S]*?END_STRUCTURED_JSON", "", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    if len(clean) > 550:
        clean = clean[:550].rsplit(".", 1)[0] + "."
    try:
        from gtts import gTTS
        tts = gTTS(text=clean, lang=lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception:
        return b""


# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "telemetry" not in st.session_state:
    st.session_state.telemetry = None

if "history" not in st.session_state:
    st.session_state.history = None

if "ml_prediction" not in st.session_state:
    st.session_state.ml_prediction = None

if "structured_advisory" not in st.session_state:
    st.session_state.structured_advisory = None

if "pdf_report_bytes" not in st.session_state:
    st.session_state.pdf_report_bytes = None

if "farm_config" not in st.session_state:
    st.session_state.farm_config = {"lat": 16.51, "lon": 80.52, "name": "Vijayawada", "crop": "tomato", "stage": CROP_STAGES[2]}

if "conversation_summary" not in st.session_state:
    st.session_state.conversation_summary = ""

if "simulated_scenario" not in st.session_state:
    st.session_state.simulated_scenario = None


def execute_pipeline(lat: float, lon: float, loc_name: str, crop_name: str, stage_name: str):
    """Executes Telemetry -> ML Engine -> RAG Pipeline (Prompt 1: Report Mode) and generates PDF Report."""
    today = datetime.now(IST).date()
    
    # 1. Fetch live telemetry & historical backfill
    readings = telemetry_service.get_current_readings(lat=lat, lon=lon)
    history = telemetry_service.get_historical_records(lat=lat, lon=lon, target_date=today, days=8)
    
    # 2. Run ML Risk Engine
    ml_req = PredictRequest(
        device_id="virtual-node-01",
        location=loc_name,
        lat=lat,
        lon=lon,
        target_date=today,
        history=history,
    )
    prediction = run_prediction(ml_req, ml_bundle, ml_static, today)
    risk_info = prediction.get("prediction", {})
    risk_level = risk_info.get("risk_level") or risk_info.get("risk_label", "low")
    risk_pct = risk_info.get("risk_pct", 0.0)
    ml_out = 1 if risk_level in {"moderate", "high"} else 0

    # 3. Formulate comprehensive initial RAG Report (PROMPT 1: Report Mode)
    initial_query = f"Provide a complete agronomic status assessment and recommendations for {crop_name} ({stage_name}) based on current field conditions."
    rag_readings = {
        "temperature_c": readings.get("temperature_c", 25.0),
        "humidity_pct": readings.get("humidity_pct", 65.0),
        "soil_moisture_pct": readings.get("soil_moisture_pct", 25.0),
        "rainfall_mm": readings.get("rainfall_mm", 0.0),
        "sunlight_wm2": readings.get("sunlight_wm2", 200.0),
        "risk_pct": risk_pct,
        "risk_level": risk_level,
    }

    farm_cfg = {"lat": lat, "lon": lon, "name": loc_name, "crop": crop_name, "stage": stage_name}

    answer, structured = rag_pipeline.answer(
        readings=rag_readings,
        ml_output=ml_out,
        crop=crop_name,
        location=loc_name,
        question=initial_query,
        chat_history=[],
        ml_prediction=prediction,
        mode="report",
    )

    # 4. Generate Official Downloadable PDF Advisory Report using logo.svg
    pdf_bytes = generate_advisory_pdf(
        farm_config=farm_cfg,
        telemetry=readings,
        ml_prediction=prediction,
        advisory_text=answer,
        logo_path=LOGO_SVG_PATH if LOGO_SVG_PATH.exists() else LOGO_JPG_PATH,
    )

    # Store state
    st.session_state.telemetry = readings
    st.session_state.history = history
    st.session_state.ml_prediction = prediction
    st.session_state.structured_advisory = structured
    st.session_state.pdf_report_bytes = pdf_bytes
    st.session_state.farm_config = farm_cfg

    # Initial greeting & advisory message in chat
    intro_prefix = (
        f"👋 **Namaste! Telemetry synchronized & initial agronomic assessment ready for {crop_name.title()} ({stage_name}):**\n\n"
        f"- 🌡️ **Temperature:** {readings.get('temperature_c', 0.0):.1f} °C\n"
        f"- 💧 **Relative Humidity:** {readings.get('humidity_pct', 0.0):.1f} %\n"
        f"- 🌱 **Soil Moisture:** {readings.get('soil_moisture_pct', 0.0):.1f} %\n"
        f"- 🧠 **AI Pathogen Risk Index:** {risk_pct}% ({risk_level.title()})\n\n"
        f"---\n\n"
    )
    st.session_state.messages = [
        {"role": "assistant", "content": intro_prefix + answer}
    ]


# ---------------------------------------------------------------------------
# Sidebar Navigation, Theme Toggle & Farm Configuration
# ---------------------------------------------------------------------------
with st.sidebar:
    # Embedded High-Resolution Logo
    if LOGO_B64:
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 0.8rem;">
                <img src="data:image/svg+xml;base64,{LOGO_B64}" style="width: 90%; max-width: 250px; height: auto;" alt="Sarva Mitra Logo" />
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif LOGO_JPG_PATH.exists():
        st.image(str(LOGO_JPG_PATH), use_container_width=True)
    else:
        st.markdown("## 🌱 Sarva Mitra")
        st.caption("One device. Any farm. Any language.")

    st.markdown("---")
    
    # 🎨 Light / Dark Mode Switch
    st.markdown("##### 🎨 UI Appearance")
    theme_choice = st.radio(
        "Theme Mode",
        ["🌙 Agronomic Dark", "☀️ Clean Light"],
        index=0 if st.session_state.theme_mode == "🌙 Agronomic Dark" else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
    if theme_choice != st.session_state.theme_mode:
        st.session_state.theme_mode = theme_choice
        st.rerun()

    apply_theme_css(st.session_state.theme_mode == "🌙 Agronomic Dark")

    st.markdown("---")
    page = st.radio(
        "📌 Navigation",
        ["📊 Monitoring Page", "💬 AI Agronomic Chat"],
        index=0,
        help="Switch between Farm Monitoring telemetry & continuous AI chat",
    )

    st.markdown("---")
    st.subheader("🌾 Farm Setup & Crop Stage")

    loc_choice = st.selectbox("Select Location Preset:", list(LOCATIONS.keys()), index=0)
    selected_preset = LOCATIONS[loc_choice]

    if loc_choice == "Custom Location (Enter Coordinates)":
        c_lat, c_lon = st.columns(2)
        cur_lat = c_lat.number_input("Lat", value=st.session_state.farm_config.get("lat", 16.51), format="%.4f")
        cur_lon = c_lon.number_input("Lon", value=st.session_state.farm_config.get("lon", 80.52), format="%.4f")
        cur_name = st.text_input("Farm Name", value="My Farm")
    else:
        cur_lat = selected_preset["lat"]
        cur_lon = selected_preset["lon"]
        cur_name = selected_preset["name"]
        st.caption(f"Coordinates: `{cur_lat}, {cur_lon}`")

    crop_label = st.selectbox("Crop Type:", list(CROPS.keys()), index=0)
    cur_crop = CROPS[crop_label]

    cur_stage = st.selectbox("Current Growth Stage:", CROP_STAGES, index=2)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Sync Telemetry", type="primary", use_container_width=True):
            if not backend_ready:
                st.error(f"Cannot initialize services: {init_error}")
            else:
                with st.spinner("Fetching virtual telemetry & evaluating ML model..."):
                    execute_pipeline(cur_lat, cur_lon, cur_name, cur_crop, cur_stage)
                    st.success("Telemetry updated!")
                    st.rerun()

    with col_btn2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_summary = ""
            st.rerun()


# Auto-run pipeline on very first page load
if st.session_state.telemetry is None and backend_ready:
    with st.spinner("Initializing Sarva Mitra Virtual Telemetry & ML Engine..."):
        execute_pipeline(cur_lat, cur_lon, cur_name, cur_crop, cur_stage)


# ---------------------------------------------------------------------------
# PAGE 1: 📊 MONITORING PAGE
# ---------------------------------------------------------------------------
if page == "📊 Monitoring Page":
    farm = st.session_state.farm_config
    telemetry = st.session_state.telemetry or {}
    history = st.session_state.history or []
    pred_data = st.session_state.ml_prediction or {}
    risk_info = pred_data.get("prediction", {})
    risk_pct = risk_info.get("risk_pct", 0.0)
    risk_level = risk_info.get("risk_level") or risk_info.get("risk_label", "low")

    # Custom HTML Hero Header with embedded Logo
    logo_img_tag = (
        f'<img src="data:image/svg+xml;base64,{LOGO_B64}" style="height: 48px; width: auto; margin-right: 18px; vertical-align: middle;" />'
        if LOGO_B64 else "🌱"
    )
    is_dark = st.session_state.theme_mode == "🌙 Agronomic Dark"
    hero_title_color = "#ffffff" if is_dark else "#0e1c12"
    hero_sub_color = "#96b2a0" if is_dark else "#496352"

    st.markdown(
        f"""
        <div class="hero-header-box">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
                <div style="display: flex; align-items: center;">
                    {logo_img_tag}
                    <div>
                        <h2 style="margin: 0; color: {hero_title_color}; font-size: 1.55rem; font-weight: 700;">
                            Sarva Mitra — Farm Monitoring
                        </h2>
                        <p style="margin: 3px 0 0 0; color: {hero_sub_color}; font-size: 0.88rem;">
                            Live microclimate telemetry & AI pathogen risk forecasting for <b>{farm['name']}</b> • <b>{farm['crop'].title()}</b> ({farm.get('stage', 'Flowering')})
                        </p>
                    </div>
                </div>
                <div style="text-align: right; margin-top: 8px;">
                    <span class="voice-badge">● LIVE TELEMETRY</span><br/>
                    <small style="color: {hero_sub_color};">Refreshed: {datetime.now(IST).strftime('%I:%M:%S %p IST')}</small>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not backend_ready:
        st.error(f"Backend services could not be initialized: {init_error}")
        st.stop()

    # 1. Real-time Telemetry Metric Cards
    st.subheader("📡 Real-Time Environmental & Soil Telemetry")
    if telemetry:
        c1, c2, c3, c4, c5 = st.columns(5)
        
        # Helper to determine threshold status tags
        t_temp = telemetry.get("temperature_c", 0.0)
        t_hum = telemetry.get("humidity_pct", 0.0)
        t_sm = telemetry.get("soil_moisture_pct", 0.0)
        t_rain = telemetry.get("rainfall_mm", 0.0)
        t_sun = telemetry.get("sunlight_wm2", 0.0)

        chip_temp = "chip-optimal" if 18.0 <= t_temp <= 32.0 else "chip-warning"
        lbl_temp = "Optimal" if 18.0 <= t_temp <= 32.0 else "Stress"

        chip_hum = "chip-danger" if t_hum > 80.0 else ("chip-optimal" if 50.0 <= t_hum <= 75.0 else "chip-warning")
        lbl_hum = "Foliar Risk" if t_hum > 80.0 else ("Optimal" if 50.0 <= t_hum <= 75.0 else "Dry Air")

        chip_sm = "chip-danger" if t_sm < 15.0 else ("chip-optimal" if 18.0 <= t_sm <= 30.0 else "chip-warning")
        lbl_sm = "Water Stress" if t_sm < 15.0 else ("Adequate" if 18.0 <= t_sm <= 30.0 else "Saturated")

        with c1:
            st.markdown(f"""
            <div class='telemetry-card'>
                <small style="color: var(--text-sub);">🌡️ Ambient Air Temp</small>
                <div style="font-size: 1.85rem; font-weight: 700; color: var(--accent-green); margin: 4px 0;">{t_temp:.1f} °C</div>
                <span class="status-chip {chip_temp}">{lbl_temp}</span>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class='telemetry-card'>
                <small style="color: var(--text-sub);">💧 Relative Humidity</small>
                <div style="font-size: 1.85rem; font-weight: 700; color: var(--accent-green); margin: 4px 0;">{t_hum:.1f} %</div>
                <span class="status-chip {chip_hum}">{lbl_hum}</span>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class='telemetry-card'>
                <small style="color: var(--text-sub);">🌱 Soil Moisture</small>
                <div style="font-size: 1.85rem; font-weight: 700; color: var(--accent-green); margin: 4px 0;">{t_sm:.1f} %</div>
                <span class="status-chip {chip_sm}">{lbl_sm}</span>
            </div>
            """, unsafe_allow_html=True)

        with c4:
            st.markdown(f"""
            <div class='telemetry-card'>
                <small style="color: var(--text-sub);">🌧️ Daily Rainfall</small>
                <div style="font-size: 1.85rem; font-weight: 700; color: var(--accent-green); margin: 4px 0;">{t_rain:.1f} mm</div>
                <span class="status-chip chip-optimal">Accumulated</span>
            </div>
            """, unsafe_allow_html=True)

        with c5:
            st.markdown(f"""
            <div class='telemetry-card'>
                <small style="color: var(--text-sub);">☀️ Solar Radiation</small>
                <div style="font-size: 1.85rem; font-weight: 700; color: var(--accent-green); margin: 4px 0;">{t_sun:.0f} W/m²</div>
                <span class="status-chip chip-optimal">Shortwave</span>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. ML Risk Engine Section & Official PDF Download Callout
    st.subheader("🧠 Machine Learning Weather Risk Engine")
    
    col_risk_meter, col_risk_details = st.columns([1, 2])
    
    with col_risk_meter:
        st.markdown("#### Crop Disease Risk Index")
        st.progress(min(1.0, max(0.0, risk_pct / 100.0)))
        
        if risk_level == "low":
            st.success(f"### 🟢 {risk_pct}% — Low Risk")
            st.caption("Conditions are optimal. Fungal and foliar pathogen development is restrained.")
        elif risk_level == "moderate":
            st.warning(f"### 🟡 {risk_pct}% — Moderate Risk")
            st.caption("Favorable moisture/humidity window. Monitor foliage for initial lesion development.")
        else:
            st.error(f"### 🔴 {risk_pct}% — High Risk")
            st.caption("High weather-proxy risk. Elevated potential for foliar blight, damping-off, or insect stress.")

    with col_risk_details:
        st.markdown("#### Model Decision Parameters")
        b_name = pred_data.get("model", {}).get("name", "XGBoost / LightGBM Ensemble")
        target_d = pred_data.get("target_date", datetime.now(IST).strftime("%Y-%m-%d"))
        
        r1, r2, r3 = st.columns(3)
        r1.metric("Trained Model", b_name)
        r2.metric("Target Date", target_d)
        r3.metric("Action Signal", "1 (Active Signal)" if risk_level in {"moderate", "high"} else "0 (Normal)")

        st.caption("Evaluated using 8 consecutive days of soil moisture lag, 3-day & 7-day cumulative rainfall windows, solar irradiance, and seasonal periodicity.")

    # 3. 📄 Official PDF Report Callout & One-Click Download
    if st.session_state.pdf_report_bytes:
        st.markdown(
            f"""
            <div class="pdf-download-card">
                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
                    <div>
                        <h4 style="margin: 0; color: var(--accent-green); font-size: 1.1rem;">📄 Official Agronomic Advisory PDF Report</h4>
                        <p style="margin: 3px 0 0 0; color: var(--text-sub); font-size: 0.85rem;">
                            Includes high-res vector logo, live farm sensor table, ML risk scores, and full agronomic field guidance.
                        </p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.download_button(
            label="📄 Download Official PDF Advisory Report",
            data=st.session_state.pdf_report_bytes,
            file_name=f"sarva_mitra_{farm['crop']}_advisory_{datetime.now(IST).strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. 🧪 Interactive Farm Stress Simulator & What-If Tester
    with st.expander("🧪 Interactive Farm Simulator & Stress Tester (Test What-If Scenarios)", expanded=False):
        st.markdown("Adjust environmental sliders to simulate weather stress and instantly test the ML risk engine's response:")
        sim_col1, sim_col2, sim_col3, sim_col4 = st.columns(4)
        sim_temp = sim_col1.slider("Simulated Temp (°C)", 10.0, 45.0, float(telemetry.get("temperature_c", 25.0)), step=0.5)
        sim_hum = sim_col2.slider("Simulated Humidity (%)", 20.0, 100.0, float(telemetry.get("humidity_pct", 70.0)), step=1.0)
        sim_sm = sim_col3.slider("Simulated Soil Moisture (%)", 5.0, 50.0, float(telemetry.get("soil_moisture_pct", 22.0)), step=0.5)
        sim_rain = sim_col4.slider("Simulated Rainfall (mm)", 0.0, 50.0, float(telemetry.get("rainfall_mm", 0.0)), step=1.0)

        if st.button("🚀 Evaluate Scenario with ML Engine", use_container_width=True):
            sim_history = list(history) if history else []
            if sim_history:
                sim_history[-1] = {
                    **sim_history[-1],
                    "soil_moisture_pct": sim_sm,
                    "rainfall_mm": sim_rain,
                    "air_temperature_c": sim_temp,
                    "humidity_pct": sim_hum,
                }
            sim_req = PredictRequest(
                device_id="virtual-node-01",
                location=farm["name"],
                lat=farm["lat"],
                lon=farm["lon"],
                target_date=datetime.now(IST).date(),
                history=sim_history,
            )
            sim_pred = run_prediction(sim_req, ml_bundle, ml_static, datetime.now(IST).date())
            sim_risk = sim_pred.get("prediction", {})
            st.session_state.simulated_scenario = sim_risk
            
        if st.session_state.simulated_scenario:
            s_risk = st.session_state.simulated_scenario
            s_pct = s_risk.get("risk_pct", 0.0)
            s_lvl = s_risk.get("risk_level", "low")
            st.info(f"**Simulated Outcome:** ML Risk evaluated at **{s_pct}% ({s_lvl.upper()})** for simulated conditions ({sim_temp}°C, {sim_hum}% RH, {sim_sm}% SM).")

    st.markdown("<br>", unsafe_allow_html=True)

    # 5. Historical Telemetry Charts (8-Day Window)
    if history:
        st.subheader("📈 8-Day Historical Telemetry Trends")
        hist_df = pd.DataFrame(history)
        if "date" in hist_df.columns:
            hist_df["date"] = pd.to_datetime(hist_df["date"]).dt.strftime("%b %d")
            hist_df = hist_df.set_index("date")

            tab_chart1, tab_chart2, tab_table = st.tabs(["🌱 Soil Moisture & Rainfall", "🌡️ Temperature & Humidity", "📋 Raw History Table"])
            
            with tab_chart1:
                chart_cols = [c for c in ["soil_moisture_pct", "rainfall_mm"] if c in hist_df.columns]
                st.line_chart(hist_df[chart_cols])
            
            with tab_chart2:
                chart_cols2 = [c for c in ["air_temperature_c", "humidity_pct"] if c in hist_df.columns]
                st.line_chart(hist_df[chart_cols2])

            with tab_table:
                st.dataframe(hist_df, use_container_width=True)

    # 6. Static Soil & Terrain Properties
    key = (round(farm["lat"], 2), round(farm["lon"], 2))
    if key not in ml_static:
        key = min(ml_static.keys(), key=lambda pt: (pt[0]-farm["lat"])**2 + (pt[1]-farm["lon"])**2)
    soil_data = ml_static.get(key, {})

    if soil_data:
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🌍 Soil Characteristics & Elevation (ISRIC SoilGrids)")
        s1, s2, s3, s4, s5, s6 = st.columns(6)
        s1.metric("Soil pH", f"{soil_data.get('soil_ph', 7.0):.1f}")
        s2.metric("Organic Carbon", f"{soil_data.get('organic_carbon', 15.0):.1f} g/kg")
        s3.metric("Clay", f"{soil_data.get('clay_pct', 30.0):.1f} %")
        s4.metric("Sand", f"{soil_data.get('sand_pct', 40.0):.1f} %")
        s5.metric("Silt", f"{soil_data.get('silt_pct', 30.0):.1f} %")
        s6.metric("Elevation", f"{soil_data.get('elevation_m', 0.0):.0f} m")


# ---------------------------------------------------------------------------
# PAGE 2: 💬 AI AGRONOMIC CHAT (With Voice & Dual Prompts)
# ---------------------------------------------------------------------------
elif page == "💬 AI Agronomic Chat":
    farm = st.session_state.farm_config
    telemetry = st.session_state.telemetry or {}
    pred_data = st.session_state.ml_prediction or {}
    risk_info = pred_data.get("prediction", {})
    risk_pct = risk_info.get("risk_pct", 0.0)
    risk_level = risk_info.get("risk_level") or risk_info.get("risk_label", "low")

    # Header with voice badge
    logo_img_tag = (
        f'<img src="data:image/svg+xml;base64,{LOGO_B64}" style="height: 44px; width: auto; margin-right: 16px; vertical-align: middle;" />'
        if LOGO_B64 else "🌱"
    )
    is_dark = st.session_state.theme_mode == "🌙 Agronomic Dark"
    hero_title_color = "#ffffff" if is_dark else "#0e1c12"
    hero_sub_color = "#96b2a0" if is_dark else "#496352"

    st.markdown(
        f"""
        <div class="hero-header-box">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
                <div style="display: flex; align-items: center;">
                    {logo_img_tag}
                    <div>
                        <h2 style="margin: 0; color: {hero_title_color}; font-size: 1.45rem; font-weight: 700;">
                            Sarva Mitra — AI Agronomic Assistant
                        </h2>
                        <p style="margin: 3px 0 0 0; color: {hero_sub_color}; font-size: 0.86rem;">
                            Continuous agronomic guidance grounded in live sensor telemetry for <b>{farm['crop'].title()}</b> at <b>{farm['name']}</b>
                        </p>
                    </div>
                </div>
                <div style="text-align: right; margin-top: 6px;">
                    <span class="voice-badge">🎙️ VOICE ENABLED</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Quick PDF Report Download Button if available
    if st.session_state.pdf_report_bytes:
        c_pdf1, c_pdf2 = st.columns([3, 1])
        with c_pdf1:
            st.caption("📄 Download the official diagnostic assessment report generated for your current farm telemetry:")
        with c_pdf2:
            st.download_button(
                label="📥 Download PDF Report",
                data=st.session_state.pdf_report_bytes,
                file_name=f"sarva_mitra_{farm['crop']}_report_{datetime.now(IST).strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    # 💡 Suggested Questions Chips
    st.markdown("##### 💡 Suggested Questions & Quick Inquiries:")
    chip_col1, chip_col2, chip_col3 = st.columns(3)
    if chip_col1.button("💧 Should I irrigate today based on soil moisture?", use_container_width=True):
        st.session_state.prompt_input = "Should I irrigate today based on my current soil moisture and weather?"
    if chip_col2.button("🔍 What specific symptoms should I inspect for?", use_container_width=True):
        st.session_state.prompt_input = "What specific diseases or pests should I inspect for given current temperature and humidity?"
    if chip_col3.button("🍂 How to prevent flower drop and yellow leaves?", use_container_width=True):
        st.session_state.prompt_input = "How can I prevent flower drop and yellowing leaves under these conditions?"

    # 🧠 Persistent Conversational Memory Expander
    if st.session_state.get("conversation_summary"):
        with st.expander("🧠 Persistent Conversational Memory (Progressive LLM Summary)", expanded=False):
            st.caption("Older chat turns are consolidated into this running memory context so historical details are never lost:")
            st.info(st.session_state.conversation_summary)

    # 📜 Render continuous chat history
    for idx, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                audio_data = generate_audio_speech(msg["content"])
                if audio_data:
                    with st.expander("🔊 Listen to this Advisory (Voice Playback)", expanded=False):
                        st.audio(audio_data, format="audio/mp3")

    # -----------------------------------------------------------------------
    # Interactive Input Options: Text Input & Voice Input
    # -----------------------------------------------------------------------
    st.markdown("---")
    
    input_tab_text, input_tab_voice = st.tabs(["💬 Text Question", "🎙️ Voice Question (Speak to Mitra)"])

    user_query = None

    with input_tab_voice:
        st.markdown("<small style='color: var(--text-sub);'>Tap the microphone to speak your question in English, Telugu, Hindi, or Kannada:</small>", unsafe_allow_html=True)
        audio_prompt = st.audio_input("Speak your question:")
        if audio_prompt is not None:
            with st.spinner("🎙️ Transcribing spoken query with Whisper Turbo..."):
                transcribed_text = transcribe_voice(audio_prompt.read(), filename="query.wav")
                if transcribed_text:
                    st.success(f"Transcribed: *\"{transcribed_text}\"*")
                    user_query = transcribed_text
                else:
                    st.warning("Could not clearly transcribe audio. Please try speaking closer to the microphone or use text input.")

    with input_tab_text:
        text_query = st.chat_input("Ask a question about crop diseases, sprays, irrigation, or weather stress...")
        if text_query:
            user_query = text_query

    if hasattr(st.session_state, "prompt_input") and st.session_state.prompt_input:
        user_query = st.session_state.prompt_input
        st.session_state.prompt_input = None

    if user_query:
        # Display user question
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Call RAG Pipeline with PROMPT 2 (Chat Mode)
        with st.chat_message("assistant"):
            with st.spinner("Consulting agricultural knowledge base..."):
                ml_out_val = 1 if risk_level in {"moderate", "high"} else 0
                readings_payload = {
                    "temperature_c": telemetry.get("temperature_c", 25.0),
                    "humidity_pct": telemetry.get("humidity_pct", 65.0),
                    "soil_moisture_pct": telemetry.get("soil_moisture_pct", 25.0),
                    "rainfall_mm": telemetry.get("rainfall_mm", 0.0),
                    "sunlight_wm2": telemetry.get("sunlight_wm2", 200.0),
                    "risk_pct": risk_pct,
                    "risk_level": risk_level,
                }

                clean_history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]
                    if not str(m.get("content", "")).startswith("Apologies, an error occurred")
                ]

                try:
                    # PROMPT 2: Conversational Chat Mode with Intent Clarification & Suggested Follow-Ups
                    answer, structured = rag_pipeline.answer(
                        readings=readings_payload,
                        ml_output=ml_out_val,
                        crop=farm["crop"],
                        location=farm["name"],
                        question=user_query,
                        chat_history=clean_history,
                        ml_prediction=pred_data,
                        existing_summary=st.session_state.get("conversation_summary", ""),
                        k_recent_turns=2,
                        mode="chat",
                    )
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    st.session_state.structured_advisory = structured
                    st.session_state.conversation_summary = getattr(rag_pipeline, "last_summary", "")

                    # Voice TTS Playback
                    audio_res = generate_audio_speech(answer)
                    if audio_res:
                        with st.expander("🔊 Listen to this Advisory (Voice Playback)", expanded=True):
                            st.audio(audio_res, format="audio/mp3")

                    # Export Advisory Option (Text)
                    st.download_button(
                        label="📥 Download Advisory Transcript",
                        data=answer,
                        file_name=f"sarva_mitra_{farm['crop']}_{datetime.now(IST).strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain",
                    )
                except Exception as err:
                    err_text = f"Apologies, an error occurred while generating advisory: {err}"
                    st.error(err_text)
