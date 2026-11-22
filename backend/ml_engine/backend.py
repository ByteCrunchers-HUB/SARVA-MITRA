"""Sarva Mitra ML engine (FastAPI).

Endpoints
  GET  /health    service status and loaded model
  GET  /locations coordinates represented in the static model table
  POST /predict   risk % and risk label for the next day, from prior daily records
                  merged with the current sensed reading

Input (JSON)
  lat, lon             point (must be one of the trained points)
  target_date          optional; default is the day after the sensed reading
  history              at least 7 consecutive prior days, each with the 15-column record
                       (static soil fields may be omitted; they are filled from the static table)
  current              today's sensed reading (soil moisture, air temperature, humidity,
                       sunlight, rainfall). Merged in as the last day of the history.

Run:  uvicorn backend:app --host 0.0.0.0 --port 8000
Env:  SARVA_MODEL_PATH   default models/sarva_mitra_risk_model.joblib
      SARVA_STATIC_PATH  default models/static_features.csv
"""
import os
from contextlib import asynccontextmanager
from datetime import date as Day, datetime, timedelta, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

SCHEMA_VERSION = "1.0"
IST = timezone(timedelta(hours=5, minutes=30))
MODEL_PATH = Path(os.getenv("SARVA_MODEL_PATH", "models/sarva_mitra_risk_model.joblib"))
STATIC_PATH = Path(os.getenv("SARVA_STATIC_PATH", "models/static_features.csv"))

# Inputs measured each day (from the 15-column record, or the sensors)
DYNAMIC = ["soil_moisture_pct", "air_temperature_c", "humidity_pct", "sunlight_wm2", "rainfall_mm"]
# Fixed for each point
STATIC = ["lat", "lon", "soil_ph", "organic_carbon", "clay_pct", "sand_pct", "silt_pct", "elevation_m"]
# Built from previous days only, so the model never sees the day it predicts
LAGS = [f"{c}_lag1" for c in DYNAMIC] + ["rain_sum3_prev", "rain_sum7_prev", "doy_sin", "doy_cos"]
FEATURES = STATIC + LAGS
MIN_HISTORY_DAYS = 7      # the 7-day rain window needs 7 prior days
RECORD_STATIC = ["soil_ph", "organic_carbon", "clay_pct", "sand_pct", "silt_pct", "elevation_m"]

# PLACEHOLDER risk bands on the 0-100 scale, confirm with an agronomist or KVK officer
RISK_LOW_MAX = 20
RISK_MODERATE_MAX = 60
INDEX_TYPE = "weather_based_proxy"


def risk_label(pct: float) -> str:
    if pct < RISK_LOW_MAX:
        return "low"
    if pct < RISK_MODERATE_MAX:
        return "moderate"
    return "high"


