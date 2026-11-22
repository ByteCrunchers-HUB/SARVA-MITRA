"""
Sensor telemetry endpoints for reading live ESP32 hardware values.
Supports both USB Serial ingestion and HTTP POST ingestion for cloud deployments.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException
from config import settings
from schemas.sensor_schema import ESP32SensorReading
from services.thingspeak_service import fetch_latest_reading as fetch_thingspeak_reading
from utils.validation import validate_sensor_ranges

router = APIRouter(prefix="/sensors", tags=["Sensors"])


@router.get("/latest", summary="Get latest ESP32 sensor telemetry from local receiver or ThingSpeak")
async def get_latest_sensors(request: Request):
    """
    Returns the most recent air temperature, air humidity, and soil moisture
    readings captured over USB Serial or HTTP ingestion from the ESP32.
    """
    receiver = getattr(request.app.state, "serial_receiver", None)
    if not receiver:
        raise HTTPException(status_code=500, detail="Serial receiver service is not initialized.")

    reading = await receiver.get_latest_reading()
    source = "local_serial_or_http"
    if not reading:
        reading = await fetch_thingspeak_reading()
        source = "thingspeak"
    if not reading:
        raise HTTPException(
            status_code=503,
            detail=(
                f"No sensor readings currently cached. "
                "Ensure ESP32 is transmitting over Serial or sending telemetry via POST /api/sensors/data."
            )
        )

    return {
        "status": "success",
        "data": reading,
        "is_serial_connected": receiver.is_connected(),
        "source": source
    }


@router.post("/data", summary="Ingest live sensor telemetry via HTTP (for ESP32 WiFi or serial forwarder)")
async def ingest_sensor_data(reading: ESP32SensorReading, request: Request):
    """
    HTTP Ingestion Endpoint:
    Allows an ESP32 connected to WiFi or a local serial forwarder running on a laptop
    to push live sensor telemetry directly to the cloud backend (Render).
    """
    valid, errors = validate_sensor_ranges(reading.temperature, reading.humidity, reading.soil_moisture)
    if not valid:
        raise HTTPException(status_code=400, detail=f"Validation failed: {errors}")

    reading_dict = {
        "device_id": reading.device_id,
        "temperature": reading.temperature,
        "humidity": reading.humidity,
        "soil_moisture": reading.soil_moisture,
        "timestamp": reading.timestamp or datetime.now(timezone.utc).isoformat()
    }

    receiver = getattr(request.app.state, "serial_receiver", None)
    if receiver:
        await receiver.update_reading(reading_dict)

    return {
        "status": "success",
        "message": "Telemetry received and cached",
        "data": reading_dict
    }


@router.get("/status", summary="Check serial communication link status")
async def get_serial_status(request: Request):
    """
    Returns the operational status of the PySerial link.
    """
    receiver = getattr(request.app.state, "serial_receiver", None)
    is_connected = receiver.is_connected() if receiver else False
    latest = await receiver.get_latest_reading() if receiver else None
    if not latest:
        latest = await fetch_thingspeak_reading()

    return {
        "serial_enabled": settings.enable_serial,
        "serial_port": settings.serial_port,
        "baudrate": settings.serial_baudrate,
        "connected": is_connected,
        "has_cached_reading": latest is not None,
        "thingspeak_configured": bool(settings.thingspeak_channel_id.strip())
    }


@router.post("/simulate", summary="Inject simulated sensor reading (testing utility)")
async def simulate_reading(reading: ESP32SensorReading, request: Request):
    """
    Testing endpoint: Injects a validated sensor reading directly into the memory cache.
    Useful during testing when ESP32 hardware is not physically connected.
    """
    valid, errors = validate_sensor_ranges(reading.temperature, reading.humidity, reading.soil_moisture)
    if not valid:
        raise HTTPException(status_code=400, detail=f"Validation failed: {errors}")

    receiver = getattr(request.app.state, "serial_receiver", None)
    if receiver:
        await receiver.set_reading_for_testing(reading.model_dump())

    return {
        "status": "simulated_reading_accepted",
        "reading": reading.model_dump()
    }
