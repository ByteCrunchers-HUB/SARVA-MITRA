"""FastAPI service for Telemetry & Virtual Sensors.

Replaces IoT hardware by streaming live and historical telemetry
to ML Engine and RAG Pipeline.
"""
from __future__ import annotations

import os
from datetime import date
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from .config import DEFAULT_LAT, DEFAULT_LOCATION_NAME, DEFAULT_LON
    from .service import telemetry_service
except ImportError:
    from config import DEFAULT_LAT, DEFAULT_LOCATION_NAME, DEFAULT_LON
    from service import telemetry_service

ML_ENGINE_URL = os.getenv("ML_ENGINE_URL", "http://127.0.0.1:8000")
RAG_PIPELINE_URL = os.getenv("RAG_PIPELINE_URL", "http://127.0.0.1:8001")

app = FastAPI(title="Sarva Mitra Telemetry & Virtual Sensor API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictPipelineRequest(BaseModel):
    lat: float = Field(default=DEFAULT_LAT, ge=-90, le=90)
    lon: float = Field(default=DEFAULT_LON, ge=-180, le=180)
    location: str = DEFAULT_LOCATION_NAME
    target_date: date | None = None
    device_id: str = "virtual-node-01"


class AdvisoryPipelineRequest(BaseModel):
    lat: float = Field(default=DEFAULT_LAT, ge=-90, le=90)
    lon: float = Field(default=DEFAULT_LON, ge=-180, le=180)
    location: str = DEFAULT_LOCATION_NAME
    crop: str = "tomato"
    question: str = "What should I inspect today?"
    target_date: date | None = None
    device_id: str = "virtual-node-01"


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "telemetry_virtual_sensor",
        "weatherapi_configured": bool(telemetry_service.weatherapi_key),
        "tomorrow_configured": bool(telemetry_service.tomorrow_key),
        "agromonitoring_configured": bool(telemetry_service.agromonitoring_key),
        "openweather_configured": bool(telemetry_service.owm_key),
        "open_meteo_live": True,
    }


@app.get("/telemetry/current")
def get_current(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON):
    return telemetry_service.get_current_readings(lat=lat, lon=lon)


@app.get("/telemetry/history")
def get_history(
    lat: float = DEFAULT_LAT,
    lon: float = DEFAULT_LON,
    days: int = Query(default=8, ge=8, le=30),
    target_date: date | None = None,
):
    return telemetry_service.get_historical_records(lat=lat, lon=lon, target_date=target_date, days=days)


@app.get("/telemetry/ml-payload")
def get_ml_payload(
    lat: float = DEFAULT_LAT,
    lon: float = DEFAULT_LON,
    location: str = DEFAULT_LOCATION_NAME,
    target_date: date | None = None,
):
    return telemetry_service.build_ml_payload(
        lat=lat, lon=lon, location=location, target_date=target_date
    )


@app.get("/telemetry/rag-payload")
def get_rag_payload(
    lat: float = DEFAULT_LAT,
    lon: float = DEFAULT_LON,
    location: str = DEFAULT_LOCATION_NAME,
    crop: str = "tomato",
    question: str = "What should I inspect today?",
    target_date: date | None = None,
):
    return telemetry_service.build_rag_payload(
        lat=lat, lon=lon, location=location, crop=crop, question=question, target_date=target_date
    )


@app.post("/pipeline/predict")
def predict_with_telemetry(req: PredictPipelineRequest):
    """Fetches virtual telemetry history and forwards to ML Engine /predict."""
    payload = telemetry_service.build_ml_payload(
        lat=req.lat,
        lon=req.lon,
        location=req.location,
        target_date=req.target_date,
        device_id=req.device_id,
    )
    try:
        resp = httpx.post(f"{ML_ENGINE_URL}/predict", json=payload, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except httpx.RequestError as exc:
        raise HTTPException(502, f"ML Engine unreachable at {ML_ENGINE_URL}: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(exc.response.status_code, exc.response.text) from exc


@app.post("/pipeline/advisory")
def advisory_with_telemetry(req: AdvisoryPipelineRequest):
    """Fetches virtual telemetry, invokes ML prediction, and gets advisory from RAG."""
    rag_payload = telemetry_service.build_rag_payload(
        lat=req.lat,
        lon=req.lon,
        location=req.location,
        crop=req.crop,
        question=req.question,
        target_date=req.target_date,
        device_id=req.device_id,
    )
    try:
        resp = httpx.post(f"{RAG_PIPELINE_URL}/advisory", json=rag_payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except httpx.RequestError as exc:
        raise HTTPException(502, f"RAG Pipeline unreachable at {RAG_PIPELINE_URL}: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(exc.response.status_code, exc.response.text) from exc
