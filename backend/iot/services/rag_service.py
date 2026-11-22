"""
RAG Service module.
Communicates with the separate, externally implemented RAG Pipeline API.
Sends the combined telemetry, weather context, and complete ML engine prediction via HTTP POST,
and returns the final advisory response to FastAPI.
"""

import logging
import httpx
from typing import Dict, Any, Optional

from config import settings
from schemas.rag_schema import RAGRequest, LocationCoordinates, CurrentSensorData, WeatherDataContext

logger = logging.getLogger("smartfarm.rag")


def build_rag_request(
    device_id: str,
    lat: float,
    lon: float,
    target_date: str,
    sensor_data: Optional[Dict[str, Any]],
    weather_data: Optional[Dict[str, Any]],
    ml_response: Dict[str, Any]
) -> RAGRequest:
    """
    Constructs the integration payload to send to the separate RAG API endpoint.
    Maintains the complete ML response.
    """
    curr_sensors = None
    if sensor_data:
        curr_sensors = CurrentSensorData(
            temperature=sensor_data.get("temperature"),
            humidity=sensor_data.get("humidity"),
            soil_moisture=sensor_data.get("soil_moisture")
        )

    weather_context = None
    if weather_data:
        weather_context = WeatherDataContext(
            rainfall_mm=weather_data.get("rainfall_mm", 0.0),
            sunlight_wm2=weather_data.get("sunlight_wm2", 0.0)
        )

    return RAGRequest(
        device_id=device_id,
        location=LocationCoordinates(lat=lat, lon=lon),
        target_date=target_date,
        current_sensor_data=curr_sensors,
        weather_data=weather_context,
        ml_response=ml_response  # Forwarded completely without modification
    )


async def call_rag_pipeline(rag_request: RAGRequest) -> Dict[str, Any]:
    """
    Invokes the external RAG Pipeline API via HTTP POST.
    """
    url = settings.rag_api_url
    logger.info("Forwarding combined context to RAG Pipeline at %s", url)

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            response = await client.post(
                url,
                json=rag_request.model_dump(),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            rag_output = response.json()

        logger.info("Successfully received RAG Pipeline response.")
        return rag_output

    except httpx.ConnectError:
        logger.error("Connection failed to RAG Pipeline at %s. Service appears offline.", url)
        raise ConnectionError(f"Cannot connect to RAG Pipeline at {url}. Ensure the RAG service is running.")
    except httpx.TimeoutException:
        logger.error("RAG Pipeline timed out after %d seconds.", settings.request_timeout)
        raise TimeoutError(f"RAG Pipeline API at {url} timed out after {settings.request_timeout}s.")
    except httpx.HTTPStatusError as e:
        logger.error("RAG Pipeline returned error %s: %s", e.response.status_code, e.response.text)
        raise ValueError(f"RAG Pipeline failed with HTTP status {e.response.status_code}: {e.response.text}")
    except Exception as e:
        logger.error("Unexpected error in RAG service: %s", str(e))
        raise ValueError(f"Invalid RAG Pipeline response: {str(e)}")


def generate_mock_rag_response(device_id: str, risk_label: str) -> Dict[str, Any]:
    """
    Generates a deterministic stub RAG response for offline end-to-end testing
    when the standalone RAG service is not yet running.
    """
    return {
        "status": "success",
        "device_id": device_id,
        "advisory": (
            f"Automated Advisory: Predicted crop risk is currently '{risk_label}'. "
            "Ensure regular drip irrigation schedule based on soil moisture trends. "
            "Monitor foliage for fungal symptoms if rainfall occurs."
        ),
        "action_items": [
            "Maintain current irrigation schedule",
            "Check soil moisture levels daily at 08:00 AM",
            "Inspect low leaves for mildew or blight signs"
        ],
        "warnings": ["STUB_RESPONSE: RAG Pipeline response was simulated for testing purposes."]
    }
