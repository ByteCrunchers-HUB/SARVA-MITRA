"""Telemetry and Virtual Sensor Service.

Provides real-time and historical agro-meteorological data from free APIs
(WeatherAPI, Tomorrow.io, AgroMonitoring, OpenWeatherMap, Open-Meteo, SoilGrids).
Formats inputs directly into the schemas required by the ML Engine and RAG Pipeline.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

try:
    from .config import (
        AGROMONITORING_API_KEY,
        DEFAULT_LAT,
        DEFAULT_LOCATION_NAME,
        DEFAULT_LON,
        OPENWEATHERMAP_API_KEY,
        TOMORROW_IO_API_KEY,
        WEATHERAPI_KEY,
    )
except ImportError:
    from config import (
        AGROMONITORING_API_KEY,
        DEFAULT_LAT,
        DEFAULT_LOCATION_NAME,
        DEFAULT_LON,
        OPENWEATHERMAP_API_KEY,
        TOMORROW_IO_API_KEY,
        WEATHERAPI_KEY,
    )

logger = logging.getLogger("telemetry_service")
IST = timezone(timedelta(hours=5, minutes=30))


class TelemetryService:
    def __init__(self):
        self.weatherapi_key = WEATHERAPI_KEY
        self.tomorrow_key = TOMORROW_IO_API_KEY
        self.agromonitoring_key = AGROMONITORING_API_KEY
        self.owm_key = OPENWEATHERMAP_API_KEY

    def get_current_readings(self, lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON) -> dict[str, Any]:
        """Fetch real-time ambient and soil telemetry with multi-API fallback."""
        data: dict[str, Any] = {
            "source": "unknown",
            "lat": lat,
            "lon": lon,
            "timestamp": datetime.now(IST).isoformat(),
            "temperature_c": None,
            "humidity_pct": None,
            "rainfall_mm": 0.0,
            "sunlight_wm2": None,
            "soil_moisture_pct": None,
            "leaf_wet_days": 0,
        }

        # 1. Try WeatherAPI for ambient weather
        if self.weatherapi_key:
            try:
                resp = httpx.get(
                    "https://api.weatherapi.com/v1/current.json",
                    params={"key": self.weatherapi_key, "q": f"{lat},{lon}"},
                    timeout=5,
                )
                if resp.status_code == 200:
                    curr = resp.json().get("current", {})
                    data["temperature_c"] = float(curr.get("temp_c", 25.0))
                    data["humidity_pct"] = float(curr.get("humidity", 60.0))
                    data["rainfall_mm"] = float(curr.get("precip_mm", 0.0))
                    data["source"] = "WeatherAPI"
            except Exception as e:
                logger.warning("WeatherAPI fetch failed: %s", e)

        # 2. Try Tomorrow.io if solar or temperature missing
        if self.tomorrow_key and (data["sunlight_wm2"] is None or data["temperature_c"] is None):
            try:
                resp = httpx.get(
                    "https://api.tomorrow.io/v4/weather/realtime",
                    params={"location": f"{lat},{lon}", "apikey": self.tomorrow_key},
                    timeout=5,
                )
                if resp.status_code == 200:
                    vals = resp.json().get("data", {}).get("values", {})
                    if data["temperature_c"] is None:
                        data["temperature_c"] = float(vals.get("temperature", 25.0))
                    if data["humidity_pct"] is None:
                        data["humidity_pct"] = float(vals.get("humidity", 60.0))
                    if "solarGHI" in vals and vals["solarGHI"] is not None:
                        data["sunlight_wm2"] = float(min(500.0, max(0.0, vals["solarGHI"])))
                    if not data["source"] or data["source"] == "unknown":
                        data["source"] = "Tomorrow.io"
            except Exception as e:
                logger.warning("Tomorrow.io fetch failed: %s", e)

        # 3. Always query Open-Meteo for soil moisture and instant shortwave radiation
        try:
            resp = httpx.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,precipitation,soil_moisture_0_to_1cm,shortwave_radiation_instant",
                    "timezone": "auto",
                },
                timeout=6,
            )
            if resp.status_code == 200:
                curr = resp.json().get("current", {})
                if data["temperature_c"] is None and "temperature_2m" in curr:
                    data["temperature_c"] = float(curr["temperature_2m"])
                if data["humidity_pct"] is None and "relative_humidity_2m" in curr:
                    data["humidity_pct"] = float(curr["relative_humidity_2m"])
                if "precipitation" in curr and curr["precipitation"] is not None:
                    data["rainfall_mm"] = max(data["rainfall_mm"], float(curr["precipitation"]))
                if data["sunlight_wm2"] is None and "shortwave_radiation_instant" in curr:
                    rad = float(curr.get("shortwave_radiation_instant", 200.0) or 0.0)
                    data["sunlight_wm2"] = min(500.0, max(0.0, round(rad, 2)))
                if "soil_moisture_0_to_1cm" in curr and curr["soil_moisture_0_to_1cm"] is not None:
                    # Convert m3/m3 to percentage (0.16 -> 16.0%)
                    raw_sm = float(curr["soil_moisture_0_to_1cm"])
                    data["soil_moisture_pct"] = round(raw_sm * 100.0, 2)
                if not data["source"] or data["source"] == "unknown":
                    data["source"] = "Open-Meteo"
        except Exception as e:
            logger.warning("Open-Meteo current fetch failed: %s", e)

        # 4. Fallback defaults if APIs failed
        if data["temperature_c"] is None:
            data["temperature_c"] = 26.5
        if data["humidity_pct"] is None:
            data["humidity_pct"] = 65.0
        if data["sunlight_wm2"] is None:
            data["sunlight_wm2"] = 210.0
        if data["soil_moisture_pct"] is None:
            data["soil_moisture_pct"] = 32.0

        # Leaf wetness heuristic: wet if rain > 0.2mm or humidity >= 85%
        data["leaf_wet_days"] = 1 if (data["rainfall_mm"] > 0.2 or data["humidity_pct"] >= 85.0) else 0
        return data

    def get_historical_records(
        self,
        lat: float = DEFAULT_LAT,
        lon: float = DEFAULT_LON,
        target_date: date | None = None,
        days: int = 8,
    ) -> list[dict[str, Any]]:
        """Fetch consecutive historical daily records ending the day before target_date.

        ML Engine requirement:
        history must be strictly consecutive and end on target_date - 1 day.
        """
        if target_date is None:
            target_date = datetime.now(IST).date()

        end_date = target_date - timedelta(days=1)
        start_date = end_date - timedelta(days=days - 1)

        # We request past_days from Open-Meteo
        # Use Open-Meteo forecast past_days or archive
        try:
            resp = httpx.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "past_days": days + 2,
                    "forecast_days": 1,
                    "hourly": "temperature_2m,relative_humidity_2m,precipitation,soil_moisture_0_to_1cm,shortwave_radiation",
                    "timezone": "auto",
                },
                timeout=10,
            )
            if resp.status_code == 200:
                hourly = resp.json().get("hourly", {})
                times = hourly.get("time", [])
                temps = hourly.get("temperature_2m", [])
                humids = hourly.get("relative_humidity_2m", [])
                precips = hourly.get("precipitation", [])
                soil_ms = hourly.get("soil_moisture_0_to_1cm", [])
                rads = hourly.get("shortwave_radiation", [])

                # Aggregate by calendar day (YYYY-MM-DD)
                daily_buckets: dict[str, dict[str, list[float]]] = {}
                for idx, t_str in enumerate(times):
                    d_str = t_str.split("T")[0]
                    if d_str not in daily_buckets:
                        daily_buckets[d_str] = {
                            "temp": [],
                            "humidity": [],
                            "precip": [],
                            "soil_m": [],
                            "sun": [],
                        }
                    if idx < len(temps) and temps[idx] is not None:
                        daily_buckets[d_str]["temp"].append(temps[idx])
                    if idx < len(humids) and humids[idx] is not None:
                        daily_buckets[d_str]["humidity"].append(humids[idx])
                    if idx < len(precips) and precips[idx] is not None:
                        daily_buckets[d_str]["precip"].append(precips[idx])
                    if idx < len(soil_ms) and soil_ms[idx] is not None:
                        daily_buckets[d_str]["soil_m"].append(soil_ms[idx])
                    if idx < len(rads) and rads[idx] is not None:
                        daily_buckets[d_str]["sun"].append(rads[idx])

                history: list[dict[str, Any]] = []
                cur = start_date
                while cur <= end_date:
                    d_iso = cur.isoformat()
                    b = daily_buckets.get(d_iso)
                    if b and b["soil_m"]:
                        avg_sm = (sum(b["soil_m"]) / len(b["soil_m"])) * 100.0
                        tot_rain = sum(b["precip"]) if b["precip"] else 0.0
                        avg_temp = sum(b["temp"]) / len(b["temp"]) if b["temp"] else 25.0
                        avg_hum = sum(b["humidity"]) / len(b["humidity"]) if b["humidity"] else 65.0
                        # Daytime sun average (filter out night zeroes for realistic W/m2)
                        day_sun = [v for v in b["sun"] if v > 5.0]
                        avg_sun = (sum(day_sun) / len(day_sun)) if day_sun else 180.0
                        leaf_wet = 1 if (tot_rain > 0.5 or avg_hum >= 80.0) else 0

                        history.append({
                            "date": d_iso,
                            "soil_moisture_pct": round(min(100.0, max(0.0, avg_sm)), 2),
                            "sunlight_wm2": round(min(500.0, max(0.0, avg_sun)), 2),
                            "rainfall_mm": round(max(0.0, tot_rain), 2),
                            "leaf_wet_days": leaf_wet,
                            "air_temperature_c": round(avg_temp, 2),
                            "humidity_pct": round(avg_hum, 2),
                        })
                    else:
                        # Interpolate fallback day if missing from bucket
                        history.append({
                            "date": d_iso,
                            "soil_moisture_pct": 28.5,
                            "sunlight_wm2": 195.0,
                            "rainfall_mm": 0.0,
                            "leaf_wet_days": 0,
                            "air_temperature_c": 25.0,
                            "humidity_pct": 60.0,
                        })
                    cur += timedelta(days=1)

                if len(history) >= days:
                    return history[-days:]
        except Exception as e:
            logger.error("Failed to build history from Open-Meteo: %s", e)

        # Fallback consecutive days generator if external query failed
        fallback_history = []
        cur = start_date
        while cur <= end_date:
            fallback_history.append({
                "date": cur.isoformat(),
                "soil_moisture_pct": 30.0,
                "sunlight_wm2": 190.0,
                "rainfall_mm": 0.0,
                "leaf_wet_days": 0,
                "air_temperature_c": 25.0,
                "humidity_pct": 60.0,
            })
            cur += timedelta(days=1)
        return fallback_history

    def build_ml_payload(
        self,
        lat: float = DEFAULT_LAT,
        lon: float = DEFAULT_LON,
        location: str = DEFAULT_LOCATION_NAME,
        target_date: date | None = None,
        device_id: str = "virtual-telemetry-01",
    ) -> dict[str, Any]:
        """Generate a complete payload ready for ML Engine `POST /predict`."""
        if target_date is None:
            target_date = datetime.now(IST).date()

        history = self.get_historical_records(lat=lat, lon=lon, target_date=target_date, days=8)
        return {
            "device_id": device_id,
            "location": location,
            "lat": lat,
            "lon": lon,
            "target_date": target_date.isoformat(),
            "history": [
                {
                    "date": row["date"],
                    "soil_moisture_pct": row["soil_moisture_pct"],
                    "sunlight_wm2": row["sunlight_wm2"],
                    "rainfall_mm": row["rainfall_mm"],
                    "leaf_wet_days": row["leaf_wet_days"],
                }
                for row in history
            ],
        }

    def build_rag_payload(
        self,
        crop: str = "tomato",
        question: str = "What should I inspect today?",
        lat: float = DEFAULT_LAT,
        lon: float = DEFAULT_LON,
        location: str = DEFAULT_LOCATION_NAME,
        target_date: date | None = None,
        device_id: str = "virtual-telemetry-01",
    ) -> dict[str, Any]:
        """Generate a complete payload ready for RAG Pipeline `POST /advisory`."""
        if target_date is None:
            target_date = datetime.now(IST).date()

        curr = self.get_current_readings(lat=lat, lon=lon)
        history = self.get_historical_records(lat=lat, lon=lon, target_date=target_date, days=8)

        return {
            "device_id": device_id,
            "location": {
                "name": location,
                "lat": lat,
                "lon": lon,
            },
            "target_date": target_date.isoformat(),
            "crop": crop,
            "question": question,
            "current_sensor_data": {
                "temperature": curr["temperature_c"],
                "humidity": curr["humidity_pct"],
                "soil_moisture": curr["soil_moisture_pct"],
            },
            "weather_data": {
                "rainfall_mm": curr["rainfall_mm"],
                "sunlight_wm2": curr["sunlight_wm2"],
            },
            "readings": {
                "temperature_c": curr["temperature_c"],
                "humidity_pct": curr["humidity_pct"],
                "soil_moisture_pct": curr["soil_moisture_pct"],
                "rainfall_mm": curr["rainfall_mm"],
                "sunlight_wm2": curr["sunlight_wm2"],
            },
            "history": [
                {
                    "date": row["date"],
                    "soil_moisture_pct": row["soil_moisture_pct"],
                    "sunlight_wm2": row["sunlight_wm2"],
                    "rainfall_mm": row["rainfall_mm"],
                    "leaf_wet_days": row["leaf_wet_days"],
                }
                for row in history
            ],
            "chat_history": [],
        }


# Singleton service instance
telemetry_service = TelemetryService()
