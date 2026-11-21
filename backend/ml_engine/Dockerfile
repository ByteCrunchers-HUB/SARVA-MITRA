FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend.py .
COPY models/ models/
ENV SARVA_MODEL_PATH=models/sarva_mitra_risk_model.joblib
EXPOSE 8000
CMD ["sh", "-c", "uvicorn backend:app --host 0.0.0.0 --port ${PORT:-8000}"]