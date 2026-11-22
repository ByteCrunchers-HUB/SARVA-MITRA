"""
Configuration management module.
Loads environment variables from .env using Pydantic Settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Legacy serial settings retained for the optional compatibility endpoints.
    serial_port: str = "COM9"
    serial_baudrate: int = 115200

    # External environmental data source used by API-only ML requests.
    nasa_power_daily_url: str = "https://power.larc.nasa.gov/api/temporal/daily/point"
    external_data_cache_seconds: int = 900
    geocoding_url: str = "https://geocoding-api.open-meteo.com/v1/search"
    model_location_max_distance_km: float = 250.0

    # Geographic Location (Defaults to Vijayawada trained point)
    latitude: float = 16.51
    longitude: float = 80.52
    location_name: str = "Vijayawada"

    # External APIs
    weather_api_base_url: str = "https://archive-api.open-meteo.com/v1/archive"
    weather_forecast_url: str = "https://api.open-meteo.com/v1/forecast"
    ml_api_url: str = "https://sarva-mitra-ml.onrender.com/predict"
    rag_api_url: str = "https://sarva-mitra-rag.onrender.com/advisory"

    # Network Request Timeout (Seconds) - 60s for Render free tier spin-up
    request_timeout: int = 60

    # History Duplication Strategy for ML Input
    allow_duplicate_history: bool = False

    # General System
    device_id: str = "API_CLIENT"
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
