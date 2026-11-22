"""
Pydantic schemas for communicating with the separate RAG Advisory API
and defining frontend endpoint responses.
Conforms to the actual deployed API contract at https://sarva-mitra-rag.onrender.com/
"""

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field, ConfigDict


# ---------- RAG Advisory API Request Schemas ----------

class RAGLocation(BaseModel):
    """Location object accepted by the RAG API."""
    name: Optional[str] = None
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class RAGCurrentSensorData(BaseModel):
    """Live ESP32 sensor readings forwarded to the RAG API."""
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    soil_moisture: Optional[float] = Field(default=None, ge=0, le=100)


class RAGWeatherData(BaseModel):
    """Weather context forwarded to the RAG API."""
    rainfall_mm: Optional[float] = Field(default=None, ge=0)
    sunlight_wm2: Optional[float] = Field(default=None, ge=0)


class RAGHistoryRecord(BaseModel):
    """
    One day's historical record for the RAG API.
    Required fields: date, soil_moisture_pct, rainfall_mm.
    """
    date: str = Field(..., description="Date formatted as YYYY-MM-DD")
    soil_moisture_pct: float = Field(..., ge=0, le=100)
    sunlight_wm2: Optional[float] = Field(default=None, ge=0)
    rainfall_mm: float = Field(..., ge=0)
    leaf_wet_days: int = Field(default=0, ge=0, le=1)


class RAGChatMessage(BaseModel):
    """Chat message for multi-turn RAG conversations."""
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1)


class RAGRequest(BaseModel):
    """
    Payload sent to the RAG Advisory API POST /advisory endpoint.
    Combines field telemetry, weather context, ML prediction, and optional chat history.
    """
    device_id: str = Field(default="unknown-device")
    location: Any = Field(default="Vijayawada", description="String name or Location object")
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lon: Optional[float] = Field(default=None, ge=-180, le=180)
    target_date: Optional[str] = Field(default=None, description="Target date YYYY-MM-DD")
    history: List[RAGHistoryRecord] = Field(default_factory=list)
    crop: str = Field(default="unknown")
    question: str = Field(default="")
    ml_output: Optional[int] = Field(default=None, ge=0, le=1, description="Binary ML output (0 or 1)")
    ml_prediction: Optional[Dict[str, Any]] = Field(default=None, description="ML prediction sub-object")
    ml_response: Optional[Dict[str, Any]] = Field(default=None, description="Complete ML engine response")
    current_sensor_data: Optional[RAGCurrentSensorData] = None
    weather_data: Optional[RAGWeatherData] = None
    readings: Dict[str, Any] = Field(default_factory=dict, description="Raw sensor readings dict")
    chat_history: List[RAGChatMessage] = Field(default_factory=list)
    session_id: Optional[str] = None
    collection_name: Optional[str] = None


# ---------- RAG Advisory API Response ----------

class RAGResponse(BaseModel):
    """
    Response returned by the external RAG Advisory API.
    Uses extra='allow' to flexibly accommodate the RAG pipeline's exact JSON schema.
    """
    model_config = ConfigDict(extra="allow")

    status: Optional[str] = "success"
    advisory: Optional[str] = None
    action_items: Optional[List[str]] = None
    rag_sources: Optional[List[Any]] = None


# ---------- Frontend Process Endpoint Schemas ----------

class ProcessRequest(BaseModel):
    """
    Input schema for the POST /api/process endpoint.
    Latitude, longitude, location, device_id, date, crop, question can be passed from UI.
    Defaults to Vijayawada coordinates (16.51, 80.52) if omitted by UI.
    """
    device_id: Optional[str] = None
    target_date: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0, description="Latitude from UI (defaults to Vijayawada 16.51)")
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0, description="Longitude from UI (defaults to Vijayawada 80.52)")
    lat: Optional[float] = Field(default=None, ge=-90.0, le=90.0, description="Alias for latitude")
    lon: Optional[float] = Field(default=None, ge=-180.0, le=180.0, description="Alias for longitude")
    location: Optional[str] = Field(default=None, description="Location name from UI (defaults to Vijayawada)")
    crop: str = Field(default="tomato", description="Crop type for RAG advisory context")
    question: str = Field(default="", description="Optional natural-language question for RAG")
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
