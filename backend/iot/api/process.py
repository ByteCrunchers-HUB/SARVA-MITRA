"""
Central orchestration endpoint (POST /api/process).
Coordinates the full lifecycle:
ESP32 -> Serial -> Weather -> Database -> History -> ML Engine -> RAG Advisory -> Frontend
"""

import logging
from datetime import date, datetime, timezone
from fastapi import APIRouter, Request, HTTPException

from config import settings
from database.sensor_repository import upsert_daily_record
from schemas.ml_schema import MLCurrentReading
from schemas.rag_schema import ProcessRequest, ProcessResponse
from services.data_integration import build_ml_request, merge_sensor_and_weather
from services.history_service import prepare_ml_history, to_rag_history
from services.ml_service import call_ml_engine, generate_mock_ml_response
from services.rag_service import build_rag_request, call_rag_pipeline, generate_mock_rag_response
from utils.validation import validate_date_format

logger = logging.getLogger("smartfarm.process")

router = APIRouter(prefix="/process", tags=["Process"])


@router.post("", response_model=ProcessResponse, summary="Execute complete end-to-end integration workflow")
async def process_telemetry(payload: ProcessRequest, request: Request):
    """
    Main integration pipeline:
    1. Read latest ESP32 sensor telemetry from PySerial receiver.
    2. Read coordinates from UI (defaults to Vijayawada: lat=16.51, lon=80.52).
    3. Fetch environmental weather parameters from Open-Meteo for the location.
    4. Persist daily combined record in SQLite.
    5. Compile consecutive daily history records.
    6. Construct ML request and call ML Engine API (POST /predict).
    7. Forward combined context + prediction to RAG Advisory API (POST /advisory).
    8. Deliver the unified result to the frontend.
    """
    device_id = payload.device_id or settings.device_id
    target_date = payload.target_date or date.today().strftime("%Y-%m-%d")

    # Resolve latitude & longitude: provided by UI, or default to Vijayawada
    resolved_lat = payload.latitude if payload.latitude is not None else (
        payload.lat if payload.lat is not None else settings.latitude
    )
    resolved_lon = payload.longitude if payload.longitude is not None else (
        payload.lon if payload.lon is not None else settings.longitude
    )
    resolved_location = payload.location or settings.location_name

    if not validate_date_format(target_date):
        raise HTTPException(status_code=400, detail=f"Invalid target_date format: {target_date}. Expected YYYY-MM-DD.")

    logger.info(
        "--- Starting Processing for Device: %s, Date: %s, Location: %s (%.2f, %.2f) ---",
        device_id, target_date, resolved_location, resolved_lat, resolved_lon
    )
    metadata = {
        "initiated_at": datetime.now(timezone.utc).isoformat(),
        "device_id": device_id,
        "target_date": target_date,
        "location": resolved_location,
        "latitude": resolved_lat,
        "longitude": resolved_lon,
        "crop": payload.crop,
        "warnings": []
    }

    # --------------------------------------------------------------------------
    # Step 1: Read Latest ESP32 Hardware Readings
    # --------------------------------------------------------------------------
    receiver = getattr(request.app.state, "serial_receiver", None)
    sensor_data = None
    if receiver:
        sensor_data = await receiver.get_latest_reading()

    if not sensor_data:
        warning_msg = f"ESP32 hardware telemetry unavailable on {settings.serial_port}. Proceeding with fallback/weather data."
        logger.warning(warning_msg)
        metadata["warnings"].append(warning_msg)

    # --------------------------------------------------------------------------
    # Step 2: Fetch External Weather Information (Open-Meteo)
    # --------------------------------------------------------------------------
    from services.weather_service import fetch_weather
    try:
        weather_data = await fetch_weather(
            lat=resolved_lat,
            lon=resolved_lon,
            target_date=target_date
        )
    except Exception as w_err:
        logger.error("Weather service unavailable: %s", w_err)
        metadata["warnings"].append(f"Weather API error: {str(w_err)}")
        weather_data = {
            "date": target_date,
            "rainfall_mm": 0.0,
            "sunlight_wm2": 0.0,
            "source": "Unavailable"
        }

    # --------------------------------------------------------------------------
    # Step 3: Persist Today's Snapshot into Database
    # --------------------------------------------------------------------------
    rainfall_val = weather_data.get("rainfall_mm", 0.0)
    sunlight_val = weather_data.get("sunlight_wm2", 0.0)
    leaf_wet = 1 if rainfall_val > 0.0 else 0

    await upsert_daily_record(
        device_id=device_id,
        date=target_date,
        temperature=sensor_data.get("temperature") if sensor_data else 28.0,
        humidity=sensor_data.get("humidity") if sensor_data else 60.0,
        soil_moisture=sensor_data.get("soil_moisture") if sensor_data else 45.0,
        rainfall_mm=rainfall_val,
        sunlight_wm2=sunlight_val,
        leaf_wet_days=leaf_wet,
        is_duplicated=False
    )

    # --------------------------------------------------------------------------
    # Step 4: Prepare History Records
    # --------------------------------------------------------------------------
    try:
        ml_history = await prepare_ml_history(device_id=device_id, target_date=target_date)
    except ValueError as hist_err:
        logger.error("History preparation failed: %s", hist_err)
        raise HTTPException(status_code=422, detail=str(hist_err))

    metadata["ml_records_count"] = len(ml_history)

    # Current sensed reading for ML engine (optional)
    curr_reading = None
    if sensor_data:
        curr_reading = MLCurrentReading(
            date=target_date,
            soil_moisture_pct=float(sensor_data.get("soil_moisture", 45.0)),
            air_temperature_c=float(sensor_data.get("temperature", 28.0)),
            humidity_pct=float(sensor_data.get("humidity", 60.0)),
            sunlight_wm2=sunlight_val,
            rainfall_mm=rainfall_val
        )

    # --------------------------------------------------------------------------
    # Step 5: Construct and Send ML Request
    # --------------------------------------------------------------------------
    ml_request_obj = build_ml_request(
        device_id=device_id,
        lat=resolved_lat,
        lon=resolved_lon,
        target_date=target_date,
        history_records=ml_history,
        current_reading=curr_reading
    )

    ml_response_data = None
    if payload.use_stub_ml:
        logger.info("Using mock ML Engine response per request flag.")
        ml_response_data = generate_mock_ml_response(device_id, target_date)
        metadata["ml_mode"] = "stub_flag"
    else:
        try:
            ml_response_data = await call_ml_engine(ml_request_obj)
            metadata["ml_mode"] = "live_service"
        except (ConnectionError, TimeoutError, ValueError) as ml_err:
            logger.warning("ML API request failed (%s). Falling back to mock stub for testing.", ml_err)
            ml_response_data = generate_mock_ml_response(device_id, target_date)
            metadata["ml_mode"] = "fallback_stub"
            metadata["warnings"].append(f"ML Engine API unavailable: {str(ml_err)}")

    # --------------------------------------------------------------------------
    # Step 6 & 7: Construct Combined Payload & Call RAG Advisory API
    # --------------------------------------------------------------------------
    rag_history = to_rag_history(ml_history)
    rag_request_obj = build_rag_request(
        device_id=device_id,
        lat=resolved_lat,
        lon=resolved_lon,
        target_date=target_date,
        sensor_data=sensor_data,
        weather_data=weather_data,
        ml_response=ml_response_data,
        history_records=rag_history,
        crop=payload.crop,
        question=payload.question
    )

    rag_response_data = None
    risk_label = ml_response_data.get("prediction", {}).get("risk_label", "moderate")

    if payload.use_stub_rag:
        logger.info("Using mock RAG Pipeline response per request flag.")
        rag_response_data = generate_mock_rag_response(device_id, risk_label)
        metadata["rag_mode"] = "stub_flag"
    else:
        try:
            rag_response_data = await call_rag_pipeline(rag_request_obj)
            metadata["rag_mode"] = "live_service"
        except (ConnectionError, TimeoutError, ValueError) as rag_err:
            logger.warning("RAG API request failed (%s). Falling back to mock stub for testing.", rag_err)
            rag_response_data = generate_mock_rag_response(device_id, risk_label)
            metadata["rag_mode"] = "fallback_stub"
            metadata["warnings"].append(f"RAG Pipeline API unavailable: {str(rag_err)}")

    metadata["completed_at"] = datetime.now(timezone.utc).isoformat()

    # --------------------------------------------------------------------------
    # Step 8: Return Unified Payload to Client
    # --------------------------------------------------------------------------
    logger.info("--- End-to-End Processing Completed Successfully ---")
    return ProcessResponse(
        device_id=device_id,
        target_date=target_date,
        status="success",
        sensor_data=sensor_data,
        weather_data=weather_data,
        ml_response=ml_response_data,
        rag_response=rag_response_data,
        metadata=metadata
    )
