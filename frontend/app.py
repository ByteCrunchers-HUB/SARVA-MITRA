"""Sarva Mitra - Interactive Streamlit UI.

Flow:
1. Entry Screen: Farmer selects city coordinates (preset or custom) and crop.
2. Immediate Pipeline Execution: Fetches Telemetry -> Runs ML Risk Model -> Generates initial RAG Advisory.
3. Live Dashboard & Continuous Chat: Displays telemetry cards, ML risk, and proactive advice in the chat with follow-up Q&A.

Run:
    streamlit run frontend/app.py
"""
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

IST = timezone(timedelta(hours=5, minutes=30))

LOCATIONS = {
    "Vijayawada (Andhra Pradesh)": {"lat": 16.51, "lon": 80.52, "name": "Vijayawada"},
    "Bengaluru (Karnataka)": {"lat": 12.97, "lon": 77.59, "name": "Bengaluru"},
    "Guntur (Andhra Pradesh)": {"lat": 16.30, "lon": 80.44, "name": "Guntur"},
    "Kurnool (Andhra Pradesh)": {"lat": 15.82, "lon": 78.03, "name": "Kurnool"},
    "Anantapur (Andhra Pradesh)": {"lat": 14.68, "lon": 77.60, "name": "Anantapur"},
    "Hyderabad (Telangana)": {"lat": 17.39, "lon": 78.49, "name": "Hyderabad"},
    "Enter Custom Coordinates": {"lat": 16.51, "lon": 80.52, "name": "Custom Farm"},
}

CROPS = {
    "Tomato 🍅": "tomato",
    "Chilli 🌶️": "chilli",
    "Ragi (Finger Millet) 🌾": "ragi",
}