def add_features(d: pd.DataFrame) -> pd.DataFrame:
    """One row per point per day. Adds lag features within each point. Used by training and the API."""
    d = d.sort_values(["lat", "lon", "date"]).copy()
    g = d.groupby(["lat", "lon"], sort=False)
    for c in DYNAMIC:
        d[f"{c}_lag1"] = g[c].shift(1)
    d["rain_sum3_prev"] = g["rainfall_mm"].transform(lambda s: s.shift(1).rolling(3, min_periods=3).sum())
    d["rain_sum7_prev"] = g["rainfall_mm"].transform(lambda s: s.shift(1).rolling(7, min_periods=7).sum())
    doy = d["date"].dt.dayofyear
    d["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    d["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    return d


# ---------- request and response models ----------

class DayRecord(BaseModel):
    """One prior day. Static fields are optional; if left out they come from the static table."""
    date: Day
    soil_moisture_pct: float = Field(ge=0, le=100)
    air_temperature_c: float = Field(ge=-20, le=60)
    humidity_pct: float = Field(ge=0, le=100)
    sunlight_wm2: float | None = Field(default=None, ge=0, le=500)
    rainfall_mm: float = Field(ge=0, le=1000)
    soil_ph: float | None = Field(default=None, ge=3.5, le=9.5)
    organic_carbon: float | None = Field(default=None, ge=0, le=100)
    clay_pct: float | None = Field(default=None, ge=0, le=100)
    sand_pct: float | None = Field(default=None, ge=0, le=100)
    silt_pct: float | None = Field(default=None, ge=0, le=100)
    elevation_m: float | None = Field(default=None, ge=0, le=6000)


class CurrentReading(BaseModel):
    """Today's sensed values. Use the day's running totals or means, the same as the daily records."""
    date: Day | None = Field(default=None, description="Defaults to today (Asia/Kolkata)")
    soil_moisture_pct: float = Field(ge=0, le=100)
    air_temperature_c: float = Field(ge=-20, le=60)
    humidity_pct: float = Field(ge=0, le=100)
    sunlight_wm2: float | None = Field(default=None, ge=0, le=500)
    rainfall_mm: float = Field(ge=0, le=1000, description="Rain so far today, mm")


class PredictRequest(BaseModel):
    device_id: str = Field(min_length=1, max_length=64)
    lat: float = Field(ge=6, le=38)
    lon: float = Field(ge=68, le=98)
    target_date: Day | None = None
    history: list[DayRecord] = Field(min_length=MIN_HISTORY_DAYS)
    current: CurrentReading | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "device_id": "sample-device",
                    "location": "Vijayawada",
                    "lat": 16.51,
                    "lon": 80.52,
                    "target_date": "2000-01-09",
                    "history": [
                        {"date": "2000-01-01", "soil_moisture_pct": 30, "sunlight_wm2": 186.34, "rainfall_mm": 0, "leaf_wet_days": 0},
                        {"date": "2000-01-02", "soil_moisture_pct": 30, "sunlight_wm2": 183.68, "rainfall_mm": 0, "leaf_wet_days": 0},
                        {"date": "2000-01-03", "soil_moisture_pct": 29, "sunlight_wm2": 187.27, "rainfall_mm": 0, "leaf_wet_days": 0},
                        {"date": "2000-01-04", "soil_moisture_pct": 28, "sunlight_wm2": 193.17, "rainfall_mm": 0, "leaf_wet_days": 0},
                        {"date": "2000-01-05", "soil_moisture_pct": 28, "sunlight_wm2": 212.04, "rainfall_mm": 0, "leaf_wet_days": 0},
                        {"date": "2000-01-06", "soil_moisture_pct": 27, "sunlight_wm2": 215.51, "rainfall_mm": 0, "leaf_wet_days": 0},
                        {"date": "2000-01-07", "soil_moisture_pct": 26, "sunlight_wm2": 207.41, "rainfall_mm": 0, "leaf_wet_days": 0},
                        {"date": "2000-01-08", "soil_moisture_pct": 26, "sunlight_wm2": 220.25, "rainfall_mm": 0, "leaf_wet_days": 0},
                    ],
                }
            ]
        }
    }

    @field_validator("history")
    @classmethod
    def validate_history_dates(cls, history: list[DayRecord]) -> list[DayRecord]:
        dates = [record.date for record in history]
        if len(set(dates)) != len(dates):
            raise ValueError("history has duplicate dates")
        if any(current != previous + timedelta(days=1) for previous, current in zip(dates, dates[1:])):
            raise ValueError("history must contain consecutive dates")
        return history


class HistoryError(Exception):
    def __init__(self, code: str, message: str, status: int = 422):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def error_body(code: str, message: str, details=None) -> dict:
    err = {"code": code, "message": message}
    if details is not None:
        err["details"] = details
    return {"schema_version": SCHEMA_VERSION, "error": err}


# ---------- loading ----------

def load_bundle() -> dict:
    bundle = joblib.load(MODEL_PATH)
    if list(bundle["features"]) != FEATURES:
        raise RuntimeError("model features do not match backend.FEATURES; retrain the model")
    return bundle


def load_static() -> dict:
    df = pd.read_csv(STATIC_PATH)
    return {(round(r["lat"], 2), round(r["lon"], 2)): r for r in df.to_dict("records")}


# ---------- merge and predict ----------

