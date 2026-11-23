"""Location search and matching to coordinates supported by the ML model."""

import logging
import math
from typing import Any, Dict, List

import httpx

from config import settings
from services.ml_service import get_supported_locations

logger = logging.getLogger("smartfarm.location")


async def geocode_place(name: str) -> Dict[str, Any]:
    """Resolve a place name to latitude/longitude using Open-Meteo Geocoding."""
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            response = await client.get(
                settings.geocoding_url,
                params={"name": name, "count": 5, "language": "en", "format": "json"},
            )
            response.raise_for_status()
            results = response.json().get("results", [])
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Geocoding failed for %r: %s", name, exc)
        raise ConnectionError("Could not resolve this place with Open-Meteo Geocoding") from exc

    if not results:
        raise ValueError(f"No location found for {name!r}")

    # The ML model is trained on Indian locations, so prefer a matching result in India.
    result = next((item for item in results if item.get("country_code") == "IN"), results[0])
    return {
        "name": result.get("name", name),
        "admin1": result.get("admin1"),
        "country": result.get("country", ""),
        "latitude": float(result["latitude"]),
        "longitude": float(result["longitude"]),
    }


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two coordinates."""
    radius = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def match_trained_location(lat: float, lon: float) -> Dict[str, Any]:
    """Snap a requested place to the nearest supported ML static-soil point."""
    locations = await get_supported_locations()
    if not locations:
        raise ConnectionError("The ML service did not return any supported locations")

    nearest = min(
        locations,
        key=lambda item: distance_km(lat, lon, float(item["lat"]), float(item["lon"])),
    )
    distance = distance_km(lat, lon, float(nearest["lat"]), float(nearest["lon"]))
    if distance > settings.model_location_max_distance_km:
        raise ValueError(
            f"This location is {distance:.0f} km from the nearest ML-trained point; "
            f"the allowed distance is {settings.model_location_max_distance_km:.0f} km. "
            "Choose a supported location from GET /api/locations."
        )

    return {"lat": float(nearest["lat"]), "lon": float(nearest["lon"]), "distance_km": round(distance, 1)}


async def list_trained_locations() -> List[Dict[str, Any]]:
    """Return all coordinate points supported by the deployed ML model."""
    return await get_supported_locations()
