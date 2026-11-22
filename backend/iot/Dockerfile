FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
# Note: no ESP32 over USB inside a cloud container; use /api/sensors/simulate or
# run the backend on the PC the ESP32 is plugged into.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
