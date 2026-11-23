from __future__ import annotations

import os

from fastembed import TextEmbedding
from langchain_core.embeddings import Embeddings


class FastEmbedEmbeddings(Embeddings):
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        cache_dir: str | None = None,
    ) -> None:
        self.model = TextEmbedding(
            model_name=model_name,
            cache_dir=cache_dir or os.getenv("FASTEMBED_CACHE_PATH", "/tmp/.fastembed-cache"),
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self.model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return next(self.model.embed([text])).tolist()
