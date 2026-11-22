"""
Weather service integrating Open-Meteo API.
Fetches daily precipitation (rainfall_mm) and solar radiation (sunlight_wm2).
Features an in-memory TTL cache to eliminate redundant external calls.
"""

import logging
import httpx
from datetime import datetime, date, timezone
from typing import Dict, Any, Tuple

from config import settings

logger = logging.getLogger("smartfarm.weather")

# In-memory cache: (lat, lon, date) -> (data_dict, timestamp)
_weather_cache: Dict[Tuple[float, float, str], Tuple[Dict[str, Any], datetime]] = {}
CACHE_TTL_SECONDS = 3600  # 1 hour cache


async def fetch_weather(lat: float, lon: float, target_date: str) -> Dict[str, Any]:
    """
    Fetches daily rainfall (mm) and sunlight (W/m²) for a given location and date.
    Uses Open-Meteo Historical Archive API for past dates, or Forecast API for today/future.
    """
    cache_key = (round(lat, 2), round(lon, 2), target_date)
    now = datetime.now(timezone.utc)

    # Check cache
    if cache_key in _weather_cache:
        cached_data, cached_time = _weather_cache[cache_key]
        if (now - cached_time).total_seconds() < CACHE_TTL_SECONDS:
            logger.debug("Weather cache hit for %s", cache_key)
            return cached_data

    # Determine whether target_date is in past, today, or future
    target_dt = datetime.strptime(target_date, "%Y-%m-%d").date()
    today_dt = date.today()

    # If date is today or future, use forecast endpoint; if older, use archive endpoint
    if target_dt >= today_dt:
        url = settings.weather_forecast_url
    else:
        url = settings.weather_api_base_url

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": target_date,
        "end_date": target_date,
        "daily": ["precipitation_sum", "shortwave_radiation_sum"],
        "timezone": "auto"
    }

    logger.info("Fetching weather from %s for (%s, %s) on %s", url, lat, lon, target_date)

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        daily_data = data.get("daily", {})
        precip_list = daily_data.get("precipitation_sum", [])
        radiation_list = daily_data.get("shortwave_radiation_sum", [])

        # Extract rainfall (mm)
        rainfall_mm = float(precip_list[0]) if (precip_list and precip_list[0] is not None) else 0.0

        # Extract solar radiation: Open-Meteo returns shortwave_radiation_sum in MJ/m²/day
        # 1 MJ/m²/day = 1,000,000 Joules / 86,400 seconds = ~11.574 W/m² (24-hour mean flux)
        radiation_mj = float(radiation_list[0]) if (radiation_list and radiation_list[0] is not None) else 0.0
        sunlight_wm2 = round((radiation_mj * 1_000_000.0) / 86400.0, 2)

        result = {
            "date": target_date,
            "rainfall_mm": round(rainfall_mm, 2),
            "sunlight_wm2": sunlight_wm2,
            "source": "Open-Meteo",
            "is_cached": False
        }

        # Store in cache
        _weather_cache[cache_key] = (result, now)
        logger.info(
            "Weather fetched successfully for %s: rainfall=%.2f mm, sunlight=%.2f W/m²",
            target_date, rainfall_mm, sunlight_wm2
        )
        return result

    except httpx.HTTPStatusError as e:
        logger.error("Open-Meteo HTTP error (%s): %s", e.response.status_code, e.response.text)
        raise ValueError(f"Weather API returned HTTP status {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error("Open-Meteo connection failure: %s", str(e))
        raise ConnectionError(f"Failed to connect to Weather API: {str(e)}")
    except Exception as e:
        logger.error("Unexpected error parsing weather data: %s", str(e))
        raise ValueError(f"Could not parse weather response: {str(e)}")
