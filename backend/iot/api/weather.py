"""
Weather endpoints for retrieving environmental data from Open-Meteo.
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from config import settings
from services.weather_service import fetch_weather
from utils.validation import validate_date_format

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("", summary="Fetch environmental weather conditions")
async def get_weather(
    target_date: Optional[str] = Query(None, description="Observation date (YYYY-MM-DD). Defaults to today."),
    lat: Optional[float] = Query(None, description="Latitude (defaults to .env setting)"),
    lon: Optional[float] = Query(None, description="Longitude (defaults to .env setting)")
):
    """
    Fetches rainfall in mm and sunlight in W/m² for the configured farm coordinates.
    Uses Open-Meteo API.
    """
    selected_date = target_date or date.today().strftime("%Y-%m-%d")

    if not validate_date_format(selected_date):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: '{selected_date}'. Date must be YYYY-MM-DD."
        )

    latitude = lat if lat is not None else settings.latitude
    longitude = lon if lon is not None else settings.longitude

    try:
        data = await fetch_weather(lat=latitude, lon=longitude, target_date=selected_date)
        return {
            "status": "success",
            "location": {
                "name": settings.location_name,
                "lat": latitude,
                "lon": longitude
            },
            "weather": data
        }
    except (ValueError, ConnectionError) as err:
        raise HTTPException(status_code=502, detail=str(err))
