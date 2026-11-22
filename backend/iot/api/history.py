"""
Historical database query endpoints.
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from config import settings
from database.sensor_repository import get_records_by_device, upsert_daily_record
from schemas.sensor_schema import DailyUnifiedRecord
from services.history_service import prepare_ml_history
from utils.validation import validate_date_format

router = APIRouter(prefix="/history", tags=["History"])


@router.get("", summary="Get historical daily records for a device")
async def get_history(
    device_id: Optional[str] = Query(None, description="ESP32 Device ID (defaults to .env setting)"),
    limit: int = Query(30, ge=1, le=365, description="Maximum number of historical records to retrieve")
):
    """
    Returns stored daily aggregated sensor and weather measurements.
    """
    dev_id = device_id or settings.device_id
    records = await get_records_by_device(dev_id, limit=limit)

    return {
        "status": "success",
        "device_id": dev_id,
        "count": len(records),
        "records": records
    }


@router.post("/record", summary="Manually add or update a daily historical record")
async def save_record(record: DailyUnifiedRecord):
    """
    Saves or updates a daily record in SQLite.
    Useful for populating historical training/testing data.
    """
    if not validate_date_format(record.date):
        raise HTTPException(status_code=400, detail="Date must follow YYYY-MM-DD format.")

    success = await upsert_daily_record(
        device_id=record.device_id,
        date=record.date,
        temperature=record.temperature,
        humidity=record.humidity,
        soil_moisture=record.soil_moisture,
        rainfall_mm=record.rainfall_mm or 0.0,
        sunlight_wm2=record.sunlight_wm2 or 0.0,
        leaf_wet_days=record.leaf_wet_days or 0,
        is_duplicated=record.is_duplicated
    )

    if not success:
        raise HTTPException(status_code=500, detail="Database write operation failed.")

    return {
        "status": "success",
        "message": f"Record for {record.device_id} on {record.date} saved successfully."
    }


@router.get("/ml-preview", summary="Preview the 8-day array prepared for the ML Engine")
async def preview_ml_history(
    device_id: Optional[str] = Query(None, description="Device ID (defaults to .env setting)"),
    target_date: Optional[str] = Query(None, description="Prediction target date (YYYY-MM-DD)")
):
    """
    Shows exactly what 8-record history will be sent to the independent ML Engine.
    Demonstrates deterministic duplication when fewer than 8 unique dates exist.
    """
    dev_id = device_id or settings.device_id
    t_date = target_date or date.today().strftime("%Y-%m-%d")

    if not validate_date_format(t_date):
        raise HTTPException(status_code=400, detail="Date must follow YYYY-MM-DD format.")

    try:
        history_records = await prepare_ml_history(dev_id, t_date)
        return {
            "status": "success",
            "device_id": dev_id,
            "target_date": t_date,
            "record_count": len(history_records),
            "history": [r.model_dump() for r in history_records]
        }
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))
