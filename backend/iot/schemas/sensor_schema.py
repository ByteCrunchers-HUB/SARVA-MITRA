"""
Pydantic schemas for ESP32 hardware sensor data and external weather readings.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class ESP32SensorReading(BaseModel):
    """
    Physical sensor readings received directly from the ESP32.
    Only 3 physical parameters: temperature, humidity, and soil moisture.
    """
    device_id: str = Field(..., description="Unique ESP32 device identifier (e.g., ESP32_01)")
    temperature: float = Field(..., ge=-40.0, le=85.0, description="Air temperature in Celsius")
    humidity: float = Field(..., ge=0.0, le=100.0, description="Air relative humidity percentage (0-100%)")
    soil_moisture: float = Field(..., ge=0.0, le=100.0, description="Soil moisture level percentage (0-100%)")
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WeatherReading(BaseModel):
    """
    Environmental parameters fetched from the external Weather API (Open-Meteo).
    """
    date: str = Field(..., description="Date of the weather observation in YYYY-MM-DD")
    rainfall_mm: float = Field(default=0.0, ge=0.0, description="Daily cumulative rainfall in millimeters")
    sunlight_wm2: float = Field(default=0.0, ge=0.0, description="Mean solar radiation in W/m²")
    source: str = Field(default="Open-Meteo", description="Provider name")


class DailyUnifiedRecord(BaseModel):
    """
    Combined daily snapshot saved to SQLite database.
    """
    device_id: str
    date: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    soil_moisture: Optional[float] = None
    rainfall_mm: Optional[float] = 0.0
    sunlight_wm2: Optional[float] = 0.0
    leaf_wet_days: Optional[int] = 0
    is_duplicated: bool = False
    created_at: Optional[str] = None
