"""
Data integration service.
Combines hardware sensor readings with external weather data,
and formats the exact JSON payload required by the ML Engine.
"""

import logging
from typing import Dict, Any, List
from config import settings
from schemas.ml_schema import MLRequest, MLHistoryRecord

logger = logging.getLogger("smartfarm.integration")


def build_ml_request(
    device_id: str,
    location_name: str,
    lat: float,
    lon: float,
    target_date: str,
    history_records: List[MLHistoryRecord]
) -> MLRequest:
    """
    Constructs and validates the exact ML request structure.
    Strictly asserts exactly 8 records in history.
    """
    if len(history_records) != 8:
        raise ValueError(f"ML Engine requires exactly 8 history records, but got {len(history_records)}")

    payload = MLRequest(
        device_id=device_id,
        location=location_name,
        lat=lat,
        lon=lon,
        target_date=target_date,
        history=history_records
    )

    logger.debug("Constructed ML Request for device %s, target_date %s", device_id, target_date)
    return payload


def merge_sensor_and_weather(sensor_data: Dict[str, Any], weather_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges live ESP32 readings with external weather conditions for storage and RAG context.
    """
    return {
        "temperature": sensor_data.get("temperature"),
        "humidity": sensor_data.get("humidity"),
        "soil_moisture": sensor_data.get("soil_moisture"),
        "rainfall_mm": weather_data.get("rainfall_mm", 0.0),
        "sunlight_wm2": weather_data.get("sunlight_wm2", 0.0),
        "timestamp": sensor_data.get("timestamp"),
        "weather_date": weather_data.get("date")
    }
