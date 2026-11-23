from __future__ import annotations

import argparse

from langchain_mongodb import MongoDBAtlasVectorSearch

try:
    from .config import (
        EMBEDDING_MODEL,
        MONGODB_DATABASE,
        MONGODB_COLLECTION,
        MONGODB_VECTOR_INDEX,
        mongodb_uri,
    )
except ImportError:
    from config import (
        EMBEDDING_MODEL,
        MONGODB_DATABASE,
        MONGODB_COLLECTION,
        MONGODB_VECTOR_INDEX,
        mongodb_uri,
    )

try:
    from .embeddings import FastEmbedEmbeddings
except ImportError:
    from embeddings import FastEmbedEmbeddings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--k", type=int, default=4)
    parser.add_argument("--collection")
    args = parser.parse_args()
    embeddings = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)
    store = MongoDBAtlasVectorSearch.from_connection_string(
        connection_string=mongodb_uri(),
        namespace=f"{MONGODB_DATABASE}.{args.collection or MONGODB_COLLECTION}",
        embedding=embeddings,
        index_name=MONGODB_VECTOR_INDEX,
        text_key="text",
        embedding_key="embedding",
    )
    for rank, (doc, distance) in enumerate(store.similarity_search_with_score(args.question, k=args.k), 1):
        metadata = doc.metadata
        nested = metadata.get("metadata", {})
        if isinstance(nested, dict):
            metadata = nested
        print(
            f"[{rank}] DOC_ID={metadata.get('doc_id','unknown')} "
            f"SECTION={metadata.get('section','unknown')} "
            f"FILE={metadata.get('filename','unknown')} "
            f"distance={distance:.4f}"
        )
        print(doc.page_content)


if __name__ == "__main__":
    main()
