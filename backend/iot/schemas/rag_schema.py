"""
Pydantic schemas for communicating with the separate RAG Advisory API
and defining frontend endpoint responses.
Conforms to the actual deployed API contract at https://sarva-mitra-rag.onrender.com/
"""

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator


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
    Combines location context, environmental history, ML prediction, and optional chat history.
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
    A UI client must submit a place name or both coordinates, plus the selected crop.
    """
    device_id: Optional[str] = None
    target_date: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0, description="Farm latitude supplied by the UI")
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0, description="Farm longitude supplied by the UI")
    lat: Optional[float] = Field(default=None, ge=-90.0, le=90.0, description="Alias for UI latitude")
    lon: Optional[float] = Field(default=None, ge=-180.0, le=180.0, description="Alias for UI longitude")
    location: Optional[str] = Field(default=None, description="Place name supplied by the UI; geocoded by the backend")
    crop: str = Field(..., min_length=1, description="Crop selected in the UI")
    question: str = Field(default="", description="Optional natural-language question for RAG")
    use_stub_ml: bool = False
    use_stub_rag: bool = False

    @model_validator(mode="after")
    def require_location_input(self):
        latitude = self.latitude if self.latitude is not None else self.lat
        longitude = self.longitude if self.longitude is not None else self.lon
        if (latitude is None) != (longitude is None):
            raise ValueError("Provide both latitude and longitude, or provide a place name.")
        if latitude is None and not (self.location and self.location.strip()):
            raise ValueError("Provide a place name or both latitude and longitude from the UI.")
        return self


class ProcessResponse(BaseModel):
    """
    End-to-end response returned to the frontend.
    """
    device_id: str
    target_date: str
    status: str
    environment_history: List[Dict[str, Any]] = Field(default_factory=list)
    sensor_data: Optional[Dict[str, Any]] = None
    weather_data: Optional[Dict[str, Any]] = None
    ml_response: Optional[Dict[str, Any]] = None
    rag_response: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
