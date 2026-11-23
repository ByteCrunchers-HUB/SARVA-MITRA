"""
Historical data preparation service.
Extracts consecutive daily records from the database and constructs the history
required by the ML Engine and RAG Pipeline, incorporating the deterministic duplication strategy when needed.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from config import settings
from database.sensor_repository import get_records_for_ml
from schemas.ml_schema import MLDayRecord
from schemas.rag_schema import RAGHistoryRecord

logger = logging.getLogger("smartfarm.history")


async def prepare_ml_history(device_id: str, target_date: str) -> List[MLDayRecord]:
    """
    Prepares at least 7 consecutive daily records up to target_date for the ML Engine.
    Conforms to the DayRecord schema: date, soil_moisture_pct, air_temperature_c, humidity_pct, sunlight_wm2, rainfall_mm.
    """
    records = await get_records_for_ml(device_id=device_id, end_date=target_date, limit=8)

    if not records:
        raise ValueError(
            f"No historical records found for device '{device_id}' up to {target_date}. "
            "Please record at least one sensor reading before running ML prediction."
        )

    count = len(records)
    logger.info("Found %d historical records in database for device %s up to %s", count, device_id, target_date)

    if count >= 7:
        return [_to_ml_day_record(r) for r in records[-7:]]

    # Handle insufficient records (< 7)
    if not settings.allow_duplicate_history:
        raise ValueError(
            f"Insufficient history: Found {count} records, but ML engine strictly requires at least 7. "
            "ALLOW_DUPLICATE_HISTORY is set to false."
        )

    logger.warning(
        "TEMPORARY TESTING MODE: Found only %d records for device %s. "
        "Deterministically duplicating records to meet the 7-record ML requirement.",
        count, device_id
    )

    needed = 7 - count
    earliest_dt = datetime.strptime(records[0]["date"], "%Y-%m-%d")

    duplicated_records: List[Dict[str, Any]] = []
    for i in range(needed):
        source_record = records[i % count]
        synth_date = (earliest_dt - timedelta(days=needed - i)).strftime("%Y-%m-%d")

        synth_record = {
            "date": synth_date,
            "soil_moisture": source_record.get("soil_moisture", 45.0),
            "temperature": source_record.get("temperature", 28.0),
            "humidity": source_record.get("humidity", 60.0),
            "sunlight_wm2": source_record.get("sunlight_wm2", 200.0),
            "rainfall_mm": source_record.get("rainfall_mm", 0.0),
            "is_duplicated": True
        }
        duplicated_records.append(synth_record)

    combined = duplicated_records + records
    return [_to_ml_day_record(r) for r in combined[-7:]]


def _to_ml_day_record(record: Dict[str, Any]) -> MLDayRecord:
    """Converts a database row or dictionary into an MLDayRecord Pydantic model."""
    return MLDayRecord(
        date=record["date"],
        soil_moisture_pct=float(record.get("soil_moisture", 45.0) or 45.0),
        air_temperature_c=float(record.get("temperature", 28.0) or 28.0),
        humidity_pct=float(record.get("humidity", 60.0) or 60.0),
        sunlight_wm2=float(record.get("sunlight_wm2", 200.0) or 200.0),
        rainfall_mm=float(record.get("rainfall_mm", 0.0) or 0.0)
    )


def to_rag_history(ml_history: List[MLDayRecord]) -> List[RAGHistoryRecord]:
    """Converts MLDayRecords into RAGHistoryRecords for the RAG API."""
    return [
        RAGHistoryRecord(
            date=r.date,
            soil_moisture_pct=r.soil_moisture_pct,
            sunlight_wm2=r.sunlight_wm2,
            rainfall_mm=r.rainfall_mm,
            leaf_wet_days=1 if r.rainfall_mm > 0.0 else 0
        )
        for r in ml_history
    ]
