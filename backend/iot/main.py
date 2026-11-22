"""
Main entry point for the Smart Agriculture Monitoring System FastAPI Backend.
Integrates hardware serial communication, database, weather, ML, and RAG pipelines.
"""

import logging
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database.database import init_db
from hardware.serial_receiver import SerialReceiver

# Import Routers
from api.health import router as health_router
from api.sensors import router as sensors_router
from api.weather import router as weather_router
from api.history import router as history_router
from api.process import router as process_router

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("smartfarm.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes database tables and background serial receiver on startup,
    and cleanly tears down background tasks on shutdown.
    """
    logger.info("=== Starting Smart Agriculture Monitoring System ===")
    
    # 1. Initialize SQLite Database
    await init_db()

    # 2. Initialize and Start ESP32 Serial Receiver (handles cloud/local mode)
    serial_receiver = SerialReceiver(
        port=settings.serial_port,
        baudrate=settings.serial_baudrate,
        enabled=settings.enable_serial
    )
    app.state.serial_receiver = serial_receiver
    await serial_receiver.start()

    logger.info("FastAPI backend initialized and ready to receive requests.")
    yield

    # Shutdown
    logger.info("Shutting down Smart Agriculture Monitoring System...")
    await serial_receiver.stop()
    logger.info("Shutdown complete.")


# Initialize FastAPI Application
app = FastAPI(
    title="Smart Agriculture Monitoring System",
    description=(
        "Centralized integration layer connecting ESP32 hardware telemetry, "
        "Open-Meteo weather data, persistent SQLite historical records, "
        "an independent ML Engine API, and a separately implemented RAG Pipeline API."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Frontend UI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Subsystem Routers
app.include_router(health_router, prefix="/api")
app.include_router(sensors_router, prefix="/api")
app.include_router(weather_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(process_router, prefix="/api")


@app.get("/", summary="Root Health Check & Welcome")
async def root():
    """Root route returning service identity and health."""
    return {
        "status": "online",
        "service": "Sarva Mitra Smart Agriculture IoT Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
