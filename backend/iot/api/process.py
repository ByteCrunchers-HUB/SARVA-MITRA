"""API-only farm workflow: geocode, fetch climate history, call ML, then RAG."""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

from config import settings
from schemas.rag_schema import ProcessRequest, ProcessResponse
from services.data_integration import build_ml_request
from services.history_service import to_rag_history
from services.location_service import geocode_place, match_trained_location
from services.ml_service import call_ml_engine, generate_mock_ml_response
from services.nasa_power_service import fetch_daily_history
from services.rag_service import build_rag_request, call_rag_pipeline, generate_mock_rag_response
from utils.validation import validate_date_format

logger = logging.getLogger("smartfarm.process")
router = APIRouter(prefix="/process", tags=["Process"])
IST = timezone(timedelta(hours=5, minutes=30))


@router.post("", response_model=ProcessResponse, summary="Run location-based ML and RAG analysis")
async def process_telemetry(payload: ProcessRequest):
    """Fetch real location-specific daily data, then call the ML and RAG APIs.

    Request coordinates can be supplied directly, or a place name can be geocoded.
    The ML model has static soil features only for its trained points, so the
    nearest supported point is used as the model reference location.
    """
    requested_lat = payload.latitude if payload.latitude is not None else payload.lat
    requested_lon = payload.longitude if payload.longitude is not None else payload.lon

    if (requested_lat is None) != (requested_lon is None):
        raise HTTPException(status_code=422, detail="Provide both latitude and longitude, or provide a location name.")

    if requested_lat is None and payload.location:
        try:
            geocoded = await geocode_place(payload.location)
        except (ValueError, ConnectionError) as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        requested_lat = geocoded["latitude"]
        requested_lon = geocoded["longitude"]
        location_name = ", ".join(part for part in (geocoded["name"], geocoded.get("admin1")) if part)
    elif requested_lat is None:
        requested_lat = settings.latitude
        requested_lon = settings.longitude
        location_name = payload.location or settings.location_name
    else:
        location_name = payload.location or f"{float(requested_lat):.4f}, {float(requested_lon):.4f}"

    try:
        model_location = await match_trained_location(float(requested_lat), float(requested_lon))
    except (ValueError, ConnectionError) as exc:
        raise HTTPException(status_code=422 if isinstance(exc, ValueError) else 502, detail=str(exc)) from exc

    target_date = payload.target_date or datetime.now(IST).date().isoformat()
    if not validate_date_format(target_date):
        raise HTTPException(status_code=400, detail=f"Invalid target_date: {target_date}. Expected YYYY-MM-DD.")

    target_day = date.fromisoformat(target_date)
    history_start = target_day - timedelta(days=7)
    history_end = target_day - timedelta(days=1)

    try:
        # Weather is requested at the selected farm coordinates, not the ML reference point.
        environment_history = await fetch_daily_history(
            lat=float(requested_lat),
            lon=float(requested_lon),
            start_date=history_start.isoformat(),
            end_date=history_end.isoformat(),
        )
    except (ValueError, ConnectionError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    device_id = payload.device_id or f"API_{float(requested_lat):.3f}_{float(requested_lon):.3f}"
    metadata: Dict[str, Any] = {
        "data_source": "NASA POWER Daily API",
        "location": location_name,
        "requested_coordinates": {"lat": float(requested_lat), "lon": float(requested_lon)},
        "ml_reference_coordinates": {"lat": model_location["lat"], "lon": model_location["lon"]},
        "distance_to_ml_reference_km": model_location["distance_km"],
        "ml_records_count": len(environment_history),
        "warnings": [],
    }
    if model_location["distance_km"] > 1:
        metadata["warnings"].append(
            "Static soil features and model location use the nearest trained point; "
            "weather values are fetched for the requested coordinates."
        )

    ml_request = build_ml_request(
        device_id=device_id,
        lat=model_location["lat"],
        lon=model_location["lon"],
        target_date=target_date,
        history_records=environment_history,
        current_reading=None,
    )

    if payload.use_stub_ml:
        ml_response = generate_mock_ml_response(
            device_id, target_date, model_location["lat"], model_location["lon"]
        )
        metadata["ml_mode"] = "stub_flag"
    else:
        try:
            ml_response = await call_ml_engine(ml_request)
            metadata["ml_mode"] = "live_service"
        except (ConnectionError, TimeoutError, ValueError) as exc:
            logger.exception("ML request failed")
            raise HTTPException(status_code=502, detail=f"ML service request failed: {exc}") from exc

    latest_environment = environment_history[-1].model_dump()
    weather_context = {
        "date": latest_environment["date"],
        "rainfall_mm": latest_environment["rainfall_mm"],
        "sunlight_wm2": latest_environment["sunlight_wm2"],
        "source": "NASA POWER",
    }
    rag_history = to_rag_history(environment_history)
    rag_request = build_rag_request(
        device_id=device_id,
        lat=float(requested_lat),
        lon=float(requested_lon),
        target_date=target_date,
        sensor_data=None,
        weather_data=weather_context,
        ml_response=ml_response,
        history_records=rag_history,
        crop=payload.crop,
        question=payload.question,
        location_name=location_name,
    )

    if payload.use_stub_rag:
        risk_label = ml_response.get("prediction", {}).get("risk_label", "moderate")
        rag_response = generate_mock_rag_response(device_id, risk_label)
        metadata["rag_mode"] = "stub_flag"
    else:
        try:
            rag_response = await call_rag_pipeline(rag_request)
            metadata["rag_mode"] = "live_service"
        except (ConnectionError, TimeoutError, ValueError) as exc:
            logger.exception("RAG request failed")
            raise HTTPException(status_code=502, detail=f"RAG service request failed: {exc}") from exc

    metadata["completed_at"] = datetime.now(timezone.utc).isoformat()
    return ProcessResponse(
        device_id=device_id,
        target_date=target_date,
        status="success",
        sensor_data=None,
        environment_history=[record.model_dump() for record in environment_history],
        weather_data=weather_context,
        ml_response=ml_response,
        rag_response=rag_response,
        metadata=metadata,
    )