def merge_inputs(req: PredictRequest, static: dict, today: Day):
    """Returns (combined DataFrame of prior days + sensed day, warnings)."""
    key = (round(req.lat, 2), round(req.lon, 2))
    if key not in static:
        raise HistoryError("unknown_location", f"no trained point at lat={req.lat}, lon={req.lon}", 404)
    table = static[key]
    warnings = []

    rows = []
    for r in req.history:
        row = {"date": pd.Timestamp(r.date), "lat": key[0], "lon": key[1],
               "soil_moisture_pct": r.soil_moisture_pct, "air_temperature_c": r.air_temperature_c,
               "humidity_pct": r.humidity_pct, "sunlight_wm2": r.sunlight_wm2, "rainfall_mm": r.rainfall_mm,
               "source": "history"}
        for c in RECORD_STATIC:
            v = getattr(r, c)
            if v is None:
                row[c] = table[c]
            else:
                row[c] = v
                if abs(v - table[c]) > 1e-6:
                    warnings.append(f"{c} on {r.date} differs from the static table; the sent value was used")
        rows.append(row)

    if req.current is not None:
        cur = req.current
        # No date sent: the reading follows the last history day, so the sensor needn't know the clock
        cur_date = pd.Timestamp(cur.date) if cur.date else max(pd.Timestamp(r.date) for r in req.history) + pd.Timedelta(days=1)
        rows.append({"date": cur_date, "lat": key[0], "lon": key[1],
                     "soil_moisture_pct": cur.soil_moisture_pct, "air_temperature_c": cur.air_temperature_c,
                     "humidity_pct": cur.humidity_pct, "sunlight_wm2": cur.sunlight_wm2,
                     "rainfall_mm": cur.rainfall_mm, "source": "sensed", **{c: table[c] for c in RECORD_STATIC}})

    hist = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    if hist["date"].duplicated().any():
        raise HistoryError("invalid_history", "history and current reading have duplicate dates")
    if hist["date"].diff().dropna().ne(pd.Timedelta(days=1)).any():
        raise HistoryError("invalid_history", "records must be consecutive days with no gaps")

    last = hist["date"].iloc[-1]
    target = pd.Timestamp(req.target_date) if req.target_date else last + pd.Timedelta(days=1)
    if last != target - pd.Timedelta(days=1):
        raise HistoryError("invalid_history", "the last record must be the day before target_date")
    return hist, target, key, table, warnings


def run_prediction(req: PredictRequest, bundle: dict, static: dict, today: Day) -> dict:
    hist, target, key, table, warnings = merge_inputs(req, static, today)

    target_row = {"date": target, "lat": key[0], "lon": key[1], **{c: table[c] for c in RECORD_STATIC},
                  **{c: np.nan for c in DYNAMIC}, "source": "target"}
    feats = add_features(pd.concat([hist, pd.DataFrame([target_row])], ignore_index=True))
    row = feats[feats["date"] == target]

    missing = [f for f in FEATURES if pd.isna(row[f].iloc[0])]
    if missing:
        raise HistoryError("missing_values",
                           f"cannot build features; missing: {', '.join(missing)}. "
                           "Send a sunlight value for the most recent day.")

    pred = float(np.clip(bundle["model"].predict(row[FEATURES])[0], 0, 100))
    sun_gaps = hist.loc[hist["sunlight_wm2"].isna(), "date"].dt.date.astype(str).tolist()
    if sun_gaps:
        warnings.append(f"sunlight missing for {', '.join(sun_gaps)}; the model needs it for the day before target")

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(IST).replace(microsecond=0).isoformat(),
        "device_id": req.device_id,
        "location": {"lat": key[0], "lon": key[1]},
        "target_date": target.date().isoformat(),
        "prediction": {
            "risk_pct": round(pred, 2),
            "risk_label": risk_label(pred),
            "risk_bands": {"low_max": RISK_LOW_MAX, "moderate_max": RISK_MODERATE_MAX},
            "index_type": INDEX_TYPE,
            "validated": False,
        },
        "model": {"name": bundle["selected_model"], "trained_through": bundle["trained_through"]},
        "inputs": [{
            "date": r.date.date().isoformat(),
            "source": r.source,
            **{c: (None if pd.isna(getattr(r, c)) else float(getattr(r, c))) for c in DYNAMIC},
        } for r in hist.itertuples()],
        "warnings": warnings,
    }


# ---------- app ----------

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.bundle = load_bundle()    # fails at startup if the model is missing or mismatched
    app.state.static = load_static()
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
            "model": {"name": b["selected_model"], "trained_through": b["trained_through"]},
            "points": len(request.app.state.static)}


@app.get("/locations")
def locations(request: Request):
    """List the coordinate points for which static model soil features are available."""
    points = [
        {"lat": lat, "lon": lon}
        for lat, lon in sorted(request.app.state.static.keys())
    ]
    return {"locations": points}


@app.post("/predict")
def predict(req: PredictRequest, request: Request):
    today = datetime.now(IST).date()
    try:
        return run_prediction(req, request.app.state.bundle, request.app.state.static, today)
    except HistoryError as e:
        return JSONResponse(status_code=e.status, content=error_body(e.code, e.message))
