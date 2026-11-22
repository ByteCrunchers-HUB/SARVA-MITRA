"""
Validation utilities for sensor data and API parameters.
"""

from datetime import datetime
from typing import List, Tuple


def validate_date_format(date_str: str) -> bool:
    """Validates that a date string follows YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def validate_sensor_ranges(temperature: float, humidity: float, soil_moisture: float) -> Tuple[bool, List[str]]:
    """
    Validates physical sensor ranges:
    - Temperature (DHT11): 0 to 50°C (standard operating range) or -40 to 80°C
    - Humidity: 0% to 100%
    - Soil Moisture: 0% to 100%
    """
    errors: List[str] = []

    if not (-40.0 <= temperature <= 85.0):
        errors.append(f"Temperature {temperature}°C out of valid range (-40°C to 85°C)")

    if not (0.0 <= humidity <= 100.0):
        errors.append(f"Humidity {humidity}% out of valid range (0% to 100%)")

    if not (0.0 <= soil_moisture <= 100.0):
        errors.append(f"Soil moisture {soil_moisture}% out of valid range (0% to 100%)")

    return len(errors) == 0, errors
