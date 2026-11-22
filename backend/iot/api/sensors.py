"""
Sensor telemetry endpoints for reading live ESP32 hardware values.
"""

from fastapi import APIRouter, Request, HTTPException
from config import settings
from schemas.sensor_schema import ESP32SensorReading
from utils.validation import validate_sensor_ranges

router = APIRouter(prefix="/sensors", tags=["Sensors"])


@router.get("/latest", summary="Get latest ESP32 sensor telemetry")
async def get_latest_sensors(request: Request):
    """
    Returns the most recent air temperature, air humidity, and soil moisture
    readings captured over USB Serial from the ESP32.
    """
    receiver = getattr(request.app.state, "serial_receiver", None)
    if not receiver:
        raise HTTPException(status_code=500, detail="Serial receiver service is not initialized.")

    reading = await receiver.get_latest_reading()
    if not reading:
        raise HTTPException(
            status_code=503,
            detail=(
                f"No sensor readings currently available on port {settings.serial_port}. "
                "Ensure ESP32 is powered, transmitting JSON, and connected."
            )
        )

    return {
        "status": "success",
        "data": reading,
        "is_serial_connected": receiver.is_connected()
    }


@router.get("/status", summary="Check serial communication link status")
async def get_serial_status(request: Request):
    """
    Returns the operational status of the PySerial link.
    """
    receiver = getattr(request.app.state, "serial_receiver", None)
    is_connected = receiver.is_connected() if receiver else False
    latest = await receiver.get_latest_reading() if receiver else None

    return {
        "serial_port": settings.serial_port,
        "baudrate": settings.serial_baudrate,
        "connected": is_connected,
        "has_cached_reading": latest is not None
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
