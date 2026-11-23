FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV FASTEMBED_CACHE_PATH=/app/.fastembed-cache
RUN python -c "from fastembed import TextEmbedding; model=TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2', cache_dir='/app/.fastembed-cache'); list(model.embed(['warmup']))"

COPY __init__.py ./rag_pipeline/__init__.py
COPY app.py ./rag_pipeline/app.py
COPY config.py ./rag_pipeline/config.py
COPY rag.py ./rag_pipeline/rag.py
COPY embeddings.py ./rag_pipeline/embeddings.py
COPY ingest.py ./rag_pipeline/ingest.py
COPY query.py ./rag_pipeline/query.py
COPY main.py ./rag_pipeline/main.py
COPY docs ./rag_pipeline/docs

ENV PYTHONUNBUFFERED=1
ENV RAG_API_HOST=0.0.0.0
ENV HF_HOME=/tmp/huggingface
ENV TRANSFORMERS_CACHE=/tmp/huggingface
ENV SENTENCE_TRANSFORMERS_HOME=/tmp/huggingface

EXPOSE 8001

CMD ["sh", "-c", "python -m uvicorn rag_pipeline.main:app --host 0.0.0.0 --port ${PORT:-8001}"]
