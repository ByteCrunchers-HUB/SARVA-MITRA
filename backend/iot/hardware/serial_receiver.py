"""
Non-blocking Python Serial Receiver for ESP32 hardware communication using PySerial.
Continuously reads JSON packets, validates them, and stores the latest readings safely.
Supports cloud/headless environments gracefully where no local hardware COM port exists.
"""

import asyncio
import json
import logging
import sys
import serial
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from schemas.sensor_schema import ESP32SensorReading
from utils.validation import validate_sensor_ranges

logger = logging.getLogger("smartfarm.serial")


class SerialReceiver:
    """
    Background worker that monitors USB Serial port for incoming ESP32 sensor telemetry.
    Ensures the FastAPI main event loop is never blocked by serial I/O.
    """

    def __init__(self, port: str = "COM9", baudrate: int = 115200, enabled: bool = True):
        self.port = port
        self.baudrate = baudrate
        self.enabled = enabled
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._latest_reading: Optional[Dict[str, Any]] = None
        self._lock = asyncio.Lock()
        self._connected = False
        self._last_error: Optional[str] = None
        self._missing_port_logged = False

    async def start(self):
        """Starts the background reading loop if enabled."""
        if not self.enabled or self.port.lower() in ("none", "disabled", "false", ""):
            logger.info("Serial receiver is disabled (cloud/server mode). Accepting readings via HTTP API.")
            return

        # Check for Windows COM port on Linux/cloud host
        if sys.platform != "win32" and self.port.upper().startswith("COM"):
            logger.info(
                "Detected cloud/Linux host with Windows port name '%s'. "
                "Serial port disabled in cloud environment. Telemetry can be submitted via POST /api/sensors/data.",
                self.port
            )
            return

        if self.is_running:
            logger.warning("Serial receiver already active.")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._read_loop())
        logger.info("Serial receiver service started on %s @ %s baud", self.port, self.baudrate)

    async def stop(self):
        """Stops the serial receiver background task."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._connected = False
        logger.info("Serial receiver service stopped.")

    async def get_latest_reading(self) -> Optional[Dict[str, Any]]:
        """Returns the most recent validated sensor reading."""
        async with self._lock:
            return self._latest_reading.copy() if self._latest_reading else None

    def is_connected(self) -> bool:
        """Returns True if the serial connection is currently open and communicating."""
        return self._connected

    async def update_reading(self, reading: Dict[str, Any]):
        """Sets or updates the latest reading (used by HTTP ingest, forwarder, or testing)."""
        async with self._lock:
            self._latest_reading = reading

    async def set_reading_for_testing(self, reading: Dict[str, Any]):
        """Helper alias for updating readings."""
        await self.update_reading(reading)

    async def _read_loop(self):
        """
        Continuous non-blocking serial reading loop.
        Catches disconnection and auto-retries. Backs off cleanly if port does not exist on host.
        """
        loop = asyncio.get_running_loop()

        while self.is_running:
            ser = None
            try:
                if not self._missing_port_logged:
                    logger.info("Attempting to connect to ESP32 on port %s...", self.port)

                ser = await loop.run_in_executor(
                    None,
                    lambda: serial.Serial(
                        port=self.port,
                        baudrate=self.baudrate,
                        timeout=1.0
                    )
                )
                self._connected = True
                self._last_error = None
                self._missing_port_logged = False
                logger.info("Connected to ESP32 on %s successfully.", self.port)

                # Reading loop
                while self.is_running:
                    raw_line = await loop.run_in_executor(None, ser.readline)
                    if not raw_line:
                        await asyncio.sleep(0.05)
                        continue

                    try:
                        line_str = raw_line.decode("utf-8", errors="ignore").strip()
                        if not line_str or not (line_str.startswith("{") and line_str.endswith("}")):
                            continue

                        data = json.loads(line_str)

                        # Validate with Pydantic model
                        parsed = ESP32SensorReading(**data)

                        # Validate physical sensor value boundaries
                        valid, errors = validate_sensor_ranges(
                            parsed.temperature,
                            parsed.humidity,
                            parsed.soil_moisture
                        )

                        if not valid:
                            logger.warning("ESP32 reading failed range validation: %s", errors)
                            continue

                        # Update latest reading
                        reading_dict = {
                            "device_id": parsed.device_id,
                            "temperature": parsed.temperature,
                            "humidity": parsed.humidity,
                            "soil_moisture": parsed.soil_moisture,
                            "timestamp": parsed.timestamp or datetime.now(timezone.utc).isoformat()
                        }

                        async with self._lock:
                            self._latest_reading = reading_dict

                        logger.debug("Valid ESP32 reading received: %s", reading_dict)

                    except (json.JSONDecodeError, ValueError) as err:
                        logger.warning("Ignored invalid serial frame: %s (Error: %s)", raw_line, err)
                    except Exception as err:
                        logger.error("Unexpected error processing serial line: %s", err)

            except (serial.SerialException, FileNotFoundError, OSError) as se:
                self._connected = False
                err_str = str(se)

                # Check if port doesn't exist on this machine (e.g. running on Linux cloud without USB)
                if "No such file or directory" in err_str or "could not open port" in err_str:
                    if not self._missing_port_logged:
                        logger.warning(
                            "Serial port %s is not available on this host: %s. "
                            "If running in cloud (Render), this is normal — send telemetry via POST /api/sensors/data.",
                            self.port, err_str
                        )
                        self._missing_port_logged = True
                    # Back off to avoid spamming the log
                    await asyncio.sleep(30)
                else:
                    logger.warning("Serial connection error on %s: %s. Retrying in 5 seconds...", self.port, se)
                    await asyncio.sleep(5)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._connected = False
                logger.error("Unexpected error in serial receiver: %s. Retrying in 5s...", e)
                await asyncio.sleep(5)
            finally:
                if ser and ser.is_open:
                    try:
                        ser.close()
                    except Exception:
                        pass
                self._connected = False
