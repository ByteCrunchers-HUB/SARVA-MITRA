
FROM python:3.13-slim

WORKDIR /app

# Install OpenMP runtime required by LightGBM
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY backend.py .
COPY models/ models/

EXPOSE 10000

CMD ["sh", "-c", "uvicorn backend:app --host 0.0.0.0 --port ${PORT:-10000}"]