st.set_page_config(
    page_title="Sarva Mitra — Universal Farm Companion",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Lazy Load Backend Modules
# ---------------------------------------------------------------------------
@st.cache_resource
def get_services():
    from backend.telemetry_service.service import telemetry_service
    from backend.ml_engine.backend import load_bundle, run_prediction, PredictRequest
    from backend.rag_pipeline.rag import RAGPipeline
    bundle = load_bundle()
    rag = RAGPipeline()
    return telemetry_service, bundle, run_prediction, PredictRequest, rag

try:
    telemetry_service, ml_bundle, run_prediction, PredictRequest, rag_pipeline = get_services()
    backend_ready = True
except Exception as exc:
    backend_ready = False
    init_error = exc


# ---------------------------------------------------------------------------
# Session State
# ---------------------------------------------------------------------------
if "monitoring_active" not in st.session_state:
    st.session_state.monitoring_active = False

if "messages" not in st.session_state:
    st.session_state.messages = []

if "telemetry" not in st.session_state:
    st.session_state.telemetry = None

if "ml_prediction" not in st.session_state:
    st.session_state.ml_prediction = None

if "structured_advisory" not in st.session_state:
    st.session_state.structured_advisory = None

if "farm_config" not in st.session_state:
    st.session_state.farm_config = {"lat": 16.51, "lon": 80.52, "name": "Vijayawada", "crop": "tomato"}


def run_full_pipeline(lat: float, lon: float, loc_name: str, crop_name: str):
    """Executes Telemetry -> ML Engine -> RAG Pipeline and sets initial advisory in chat."""
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
    prediction = run_prediction(ml_req, ml_bundle)
    risk_info = prediction.get("prediction", {})
    risk_level = risk_info.get("risk_level", "low")
    risk_pct = risk_info.get("risk_pct", 0.0)
    ml_out = 1 if risk_level in {"moderate", "high"} else 0

    # 3. Formulate proactive RAG Advisory
    initial_query = f"Provide a complete agronomic status assessment and recommendations for {crop_name} based on current field conditions."
    rag_readings = {
        "temperature_c": readings.get("temperature_c", 25.0),
        "humidity_pct": readings.get("humidity_pct", 65.0),
        "soil_moisture_pct": readings.get("soil_moisture_pct", 25.0),
        "rainfall_mm": readings.get("rainfall_mm", 0.0),
        "sunlight_wm2": readings.get("sunlight_wm2", 200.0),
        "risk_pct": risk_pct,
        "risk_level": risk_level,
    }

    answer, structured = rag_pipeline.answer(
        readings=rag_readings,
        ml_output=ml_out,
        crop=crop_name,
        location=loc_name,
        question=initial_query,
        chat_history=[],
        ml_prediction=prediction,
    )

    # Store state
    st.session_state.telemetry = readings
    st.session_state.ml_prediction = prediction
    st.session_state.structured_advisory = structured
    st.session_state.farm_config = {"lat": lat, "lon": lon, "name": loc_name, "crop": crop_name}
    st.session_state.monitoring_active = True

    # Initial chat message from AI companion
    intro_prefix = (
        f"👋 **Namaste! I have analyzed the live telemetry for your {crop_name.title()} crop in {loc_name}.**\n\n"
        f"- 🌡️ **Temperature:** {readings.get('temperature_c', 0.0):.1f} °C\n"
        f"- 💧 **Relative Humidity:** {readings.get('humidity_pct', 0.0):.1f} %\n"
        f"- 🌱 **Soil Moisture:** {readings.get('soil_moisture_pct', 0.0):.1f} %\n"
        f"- 🧠 **ML Weather Risk:** {risk_pct}% ({risk_level.title()})\n\n"
        f"---\n\n"
    )
    st.session_state.messages = [
        {"role": "assistant", "content": intro_prefix + answer}
    ]


# ---------------------------------------------------------------------------
# SCREEN 1: ENTRY / LOCATION SELECTION
# ---------------------------------------------------------------------------
if not st.session_state.monitoring_active:
    st.markdown("<h1 style='text-align: center;'>🌱 Sarva Mitra — Universal Farm Companion</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Autonomous farm telemetry, AI weather-risk forecasting, and personalized agronomic guidance.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        st.subheader("📍 Setup Your Farm")
        
        city_selection = st.selectbox("Select Your City / Region:", list(LOCATIONS.keys()), index=0)
        selected_preset = LOCATIONS[city_selection]

        if city_selection == "Enter Custom Coordinates":
            c_lat, c_lon = st.columns(2)
            input_lat = c_lat.number_input("Latitude", value=16.51, format="%.4f")
            input_lon = c_lon.number_input("Longitude", value=80.52, format="%.4f")
            input_name = st.text_input("Farm / Village Name", value="My Farm")
        else:
            input_lat = selected_preset["lat"]
            input_lon = selected_preset["lon"]
            input_name = selected_preset["name"]
            st.info(f"Coordinates: **Latitude {input_lat}**, **Longitude {input_lon}**")

        crop_label = st.selectbox("Select Your Crop:", list(CROPS.keys()), index=0)
        chosen_crop = CROPS[crop_label]

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Fetch Telemetry & Start Monitoring", type="primary", use_container_width=True):
            if not backend_ready:
                st.error(f"Cannot initialize services: {init_error}")
            else:
                status_container = st.status("📡 Initializing Farm Monitoring...", expanded=True)
                with status_container:
                    st.write("🛰️ Fetching real-time virtual telemetry from meteorological & soil APIs...")
                    time.sleep(0.3)
                    st.write("🧠 Computing 8-day history & running ML Risk Prediction model...")
                    time.sleep(0.3)
                    st.write("📚 Querying RAG vector knowledge base & synthesizing proactive advisory...")
                    run_full_pipeline(input_lat, input_lon, input_name, chosen_crop)
                    status_container.update(label="✅ Monitoring Active!", state="complete", expanded=False)
                st.rerun()

    st.stop()


# ---------------------------------------------------------------------------
# SCREEN 2: ACTIVE DASHBOARD & CONTINUOUS CHAT
# ---------------------------------------------------------------------------

farm = st.session_state.farm_config
telemetry = st.session_state.telemetry
pred = st.session_state.ml_prediction.get("prediction", {}) if st.session_state.ml_prediction else {}
risk_level = pred.get("risk_level", "low")
risk_pct = pred.get("risk_pct", 0.0)

# Sidebar with Farm Info & Actions
with st.sidebar:
    st.title("🌾 Active Farm")
    st.write(f"**Location:** {farm['name']}")
    st.write(f"**Coordinates:** `{farm['lat']}, {farm['lon']}`")
    st.write(f"**Crop:** {farm['crop'].title()}")
    st.markdown("---")

    risk_badge = "🟢 LOW RISK" if risk_level == "low" else ("🟡 MODERATE RISK" if risk_level == "moderate" else "🔴 HIGH RISK")
    st.markdown(f"**ML Environmental Risk:**\n### {risk_badge} ({risk_pct}%)")
    st.caption(f"Telemetry Source: **{telemetry.get('source', 'WeatherAPI / Open-Meteo')}**")

    st.markdown("---")
    if st.button("🔄 Refresh Telemetry", use_container_width=True):
        with st.spinner("Updating telemetry & risk analysis..."):
            run_full_pipeline(farm["lat"], farm["lon"], farm["name"], farm["crop"])
            st.success("Telemetry refreshed!")
            st.rerun()

    if st.button("📍 Change Location / Crop", use_container_width=True):
        st.session_state.monitoring_active = False
        st.session_state.messages = []
        st.rerun()

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# Main Dashboard Header
st.title(f"🌱 Sarva Mitra — {farm['crop'].title()} Farm Monitor")
st.caption(f"Real-time Telemetry & AI Advisory for **{farm['name']}** | Lat: `{farm['lat']}`, Lon: `{farm['lon']}`")

# 1. Telemetry Metrics Cards
if telemetry:
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🌡️ Air Temperature", f"{telemetry.get('temperature_c', 0.0):.1f} °C")
    m2.metric("💧 Relative Humidity", f"{telemetry.get('humidity_pct', 0.0):.1f} %")
    m3.metric("🌱 Soil Moisture", f"{telemetry.get('soil_moisture_pct', 0.0):.1f} %")
    m4.metric("🌧️ Rainfall Today", f"{telemetry.get('rainfall_mm', 0.0):.1f} mm")
    m5.metric("☀️ Solar Radiation", f"{telemetry.get('sunlight_wm2', 0.0):.0f} W/m²")

# 2. Risk Alert Banner
if risk_level == "high":
    st.error(f"⚠️ **High Environmental Stress Risk ({risk_pct}%)**: Weather and soil conditions heavily favor fungal pathogens or pest multiplication. Immediate field inspection recommended.")
elif risk_level == "moderate":
    st.warning(f"⚡ **Moderate Environmental Stress Risk ({risk_pct}%)**: Monitor soil moisture saturation and leaf wetness carefully.")
else:
    st.info(f"✅ **Optimal Field Conditions ({risk_pct}% Low Risk)**: Soil moisture and meteorological metrics are within safe operational bands.")

# Structured Action Items Expander
struct = st.session_state.structured_advisory
if struct and isinstance(struct, dict) and any(struct.values()):
    with st.expander("📋 Current Action Plan & Field Guidance", expanded=False):
        c_act1, c_act2 = st.columns(2)
        if struct.get("diagnosis"):
            c_act1.write(f"**Primary Focus:** {struct['diagnosis']}")
        if struct.get("irrigation"):
            c_act2.write(f"**Irrigation Advice:** {struct['irrigation']}")
        if struct.get("action_items"):
            st.write("**Field Action Steps:**")
            for item in struct["action_items"]:
                st.write(f"- {item}")
        if struct.get("chemical_control"):
            st.write(f"**Plant Protection:** {struct['chemical_control']}")

st.markdown("---")

# 3. Continuous Chat Section
st.subheader("💬 Ask Your Farm Companion")
st.caption("Ask questions about irrigation schedules, pest/disease prevention, fertilizers, or current sensor readings.")

# Quick Prompt Helper Pills
q1, q2, q3 = st.columns(3)
if q1.button("💧 Should I irrigate today based on soil moisture?", use_container_width=True):
    st.session_state.prompt_input = "Should I irrigate today based on my current soil moisture and weather?"
if q2.button("🔍 What specific diseases should I inspect for?", use_container_width=True):
    st.session_state.prompt_input = "What specific diseases or pests should I inspect for given current temperature and humidity?"
if q3.button("🍂 How to prevent flower drop and yellow leaves?", use_container_width=True):
    st.session_state.prompt_input = "How can I prevent flower drop and yellowing leaves under these conditions?"

# Render conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Chat Input
user_query = st.chat_input("Type your question in English, Hindi, or Telugu...")

if hasattr(st.session_state, "prompt_input") and st.session_state.prompt_input:
    user_query = st.session_state.prompt_input
    st.session_state.prompt_input = None

if user_query:
    # 1. Render user message
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # 2. Query RAG with continuous chat history and live telemetry
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

            chat_history_list = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[:-1]
            ]

            try:
                answer, structured = rag_pipeline.answer(
                    readings=readings_payload,
                    ml_output=ml_out_val,
                    crop=farm["crop"],
                    location=farm["name"],
                    question=user_query,
                    chat_history=chat_history_list,
                    ml_prediction=st.session_state.ml_prediction,
                )
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as err:
                err_text = f"Apologies, an error occurred while processing: {err}"
                st.error(err_text)
                st.session_state.messages.append({"role": "assistant", "content": err_text})
