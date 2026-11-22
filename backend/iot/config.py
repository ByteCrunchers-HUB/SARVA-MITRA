"""
Configuration management module.
Loads environment variables from .env using Pydantic Settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Serial Port Settings
    serial_port: str = "COM9"
    serial_baudrate: int = 115200

    # Geographic Location
    latitude: float = 16.5062
    longitude: float = 80.6480
    location_name: str = "Vijayawada"

    # External APIs
    weather_api_base_url: str = "https://archive-api.open-meteo.com/v1/archive"
    weather_forecast_url: str = "https://api.open-meteo.com/v1/forecast"
    ml_api_url: str = "http://localhost:8001/predict"
    rag_api_url: str = "http://localhost:8002/rag/query"

    # Network Request Timeout (Seconds)
    request_timeout: int = 30

    # History Duplication Strategy for ML Input
    allow_duplicate_history: bool = True

    # General System
    device_id: str = "ESP32_01"
    log_level: str = "INFO"
    host: str = "127.0.0.1"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings singleton
settings = Settings()
