"""
Repository layer providing data access operations for daily sensor and weather records.
"""

import logging
from typing import List, Optional, Dict, Any
from database.database import get_db_connection

logger = logging.getLogger("smartfarm.repository")


async def upsert_daily_record(
    device_id: str,
    date: str,
    temperature: Optional[float] = None,
    humidity: Optional[float] = None,
    soil_moisture: Optional[float] = None,
    rainfall_mm: float = 0.0,
    sunlight_wm2: float = 0.0,
    leaf_wet_days: int = 0,
    is_duplicated: bool = False
) -> bool:
    """
    Inserts or updates a daily aggregated record for a device on a specific date.
    Uses INSERT OR REPLACE to uphold the UNIQUE(device_id, date) constraint.
    """
    try:
        async with get_db_connection() as db:
            await db.execute("""
                INSERT INTO daily_records (
                    device_id, date, temperature, humidity, soil_moisture,
                    rainfall_mm, sunlight_wm2, leaf_wet_days, is_duplicated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(device_id, date) DO UPDATE SET
                    temperature = COALESCE(excluded.temperature, daily_records.temperature),
                    humidity = COALESCE(excluded.humidity, daily_records.humidity),
                    soil_moisture = COALESCE(excluded.soil_moisture, daily_records.soil_moisture),
                    rainfall_mm = excluded.rainfall_mm,
                    sunlight_wm2 = excluded.sunlight_wm2,
                    leaf_wet_days = excluded.leaf_wet_days,
                    is_duplicated = excluded.is_duplicated
            """, (
                device_id,
                date,
                temperature,
                humidity,
                soil_moisture,
                rainfall_mm,
                sunlight_wm2,
                leaf_wet_days,
                1 if is_duplicated else 0
            ))
            await db.commit()
            logger.info("Successfully upserted record for device %s on %s", device_id, date)
            return True
    except Exception as e:
        logger.error("Failed to upsert daily record for %s on %s: %s", device_id, date, e)
        return False


async def get_records_by_device(device_id: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Retrieves up to `limit` stored historical records for a device, ordered newest first."""
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT id, device_id, date, temperature, humidity, soil_moisture,
                   rainfall_mm, sunlight_wm2, leaf_wet_days, is_duplicated, created_at
            FROM daily_records
            WHERE device_id = ?
            ORDER BY date DESC
            LIMIT ?
        """, (device_id, limit))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_records_for_ml(device_id: str, end_date: str, limit: int = 8) -> List[Dict[str, Any]]:
    """
    Retrieves up to `limit` records on or before `end_date`, sorted in chronological order (oldest first).
    """
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT id, device_id, date, temperature, humidity, soil_moisture,
                   rainfall_mm, sunlight_wm2, leaf_wet_days, is_duplicated, created_at
            FROM daily_records
            WHERE device_id = ? AND date <= ?
            ORDER BY date DESC
            LIMIT ?
        """, (device_id, end_date, limit))
        rows = await cursor.fetchall()
        # Convert to dict and sort chronologically (oldest -> newest)
        records = [dict(row) for row in rows]
        records.reverse()
        return records


async def get_record_by_date(device_id: str, date: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single record by device and date."""
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT id, device_id, date, temperature, humidity, soil_moisture,
                   rainfall_mm, sunlight_wm2, leaf_wet_days, is_duplicated, created_at
            FROM daily_records
            WHERE device_id = ? AND date = ?
        """, (device_id, date))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def count_records(device_id: str) -> int:
    """Returns the total number of recorded days for a device."""
    async with get_db_connection() as db:
        cursor = await db.execute("""
            SELECT COUNT(*) as count FROM daily_records WHERE device_id = ?
        """, (device_id,))
        row = await cursor.fetchone()
        return row["count"] if row else 0
