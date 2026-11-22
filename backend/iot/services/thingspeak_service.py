"""Fetch the most recent ESP32 reading from ThingSpeak."""

import logging
import time
from typing import Any, Dict, Optional

import httpx

from config import settings
from schemas.sensor_schema import ESP32SensorReading
from utils.validation import validate_sensor_ranges

logger = logging.getLogger("smartfarm.thingspeak")

_cached_reading: Optional[Dict[str, Any]] = None
_last_fetch_at = 0.0


async def fetch_latest_reading() -> Optional[Dict[str, Any]]:
    """Fetch and validate ThingSpeak's latest channel entry, with a short cache."""
    global _cached_reading, _last_fetch_at

    channel_id = settings.thingspeak_channel_id.strip()
    if not channel_id:
        return None

    now = time.monotonic()
    cache_seconds = max(1, settings.thingspeak_read_cache_seconds)
    if now - _last_fetch_at < cache_seconds:
        return _cached_reading.copy() if _cached_reading else None
    _last_fetch_at = now

    url = f"https://api.thingspeak.com/channels/{channel_id}/feeds/last.json"
    params = {}
    if settings.thingspeak_read_api_key.strip():
        params["api_key"] = settings.thingspeak_read_api_key.strip()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            feed = response.json()

        if not isinstance(feed, dict):
            logger.warning("ThingSpeak returned no feed object for channel %s", channel_id)
            return _cached_reading.copy() if _cached_reading else None

        temperature = feed.get("field1")
        humidity = feed.get("field2")
        soil_moisture = feed.get("field3")
        if temperature is None or humidity is None or soil_moisture is None:
            return _cached_reading.copy() if _cached_reading else None

        parsed = ESP32SensorReading(
            device_id=settings.device_id,
            temperature=float(temperature),
            humidity=float(humidity),
            soil_moisture=float(soil_moisture),
            timestamp=feed.get("created_at"),
        )
        valid, errors = validate_sensor_ranges(
            parsed.temperature, parsed.humidity, parsed.soil_moisture
        )
        if not valid:
            logger.warning("ThingSpeak reading failed range validation: %s", errors)
            return _cached_reading.copy() if _cached_reading else None

        _cached_reading = parsed.model_dump()
        return _cached_reading.copy()
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        logger.warning("Unable to fetch a valid ThingSpeak reading: %s", exc)
        return _cached_reading.copy() if _cached_reading else None
