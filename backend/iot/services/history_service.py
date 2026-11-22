"""
Historical data preparation service.
Extracts consecutive daily records from the database and constructs the exact 8-record history
required by the ML Engine, incorporating the deterministic duplication strategy when enabled.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from config import settings
from database.sensor_repository import get_records_for_ml
from schemas.ml_schema import MLHistoryRecord

logger = logging.getLogger("smartfarm.history")


async def prepare_ml_history(device_id: str, target_date: str) -> List[MLHistoryRecord]:
    """
    Prepares exactly 8 consecutive daily records up to target_date for the ML Engine.
    
    Rules:
    - If 8+ records exist: selects the last 8 chronologically.
    - If fewer than 8 records exist and ALLOW_DUPLICATE_HISTORY=True:
        Deterministically duplicates available records and assigns synthetic sequential
        dates backwards so that ML receives an array of exactly 8 chronologically ordered records.
        Logs every duplicated record.
    - If fewer than 8 records exist and ALLOW_DUPLICATE_HISTORY=False:
        Raises ValueError explaining that real history is insufficient.
    """
    records = await get_records_for_ml(device_id=device_id, end_date=target_date, limit=8)

    if not records:
        raise ValueError(
            f"No historical records found for device '{device_id}' up to {target_date}. "
            "Please record at least one sensor reading before running ML prediction."
        )

    count = len(records)
    logger.info("Found %d historical records in database for device %s up to %s", count, device_id, target_date)

    if count == 8:
        # We have exactly 8 genuine records
        logger.info("Retrieved complete 8-day genuine historical dataset.")
        return [_to_ml_history_record(r) for r in records]

    # Handle insufficient records (< 8)
    if not settings.allow_duplicate_history:
        raise ValueError(
            f"Insufficient history: Found {count} records, but ML engine strictly requires 8. "
            "ALLOW_DUPLICATE_HISTORY is set to false. Historical duplication is disabled."
        )

    # Strategy: Deterministic duplication to fill the 8 slots
    logger.warning(
        "TEMPORARY TESTING MODE: Found only %d records for device %s. "
        "Deterministically duplicating records to meet the strict 8-record ML engine requirement.",
        count, device_id
    )

    needed = 8 - count
    # Earliest date in existing records
    earliest_dt = datetime.strptime(records[0]["date"], "%Y-%m-%d")

    # Generate synthetic historical dates counting backwards from earliest real date
    duplicated_records: List[Dict[str, Any]] = []
    for i in range(needed):
        # Deterministically repeat available records in round-robin fashion
        source_record = records[i % count]
        synth_date = (earliest_dt - timedelta(days=needed - i)).strftime("%Y-%m-%d")

        synth_record = {
            "date": synth_date,
            "soil_moisture": source_record.get("soil_moisture", 0.0),
            "sunlight_wm2": source_record.get("sunlight_wm2", 0.0),
            "rainfall_mm": source_record.get("rainfall_mm", 0.0),
            "leaf_wet_days": source_record.get("leaf_wet_days", 0),
            "is_duplicated": True
        }
        duplicated_records.append(synth_record)
        logger.debug(
            "Synthesized duplicate history record: date=%s (copied from source date %s)",
            synth_date, source_record["date"]
        )

    # Combine: [duplicated (older dates)] + [real records]
    combined = duplicated_records + records

    # Ensure final count is exactly 8
    final_records = combined[-8:]
    return [_to_ml_history_record(r) for r in final_records]


def _to_ml_history_record(record: Dict[str, Any]) -> MLHistoryRecord:
    """Converts a database row or dictionary into an MLHistoryRecord Pydantic model."""
    return MLHistoryRecord(
        date=record["date"],
        soil_moisture_pct=float(record.get("soil_moisture", 0.0) or 0.0),
        sunlight_wm2=float(record.get("sunlight_wm2", 0.0) or 0.0),
        rainfall_mm=float(record.get("rainfall_mm", 0.0) or 0.0),
        leaf_wet_days=int(record.get("leaf_wet_days", 0) or 0)
    )
