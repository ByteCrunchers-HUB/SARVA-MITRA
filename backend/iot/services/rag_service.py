"""
RAG Service module.
Communicates with the separate, externally implemented RAG Advisory API.
Sends field telemetry, weather context, and ML engine prediction via HTTP POST,
and returns the final advisory response to FastAPI.
"""

import logging
import httpx
from typing import Dict, Any, Optional, List

from config import settings
from schemas.rag_schema import (
    RAGRequest,
    RAGCurrentSensorData,
    RAGWeatherData,
    RAGHistoryRecord
)

logger = logging.getLogger("smartfarm.rag")


def build_rag_request(
    device_id: str,
    lat: float,
    lon: float,
    target_date: str,
    sensor_data: Optional[Dict[str, Any]],
    weather_data: Optional[Dict[str, Any]],
    ml_response: Dict[str, Any],
    history_records: Optional[List[RAGHistoryRecord]] = None,
    crop: str = "tomato",
    question: str = ""
) -> RAGRequest:
    """
    Constructs the integration payload for the RAG Advisory API (/advisory).
    """
    curr_sensors = None
    readings_dict = {}
    if sensor_data:
        curr_sensors = RAGCurrentSensorData(
            temperature=sensor_data.get("temperature"),
            humidity=sensor_data.get("humidity"),
            soil_moisture=sensor_data.get("soil_moisture")
        )
        readings_dict = {
            "temperature_c": sensor_data.get("temperature"),
            "humidity_pct": sensor_data.get("humidity"),
            "soil_moisture_pct": sensor_data.get("soil_moisture")
        }

    weather_context = None
    if weather_data:
        weather_context = RAGWeatherData(
            rainfall_mm=weather_data.get("rainfall_mm", 0.0),
            sunlight_wm2=weather_data.get("sunlight_wm2", 0.0)
        )

    # Extract risk prediction
    ml_pred = ml_response.get("prediction", {}) if ml_response else {}
    ml_output_val = 1 if ml_pred.get("risk_label", "").lower() in ["moderate", "high"] else 0

    return RAGRequest(
        device_id=device_id,
        location=settings.location_name,
        lat=lat,
        lon=lon,
        target_date=target_date,
        history=history_records or [],
        crop=crop,
        question=question or "What farming actions or crop protections are recommended based on current readings?",
        ml_output=ml_output_val,
        ml_prediction=ml_pred,
        ml_response=ml_response,
        current_sensor_data=curr_sensors,
        weather_data=weather_context,
        readings=readings_dict
    )


async def call_rag_pipeline(rag_request: RAGRequest) -> Dict[str, Any]:
    """
    Invokes the external RAG Advisory API via HTTP POST.
    """
    url = settings.rag_api_url
    logger.info("Forwarding combined context to RAG Advisory API at %s", url)

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            response = await client.post(
                url,
                json=rag_request.model_dump(),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            rag_output = response.json()

        logger.info("Successfully received RAG Advisory response.")
        return rag_output

    except httpx.ConnectError:
        logger.error("Connection failed to RAG API at %s. Service appears offline.", url)
        raise ConnectionError(f"Cannot connect to RAG API at {url}. Ensure the service is running.")
    except httpx.TimeoutException:
        logger.error("RAG API timed out after %d seconds.", settings.request_timeout)
        raise TimeoutError(f"RAG API at {url} timed out after {settings.request_timeout}s.")
    except httpx.HTTPStatusError as e:
        logger.error("RAG API returned error %s: %s", e.response.status_code, e.response.text)
        raise ValueError(f"RAG API failed with HTTP status {e.response.status_code}: {e.response.text}")
    except Exception as e:
        logger.error("Unexpected error in RAG service: %s", str(e))
        raise ValueError(f"Invalid RAG response: {str(e)}")


def generate_mock_rag_response(device_id: str, risk_label: str) -> Dict[str, Any]:
    """
    Generates a deterministic stub RAG response for offline end-to-end testing.
    """
    return {
        "status": "success",
        "device_id": device_id,
        "advisory": (
            f"Advisory based on '{risk_label}' crop risk: "
            "Ensure regular irrigation schedule based on soil moisture trends. "
            "Inspect crops for disease symptoms or pest presence under high humidity conditions."
        ),
        "action_items": [
            "Maintain soil moisture within optimal range for current growth stage",
            "Check soil moisture readings daily via ESP32 telemetry",
            "Monitor foliage for mildew or blight signs if rainfall or high humidity occurs"
        ],
        "warnings": ["STUB_RESPONSE: RAG Advisory response was simulated for testing purposes."]
    }
