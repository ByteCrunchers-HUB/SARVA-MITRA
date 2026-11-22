"""
Pydantic schemas for communicating with the separate RAG Pipeline API
and defining frontend endpoint responses.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class LocationCoordinates(BaseModel):
    lat: float
    lon: float


class CurrentSensorData(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    soil_moisture: Optional[float] = None


class WeatherDataContext(BaseModel):
    rainfall_mm: float = 0.0
    sunlight_wm2: float = 0.0


class RAGRequest(BaseModel):
    """
    Combined payload forwarded from FastAPI to the separate RAG Pipeline API.
    Contains field readings, weather context, and the complete ML prediction object.
    """
    device_id: str
    location: LocationCoordinates
    target_date: str
    current_sensor_data: Optional[CurrentSensorData] = None
    weather_data: Optional[WeatherDataContext] = None
    ml_response: Dict[str, Any] = Field(
        ...,
        description="Complete, untouched JSON response received from ML Engine API"
    )


class RAGResponse(BaseModel):
    """
    Response returned by the external RAG pipeline.
    Uses extra='allow' to flexibly accommodate the RAG pipeline's exact JSON schema.
    """
    model_config = ConfigDict(extra="allow")

    status: Optional[str] = "success"
    advisory: Optional[str] = None
    action_items: Optional[List[str]] = None
    rag_sources: Optional[List[Any]] = None


class ProcessRequest(BaseModel):
    """
    Input schema for the POST /api/process endpoint.
    All fields are optional with automatic defaults from config and hardware.
    """
    device_id: Optional[str] = None
    target_date: Optional[str] = None
    use_stub_ml: bool = False
    use_stub_rag: bool = False


class ProcessResponse(BaseModel):
    """
    End-to-end response returned to the frontend.
    """
    device_id: str
    target_date: str
    status: str
    sensor_data: Optional[Dict[str, Any]] = None
    weather_data: Optional[Dict[str, Any]] = None
    ml_response: Optional[Dict[str, Any]] = None
    rag_response: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
