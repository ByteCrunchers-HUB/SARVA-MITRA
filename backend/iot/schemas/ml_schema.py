"""
Pydantic schemas for communicating with the independent ML Engine API.
Strictly conforms to the 8-record history requirement and full prediction response preservation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class MLHistoryRecord(BaseModel):
    """
    Individual daily record required by the ML model.
    Note: Air temperature and humidity are deliberately excluded from ML input history
    per the exact ML engine contract specification.
    """
    date: str = Field(..., description="Date formatted as YYYY-MM-DD")
    soil_moisture_pct: float = Field(..., description="Soil moisture percentage")
    sunlight_wm2: float = Field(..., description="Solar radiation in W/m²")
    rainfall_mm: float = Field(..., description="Daily precipitation in mm")
    leaf_wet_days: int = Field(default=0, description="Leaf wetness indicator/days")


class MLRequest(BaseModel):
    """
    Payload constructed and sent to the independent ML Engine API.
    Must contain exactly 8 daily history records.
    """
    device_id: str = Field(..., description="Identifier of the field device")
    location: str = Field(..., description="Geographic location name")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    target_date: str = Field(..., description="Target prediction date (YYYY-MM-DD)")
    history: List[MLHistoryRecord] = Field(
        ...,
        min_length=8,
        max_length=8,
        description="Exactly 8 consecutive daily records required by ML engine"
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


class MLInputRecord(BaseModel):
    date: Optional[str] = None
    source: Optional[str] = None
    soil_moisture_pct: Optional[float] = None
    air_temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    sunlight_wm2: Optional[float] = None
    rainfall_mm: Optional[float] = None
    leaf_wet_days: Optional[int] = None


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
