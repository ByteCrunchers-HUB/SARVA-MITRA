"""Fetch daily, location-specific agrometeorology from NASA POWER."""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

import httpx

from config import settings
from schemas.ml_schema import MLDayRecord

logger = logging.getLogger("smartfarm.nasa_power")

PARAMETERS = "T2M,RH2M,ALLSKY_SFC_SW_DWN,PRECTOTCORR,GWETTOP"
_cache: Dict[Tuple[float, float, str, str], Tuple[List[Dict[str, Any]], datetime]] = {}


async def fetch_daily_history(
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
) -> List[MLDayRecord]:
    """Return complete daily ML records for an inclusive date range.

    NASA POWER daily values match the data source used to build this project's
    training data. GWETTOP is a 0..1 surface wetness fraction, converted to %;
    daily solar energy is converted from MJ/m²/day to mean W/m².
    """
    cache_key = (round(lat, 3), round(lon, 3), start_date, end_date)
    now = datetime.now(timezone.utc)
    cached = _cache.get(cache_key)
    if cached and (now - cached[1]).total_seconds() < settings.external_data_cache_seconds:
        return [MLDayRecord(**row) for row in cached[0]]

    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if end < start:
        raise ValueError("end_date must be on or after start_date")

    params = {
        "parameters": PARAMETERS,
        "community": "AG",
        "longitude": lat_lon_text(lon),
        "latitude": lat_lon_text(lat),
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
        "time-standard": "UTC",
    }
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            response = await client.get(settings.nasa_power_daily_url, params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        logger.error("NASA POWER returned %s: %s", exc.response.status_code, exc.response.text[:300])
        raise ConnectionError(f"NASA POWER returned HTTP {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        logger.error("NASA POWER request failed: %s", exc)
        raise ConnectionError("Could not fetch daily data from NASA POWER") from exc

    try:
        raw = payload["properties"]["parameter"]
        values_by_date = {
            "air_temperature_c": raw["T2M"],
            "humidity_pct": raw["RH2M"],
            "sunlight_mj_m2_day": raw["ALLSKY_SFC_SW_DWN"],
            "rainfall_mm": raw["PRECTOTCORR"],
            "soil_wetness_fraction": raw["GWETTOP"],
        }
    except (KeyError, TypeError) as exc:
        raise ValueError("NASA POWER response is missing required daily parameters") from exc

    records: List[Dict[str, Any]] = []
    current = start
    while current <= end:
        day = current.strftime("%Y%m%d")
        try:
            temp = _valid_number(values_by_date["air_temperature_c"].get(day))
            humidity = _valid_number(values_by_date["humidity_pct"].get(day))
            solar_mj = _valid_number(values_by_date["sunlight_mj_m2_day"].get(day))
            rain = _valid_number(values_by_date["rainfall_mm"].get(day))
            wetness = _valid_number(values_by_date["soil_wetness_fraction"].get(day))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"NASA POWER has incomplete data for {current.isoformat()}") from exc

        # The ML model expects a percentage; POWER reports GWETTOP as a fraction.
        soil_moisture_pct = wetness * 100.0 if wetness <= 1.0 else wetness
        record = {
            "date": current.isoformat(),
            "soil_moisture_pct": round(soil_moisture_pct, 2),
            "air_temperature_c": round(temp, 2),
            "humidity_pct": round(humidity, 2),
            "sunlight_wm2": round(solar_mj * 1_000_000.0 / 86400.0, 2),
            "rainfall_mm": round(rain, 2),
        }
        records.append(record)
        current += timedelta(days=1)

    if len(records) < 7:
        raise ValueError(f"NASA POWER returned {len(records)} days; the ML model requires at least 7")

    _cache[cache_key] = (records, now)
    return [MLDayRecord(**row) for row in records]


def _valid_number(value: Any) -> float:
    """Parse POWER values and reject its -999 missing-data sentinel."""
    number = float(value)
    if number == -999 or not (-1e6 < number < 1e6):
        raise ValueError("missing NASA POWER value")
    return number


def lat_lon_text(value: float) -> str:
    """Use stable coordinate formatting for NASA POWER request parameters."""
    return f"{value:.4f}"
