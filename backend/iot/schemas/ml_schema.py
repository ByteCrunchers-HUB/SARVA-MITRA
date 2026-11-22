"""
Pydantic schemas for communicating with the independent ML Engine API.
Conforms to the actual deployed API contract at https://sarva-mitra-ml.onrender.com/
"""

from datetime import date as DateType
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MLDayRecord(BaseModel):
    """
    One prior day's record. Maps to DayRecord in the ML Engine.
    Static soil fields are optional; if omitted the ML engine fills them from its static table.
    """
    date: str = Field(..., description="Date formatted as YYYY-MM-DD")
    soil_moisture_pct: float = Field(..., ge=0, le=100, description="Soil moisture percentage")
    air_temperature_c: float = Field(..., ge=-20, le=60, description="Air temperature in Celsius")
    humidity_pct: float = Field(..., ge=0, le=100, description="Relative humidity percentage")
    sunlight_wm2: Optional[float] = Field(default=None, ge=0, le=500, description="Solar radiation in W/m²")
    rainfall_mm: float = Field(default=0.0, ge=0, le=1000, description="Daily precipitation in mm")
    # Static soil fields (optional - ML engine fills from its trained static table)
    soil_ph: Optional[float] = Field(default=None, ge=3.5, le=9.5)
    organic_carbon: Optional[float] = Field(default=None, ge=0, le=100)
    clay_pct: Optional[float] = Field(default=None, ge=0, le=100)
    sand_pct: Optional[float] = Field(default=None, ge=0, le=100)
    silt_pct: Optional[float] = Field(default=None, ge=0, le=100)
    elevation_m: Optional[float] = Field(default=None, ge=0, le=6000)


class MLCurrentReading(BaseModel):
    """
    Today's live sensor reading. Maps to CurrentReading in the ML Engine.
    The ML engine merges this as the last day of history.
    """
    date: Optional[str] = Field(default=None, description="Defaults to today in ML engine")
    soil_moisture_pct: float = Field(..., ge=0, le=100)
    air_temperature_c: float = Field(..., ge=-20, le=60)
    humidity_pct: float = Field(..., ge=0, le=100)
    sunlight_wm2: Optional[float] = Field(default=None, ge=0, le=500)
    rainfall_mm: float = Field(default=0.0, ge=0, le=1000, description="Rain so far today, mm")


class MLRequest(BaseModel):
    """
    Payload sent to the ML Engine POST /predict endpoint.
    Must contain at least 7 consecutive daily history records.
    Optionally includes today's live sensor reading in `current`.
    """
    device_id: str = Field(..., min_length=1, max_length=64, description="Identifier of the field device")
    lat: float = Field(..., ge=6, le=38, description="Latitude (Indian subcontinent range)")
    lon: float = Field(..., ge=68, le=98, description="Longitude (Indian subcontinent range)")
    target_date: Optional[str] = Field(default=None, description="Target prediction date (YYYY-MM-DD)")
    history: List[MLDayRecord] = Field(
        ...,
        min_length=7,
        description="At least 7 consecutive prior daily records"
    )
    current: Optional[MLCurrentReading] = Field(
        default=None,
        description="Today's live sensor reading (merged as last day by ML engine)"
    )


class MLRiskBands(BaseModel):
    low_max: Optional[float] = None
    moderate_max: Optional[float] = None


class MLPrediction(BaseModel):
    risk_pct: float = Field(..., description="Predicted disease or drought risk percentage")
    risk_label: str = Field(..., description="Categorical risk rating: low, moderate, high")
    risk_bands: Optional[Dict[str, Any]] = None
    index_type: Optional[str] = None
    validated: Optional[bool] = None


class MLModelInfo(BaseModel):
    name: str = Field(..., description="Name of the machine learning model")
    trained_through: Optional[Any] = None


class MLResponse(BaseModel):
    """
    Complete response returned by the ML Engine API.
    All fields are preserved completely for downstream transmission to the RAG service.
    """
    schema_version: str = Field(default="1.0")
    generated_at: Optional[str] = None
    device_id: Optional[str] = None
    location: Optional[Dict[str, float]] = None
    target_date: Optional[str] = None
    prediction: MLPrediction
    model: MLModelInfo
    inputs: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    warnings: Optional[List[str]] = Field(default_factory=list)
