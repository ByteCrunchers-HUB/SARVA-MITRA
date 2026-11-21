FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./rag_pipeline

ENV PYTHONUNBUFFERED=1
ENV RAG_API_HOST=0.0.0.0

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "rag_pipeline.main:app", "--host", "0.0.0.0", "--port", "8001"]
