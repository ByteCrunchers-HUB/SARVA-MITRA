"""Sarva Mitra ML engine.

Endpoints
  GET  /health   service status and loaded model
  POST /predict  risk for one device and day, from the daily history sent by the backend

Run:  uvicorn backend:app --host 0.0.0.0 --port 8000
Env:  SARVA_MODEL_PATH  trained .joblib bundle (default: models/sarva_mitra_risk_model.joblib)
"""
import os
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0"
IST = timezone(timedelta(hours=5, minutes=30))
MODEL_PATH = Path(os.getenv("SARVA_MODEL_PATH", "models/sarva_mitra_risk_model.joblib"))
HISTORY_DAYS = 8                       # the model needs this many prior days
RISK_LOW_MAX = 20                      # PLACEHOLDER risk bands, confirm with an agronomist
RISK_MODERATE_MAX = 60
INDEX_TYPE = "weather_based_proxy"     # not validated against field disease records

# Must match the training notebook exactly
FEATURES = [
    "lat", "lon",
    "soil_moisture_lag1", "soil_moisture_trend3",
    "sunlight_lag1", "rain_lag1",
    "rain_sum3_prev", "rain_sum7_prev", "wet_days3_prev",
    "doy_sin", "doy_cos",
]


# ---------- request models ----------

class DayRecord(BaseModel):
    date: date
    soil_moisture_pct: float = Field(ge=0, le=100)
    sunlight_wm2: float | None = Field(default=None, ge=0, le=500)
    rainfall_mm: float = Field(ge=0, le=1000)
    leaf_wet_days: int = Field(ge=0, le=1)


class PredictRequest(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)
    location: str = Field(min_length=1)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    target_date: date
    history: list[DayRecord] = Field(min_length=HISTORY_DAYS)


class HistoryError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


# ---------- model ----------

@lru_cache(maxsize=1)
def load_bundle() -> dict:
    """Bundle keys: model, features, target, trained_through, selected_model."""
    return joblib.load(MODEL_PATH)


# ---------- features (identical to training) ----------

def build_features(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw.sort_values(["location", "date"]).reset_index(drop=True).copy()
    d["sunlight_wm2"] = d.groupby("location")["sunlight_wm2"].transform(
        lambda s: s.interpolate(limit=3, limit_direction="both"))
    d["sunlight_wm2"] = d["sunlight_wm2"].fillna(d["sunlight_wm2"].median())

    g = d.groupby("location")
    d["soil_moisture_lag1"] = g["soil_moisture_pct"].shift(1)
    d["soil_moisture_trend3"] = g["soil_moisture_pct"].shift(1) - g["soil_moisture_pct"].shift(4)
    d["sunlight_lag1"] = g["sunlight_wm2"].shift(1)
    d["rain_lag1"] = g["rainfall_mm"].shift(1)
    d["rain_sum3_prev"] = g["rainfall_mm"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).sum())
    d["rain_sum7_prev"] = g["rainfall_mm"].transform(lambda s: s.shift(1).rolling(7, min_periods=1).sum())
    d["wet_days3_prev"] = g["leaf_wet_days"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).sum())

    doy = d["date"].dt.dayofyear
    d["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    d["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    return d


def features_for_target(history: pd.DataFrame, target: pd.Timestamp) -> pd.DataFrame:
    last = history.iloc[-1]
    target_row = pd.DataFrame([{
        "date": target, "location": last["location"], "lat": last["lat"], "lon": last["lon"],
        "soil_moisture_pct": np.nan, "sunlight_wm2": np.nan,
        "rainfall_mm": np.nan, "leaf_wet_days": np.nan,
    }])
    feats = build_features(pd.concat([history, target_row], ignore_index=True))
    return feats[feats["date"] == target]


# ---------- prediction ----------

def risk_level(pct: float) -> str:
    if pct < RISK_LOW_MAX:
        return "low"
    if pct < RISK_MODERATE_MAX:
        return "moderate"
    return "high"


def run_prediction(req: PredictRequest, bundle: dict) -> dict:
    hist = pd.DataFrame([{
        "date": pd.Timestamp(r.date), "location": req.location, "lat": req.lat, "lon": req.lon,
        "soil_moisture_pct": r.soil_moisture_pct, "sunlight_wm2": r.sunlight_wm2,
        "rainfall_mm": r.rainfall_mm, "leaf_wet_days": r.leaf_wet_days,
    } for r in req.history]).sort_values("date").reset_index(drop=True)

    target = pd.Timestamp(req.target_date)
    if hist["date"].duplicated().any():
        raise HistoryError("invalid_history", "history has duplicate dates")
    if hist["date"].diff().dropna().ne(pd.Timedelta(days=1)).any():
        raise HistoryError("invalid_history", "history must be consecutive daily records with no gaps")
    if hist["date"].iloc[-1] != target - pd.Timedelta(days=1):
        raise HistoryError("invalid_history", "history must end the day before target_date")

    feats = features_for_target(hist, target)
    if feats.empty or feats[FEATURES].isna().to_numpy().any():
        raise HistoryError("missing_values",
                           "not enough valid values to build features (check sunlight and soil moisture)")

    pred = float(np.clip(bundle["model"].predict(feats[FEATURES])[0], 0, 100))
    warnings = [f"sunlight missing for {r.date.date().isoformat()}, interpolated"
                for r in hist.itertuples() if pd.isna(r.sunlight_wm2)]

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(IST).replace(microsecond=0).isoformat(),
        "device_id": req.device_id,
        "location": {"name": req.location, "lat": req.lat, "lon": req.lon},
        "target_date": req.target_date.isoformat(),
        "prediction": {
            "risk_pct": round(pred, 2),
            "risk_level": risk_level(pred),
            "risk_bands": {"low_max": RISK_LOW_MAX, "moderate_max": RISK_MODERATE_MAX},
            "index_type": INDEX_TYPE,
            "validated": False,
        },
        "model": {"name": bundle["selected_model"], "trained_through": bundle["trained_through"]},
        "inputs": [{
            "date": r.date.date().isoformat(),
            "soil_moisture_pct": r.soil_moisture_pct,
            "sunlight_wm2": None if pd.isna(r.sunlight_wm2) else r.sunlight_wm2,
            "rainfall_mm": r.rainfall_mm,
            "leaf_wet_days": int(r.leaf_wet_days),
        } for r in hist.itertuples()],
        "warnings": warnings,
    }


def error_body(code: str, message: str, details=None) -> dict:
    err = {"code": code, "message": message}
    if details is not None:
        err["details"] = details
    return {"schema_version": SCHEMA_VERSION, "error": err}


# ---------- app ----------

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.bundle = load_bundle()   # fails at startup if the model file is missing
    yield


app = FastAPI(title="Sarva Mitra ML Engine", version=SCHEMA_VERSION, lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def invalid_request(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422,
                        content=error_body("invalid_request", "request validation failed",
                                           jsonable_encoder(exc.errors())))


@app.get("/health")
def health(request: Request):
    b = request.app.state.bundle
    return {"schema_version": SCHEMA_VERSION, "status": "ok",
            "model": {"name": b["selected_model"], "trained_through": b["trained_through"]}}


@app.post("/predict")
def predict(req: PredictRequest, request: Request):
    try:
        return run_prediction(req, request.app.state.bundle)
    except HistoryError as e:
        return JSONResponse(status_code=422, content=error_body(e.code, e.message))