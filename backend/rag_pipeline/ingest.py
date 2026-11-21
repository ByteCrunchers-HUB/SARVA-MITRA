from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import PurePosixPath

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from pymongo import MongoClient

try:
    from .config import (
        DOCS_DIR,
        EMBEDDING_MODEL,
        MONGODB_DATABASE,
        MONGODB_COLLECTION,
        mongodb_uri,
    )
except ImportError:
    from config import (
        DOCS_DIR,
        EMBEDDING_MODEL,
        MONGODB_DATABASE,
        MONGODB_COLLECTION,
        mongodb_uri,
    )


EXCLUDED = {"00_README_manifest", "01_dataset_columns_reference", "23_master_prompt"}
MARKER = "sarva-mitra-rag"


def load_documents() -> list[Document]:
    documents = []
    for path in sorted(DOCS_DIR.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".txt", ".md", ".pdf"}:
            doc_id = path.stem
            if doc_id not in EXCLUDED:
                if path.suffix.lower() == ".pdf":
                    from langchain_community.document_loaders import PyPDFLoader
                    documents.extend(PyPDFLoader(str(path)).load())
                else:
                    documents.append(Document(
                        page_content=path.read_text(encoding="utf-8"),
                        metadata={"source": str(path), "filename": path.name},
                    ))
    return documents


def parse_metadata(text: str, filename: str) -> dict:
    metadata = {
        "filename": filename,
        "source": filename,
        "doc_id": filename.rsplit(".", 1)[0],
        "parent_id": filename.rsplit(".", 1)[0],
        "section": "document",
        "kind": "parent",
        "embed": True,
        "crops": [],
    }
    for line in text.splitlines()[:12]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().upper()
        value = value.strip()
        if key == "DOC_ID":
            metadata["doc_id"] = value
            metadata["parent_id"] = value
        elif key == "TITLE":
            metadata["title"] = value
        elif key == "CROPS":
            metadata["crops"] = sorted({
                item.strip().lower()
                for item in re.split(r"[,\-/]", value)
                if item.strip()
            })
        elif key == "EMBED":
            metadata["embed"] = value.lower().startswith("yes")
    return metadata


def sections(text: str) -> list[tuple[str, str]]:
    output = []
    name = "HEADER"
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and stripped.upper() == stripped and len(stripped) <= 80:
            if lines:
                output.append((name, "\n".join(lines).strip()))
            name = stripped
            lines = []
        else:
            lines.append(line)
    if lines:
        output.append((name, "\n".join(lines).strip()))
    return [(name, content) for name, content in output if content]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--collection")
    args = parser.parse_args()

    documents = load_documents()
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        encode_kwargs={"normalize_embeddings": True},
        model_kwargs={"device": "cpu"},
    )
    parents = []
    children = []
    for document in documents:
        filename = PurePosixPath(document.metadata["source"]).name
        metadata = parse_metadata(document.page_content, filename)
        parents.append((document.page_content, metadata))
        if metadata["embed"]:
            for section_name, content in sections(document.page_content):
                children.append((f"{metadata.get('title', '')}\n{section_name}\n{content}",
                                 {**metadata, "kind": "child", "section": section_name}))

    vectors = embeddings.embed_documents([text for text, _ in children])
    records = [
        {"corpus": MARKER, "kind": "parent", "text": text, "metadata": metadata}
        for text, metadata in parents
    ]
    records.extend(
        {"corpus": MARKER, "kind": "child", "text": text, "embedding": vector,
         "metadata": metadata}
        for (text, metadata), vector in zip(children, vectors, strict=True)
    )

    with MongoClient(mongodb_uri()) as client:
        database = client[MONGODB_DATABASE]
        target = args.collection or (MONGODB_COLLECTION if args.apply else f"{MONGODB_COLLECTION}_staging")
        collection = database[target]
        collection.create_index("metadata.doc_id")
        backup = None
        if args.apply:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup = f"{target}_backup_{timestamp}"
            old = list(collection.find({}))
            if old:
                database[backup].insert_many(old)
        collection.delete_many({"corpus": MARKER})
        if records:
            collection.insert_many(records)
    print(f"Indexed {len(records)} records from {len(parents)} documents into {MONGODB_DATABASE}.{target}")
    if backup:
        print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
