"""
Non-blocking Python Serial Receiver for ESP32 hardware communication using PySerial.
Continuously reads JSON packets, validates them, and stores the latest readings safely.
"""

import asyncio
import json
import logging
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

    def __init__(self, port: str = "COM9", baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._latest_reading: Optional[Dict[str, Any]] = None
        self._lock = asyncio.Lock()
        self._connected = False
        self._last_error: Optional[str] = None

    async def start(self):
        """Starts the background reading loop."""
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

    async def set_reading_for_testing(self, reading: Dict[str, Any]):
        """Helper to inject simulated readings during testing or when hardware is not plugged in."""
        async with self._lock:
            self._latest_reading = reading

    async def _read_loop(self):
        """
        Continuous non-blocking serial reading loop.
        Catches disconnection and auto-retries every 5 seconds.
        """
        loop = asyncio.get_running_loop()

        while self.is_running:
            ser = None
            try:
                logger.info("Attempting to connect to ESP32 on port %s...", self.port)
                # Open serial port in an executor thread to avoid blocking event loop
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
                logger.info("Connected to ESP32 on %s successfully.", self.port)

                # Reading loop
                while self.is_running:
                    # Read line in thread executor
                    raw_line = await loop.run_in_executor(None, ser.readline)
                    if not raw_line:
                        await asyncio.sleep(0.05)
                        continue

                    try:
                        line_str = raw_line.decode("utf-8", errors="ignore").strip()
                        if not line_str or not (line_str.startswith("{") and line_str.endswith("}")):
                            continue

                        data = json.loads(line_str)

                        # ESP32 reports sensor faults as JSON with an "error" key
                        if "error" in data:
                            logger.warning("ESP32 reported a sensor fault: %s", data.get("error"))
                            continue

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

            except serial.SerialException as se:
                self._connected = False
                msg = str(se)
                if msg != self._last_error:
                    logger.warning(
                        "Serial port %s unavailable: %s. Will keep retrying every 5s "
                        "(close Serial Monitor / check COM port).", self.port, msg
                    )
                    self._last_error = msg
                else:
                    logger.debug("Serial still unavailable on %s", self.port)
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
