"""
Asynchronous SQLite database initialization and connection management using aiosqlite.
"""

import os
import logging
from contextlib import asynccontextmanager

import aiosqlite

logger = logging.getLogger("smartfarm.database")

DB_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "smartfarm.db")


@asynccontextmanager
async def get_db_connection():
    """
    Async context manager that opens a SQLite connection with row_factory set.

    Usage (NO `await` in front):
        async with get_db_connection() as db:
            cursor = await db.execute("SELECT * FROM daily_records")
            rows = await cursor.fetchall()
    """
    async with aiosqlite.connect(DB_FILE_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db() -> None:
    """
    Initializes SQLite database tables.
    Creates daily_records table with a UNIQUE constraint on (device_id, date)
    to strictly prevent accidental duplicate daily records.
    """
    logger.info("Initializing SQLite database at %s", DB_FILE_PATH)
    async with get_db_connection() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                date TEXT NOT NULL,
                temperature REAL,
                humidity REAL,
                soil_moisture REAL,
                rainfall_mm REAL DEFAULT 0.0,
                sunlight_wm2 REAL DEFAULT 0.0,
                leaf_wet_days INTEGER DEFAULT 0,
                is_duplicated INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(device_id, date)
            )
        """)
        await db.commit()
    logger.info("Database table 'daily_records' ready.")
