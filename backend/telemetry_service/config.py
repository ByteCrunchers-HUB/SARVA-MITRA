import os
from pathlib import Path
from dotenv import load_dotenv

# Load root .env if present
root_dir = Path(__file__).resolve().parent.parent.parent
load_dotenv(root_dir / ".env")

# API Keys
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "")
WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY", "")
AGROMONITORING_API_KEY = os.getenv("AGROMONITORING_API_KEY", "")
TOMORROW_IO_API_KEY = os.getenv("TOMORROW_IO_API_KEY", "")

# Open-Meteo & SoilGrids are free and open (API key optional)
OPEN_METEO_API_KEY = os.getenv("OPEN_METEO_API_KEY", "")

# Default coordinates if none provided (e.g. Vijayawada, AP)
DEFAULT_LAT = float(os.getenv("DEFAULT_LAT", "16.51"))
DEFAULT_LON = float(os.getenv("DEFAULT_LON", "80.52"))
DEFAULT_LOCATION_NAME = os.getenv("DEFAULT_LOCATION_NAME", "Vijayawada")
