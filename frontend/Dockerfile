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

# Expose Streamlit default port
EXPOSE 8501

ENV PYTHONUNBUFFERED=1
ENV SARVA_MODEL_PATH=backend/ml_engine/models/sarva_mitra_risk_model.joblib

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:${PORT:-8501}/_stcore/health || exit 1

# Launch Streamlit bound to Render dynamic port or 8501
CMD ["sh", "-c", "streamlit run frontend/app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false"]
