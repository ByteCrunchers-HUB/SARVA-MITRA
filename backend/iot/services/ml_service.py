"""
ML Service module.
Handles HTTP REST communication with the independent ML Engine API.
Preserves the full ML response structure without truncating or inventing values.
"""

import logging
import httpx
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from config import settings
from schemas.ml_schema import MLRequest, MLResponse

logger = logging.getLogger("smartfarm.ml")
_supported_locations_cache = None
_supported_locations_cached_at = 0.0


async def get_supported_locations() -> list[Dict[str, float]]:
    """Fetch coordinate points supported by the independent ML model."""
    global _supported_locations_cache, _supported_locations_cached_at
    now = time.monotonic()
    if _supported_locations_cache and now - _supported_locations_cached_at < 3600:
        return [location.copy() for location in _supported_locations_cache]

    base_url = settings.ml_api_url.rstrip("/")
    url = f"{base_url.rsplit('/', 1)[0]}/locations" if base_url.endswith("/predict") else f"{base_url}/locations"
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            locations = response.json().get("locations", [])
        _supported_locations_cache = [
            {"lat": float(item["lat"]), "lon": float(item["lon"])}
            for item in locations
        ]
        _supported_locations_cached_at = now
        return [location.copy() for location in _supported_locations_cache]
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        logger.error("Could not load locations supported by ML Engine: %s", exc)
        raise ConnectionError("Could not load supported locations from the ML service") from exc


async def call_ml_engine(request_payload: MLRequest) -> Dict[str, Any]:
    """
    Sends the seven-day API history payload to the independent ML Engine via HTTP POST.
    Validates and preserves the entire response.
    """
    url = settings.ml_api_url
    logger.info("Dispatching ML prediction request to %s for device %s", url, request_payload.device_id)

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            response = await client.post(
                url,
                json=request_payload.model_dump(),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            raw_data = response.json()

        # Validate against MLResponse schema while preserving all nested data
        validated_response = MLResponse(**raw_data)
        logger.info(
            "Received ML prediction: risk=%s (%.1f%%) from model '%s'",
            validated_response.prediction.risk_label,
            validated_response.prediction.risk_pct,
            validated_response.model.name
        )
        return validated_response.model_dump()

    except httpx.ConnectError:
        logger.error("Connection failed to ML Engine at %s. Service appears offline.", url)
        raise ConnectionError(f"Cannot connect to ML Engine at {url}. Ensure the ML API service is running.")
    except httpx.TimeoutException:
        logger.error("ML Engine timed out after %d seconds.", settings.request_timeout)
        raise TimeoutError(f"ML Engine API at {url} timed out after {settings.request_timeout}s.")
    except httpx.HTTPStatusError as e:
        logger.error("ML Engine returned error %s: %s", e.response.status_code, e.response.text)
        raise ValueError(f"ML Engine failed with HTTP status {e.response.status_code}: {e.response.text}")
    except Exception as e:
        logger.error("Error processing ML Engine response: %s", str(e))
        raise ValueError(f"Invalid ML Engine response format: {str(e)}")


def generate_mock_ml_response(
    device_id: str,
    target_date: str,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Generates a deterministic stub ML response conforming to the exact schema specification
    for testing when the external ML Engine API service is not yet deployed or running.
    """
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "device_id": device_id,
        "location": {
            "lat": settings.latitude if lat is None else lat,
            "lon": settings.longitude if lon is None else lon
        },
        "target_date": target_date,
        "prediction": {
            "risk_pct": 15.0,
            "risk_label": "low",
            "risk_bands": {
                "low_max": 20,
                "moderate_max": 60
            },
            "index_type": "weather_based_proxy",
            "validated": False
        },
        "model": {
            "name": "XGBoost (simulated_stub)",
            "trained_through": 2022
        },
        "inputs": [],
        "warnings": ["STUB_RESPONSE: Independent ML Engine API was simulated for offline testing."]
    }
