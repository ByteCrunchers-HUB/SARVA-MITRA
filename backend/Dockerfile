FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy repository
COPY . .

ENV PYTHONUNBUFFERED=1
ENV SARVA_MODEL_PATH=backend/ml_engine/models/sarva_mitra_risk_model.joblib

EXPOSE 8000

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:${PORT:-8000}/api/health || exit 1

# Launch Unified FastAPI backend bound to Render dynamic port
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
