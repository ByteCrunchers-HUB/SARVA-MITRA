from __future__ import annotations

import json
import re

from langchain_core.documents import Document
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from groq import APIError

try:
    from .config import (
        DOCS_DIR,
        EMBEDDING_MODEL,
        GROQ_API_KEY,
        GROQ_MODEL,
        MONGODB_DATABASE,
        MONGODB_COLLECTION,
        MONGODB_VECTOR_INDEX,
        mongodb_uri,
        RAG_USE_VECTOR_SEARCH,
        EMBEDDING_DIMENSION,
    )
except ImportError:
    from config import (
        DOCS_DIR,
        EMBEDDING_MODEL,
        EMBEDDING_DIMENSION,
        GROQ_API_KEY,
        GROQ_MODEL,
        MONGODB_DATABASE,
        MONGODB_COLLECTION,
        MONGODB_VECTOR_INDEX,
        mongodb_uri,
        RAG_USE_VECTOR_SEARCH,
    )

try:
    from .embeddings import FastEmbedEmbeddings
except ImportError:
    from embeddings import FastEmbedEmbeddings


_embeddings = None


def build_query(readings: dict, ml_output: int, crop: str, location: str, question: str) -> str:
    crop = crop if crop.lower() not in {"", "unknown"} else "unknown crop"
    parts = [
        f"ML output {ml_output}",
        f"crop: {crop}",
        f"location: {location}",
        f"sensor readings: {json.dumps(readings, ensure_ascii=False, sort_keys=True)}",
    ]
    if question.strip():
        parts.append(f"farmer question: {question.strip()}")
    return "; ".join(parts)


def metadata_value(metadata: dict, key: str, default=None):
    if key in metadata:
        return metadata[key]
    nested = metadata.get("metadata")
    return nested.get(key, default) if isinstance(nested, dict) else default


def parent_is_compatible(doc_id: str, text: str, crop: str) -> bool:
    if doc_id in {"02_weather_thresholds_by_disease", "21_soil_moisture_effects_by_disease",
                  "22_healthy_state_betterments", "24_field_hygiene"}:
        return True
    if crop.lower() in {"", "unknown"}:
        return True
    return crop.lower() in text.lower()


def crop_specific_parent_ids(crop: str) -> list[str]:
    crop_name = crop.lower()
    if "tomato" in crop_name:
        return [
            "tomato_field_checklist",
            "tomato_soil_moisture_bands",
            "tomato_nutrient_deficiencies",
            "tomato_blight_leafspot_comparison",
        ]
    if "chilli" in crop_name or "chili" in crop_name:
        return [
            "chilli_field_checklist",
            "chilli_soil_moisture_bands",
            "chilli_nutrient_deficiencies",
            "chilli_heat_stress",
            "chilli_viral_diseases",
            "chilli_wilt_damping_off",
            "chilli_bacterial_leaf_spot",
        ]
    if "ragi" in crop_name or "finger millet" in crop_name:
        return [
            "ragi_field_checklist",
            "ragi_soil_moisture_bands",
            "ragi_blast_detailed",
            "ragi_foliar_comparison",
        ]
    return []


class RAGPipeline:
    def __init__(self, collection_name: str | None = None) -> None:
        self.collection_name = collection_name
        self.last_retrieval = {"query": "", "matches": [], "documents_sent": []}
        self.embeddings = None
        if RAG_USE_VECTOR_SEARCH:
            global _embeddings
            if _embeddings is None:
                _embeddings = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)
            self.embeddings = _embeddings
        if not GROQ_API_KEY or "replace_with_" in GROQ_API_KEY:
            raise RuntimeError("Set GROQ_API_KEY in the root .env")
        from langchain_groq import ChatGroq
        self.llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0)
        self.master_prompt = (DOCS_DIR / "23_master_prompt.txt").read_text(encoding="utf-8")

    def retrieve(self, readings: dict, ml_output: int, crop: str, location: str, question: str) -> list[Document]:
        if not RAG_USE_VECTOR_SEARCH:
            raise RuntimeError("Vector search is disabled. Set RAG_USE_VECTOR_SEARCH=true")

        with MongoClient(
            mongodb_uri(),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
        ) as client:
            collection = client[MONGODB_DATABASE][self.collection_name or MONGODB_COLLECTION]
            child = collection.find_one({
                "corpus": "sarva-mitra-rag",
                "kind": "child",
            })
            if child:
                metadata = child.get("metadata", {})
                indexed_model = metadata.get("embedding_model")
                indexed_dimension = metadata.get("embedding_dimension")
                if indexed_model and indexed_model != EMBEDDING_MODEL:
                    raise RuntimeError(
                        f"Indexed with {indexed_model}, but runtime uses {EMBEDDING_MODEL}. Re-run ingest --apply"
                    )
                if indexed_dimension and indexed_dimension != EMBEDDING_DIMENSION:
                    raise RuntimeError(
                        f"Indexed at {indexed_dimension} dimensions, but runtime uses {EMBEDDING_DIMENSION}. Re-run ingest --apply"
                    )
            parent_ids: list[str] = []
            matches: list[dict] = []

            if ml_output == 0:
                parent_ids = [
                    "22_healthy_state_betterments",
                    "24_field_hygiene",
                    "21_soil_moisture_effects_by_disease",
                    "19_heat_stress_fruit_set_tomato",
                    "20_soil_salinity_ec_tomato",
                ]
                parent_ids.extend(crop_specific_parent_ids(crop))
            else:
                try:
                    from langchain_mongodb import MongoDBAtlasVectorSearch

                    namespace = f"{MONGODB_DATABASE}.{self.collection_name or MONGODB_COLLECTION}"
                    store = MongoDBAtlasVectorSearch.from_connection_string(
                        connection_string=mongodb_uri(),
                        namespace=namespace,
                        embedding=self.embeddings,
                        index_name=MONGODB_VECTOR_INDEX,
                        text_key="text",
                        embedding_key="embedding",
                    )
                    query = build_query(readings, ml_output, crop, location, question)
                    self.last_retrieval["query"] = query
                    excluded = {
                        "19_heat_stress_fruit_set_tomato",
                        "20_soil_salinity_ec_tomato",
                        "22_healthy_state_betterments",
                        "24_field_hygiene",
                    }
                    for rank, (doc, distance) in enumerate(
                        store.similarity_search_with_score(query, k=20),
                        start=1,
                    ):
                        parent_id = metadata_value(doc.metadata, "parent_id") or metadata_value(doc.metadata, "doc_id")
                        if not parent_id or parent_id in parent_ids or parent_id in excluded:
                            continue
                        crops = metadata_value(doc.metadata, "crops", [])
                        if crop.lower() not in {"", "unknown"} and isinstance(crops, list) and crops:
                            if not any(crop.lower() in str(value).lower() for value in crops):
                                continue
                        if not parent_is_compatible(parent_id, doc.page_content, crop):
                            continue
                        parent_ids.append(parent_id)
                        distance_float = float(distance) if isinstance(distance, (int, float)) else None
                        matches.append({
                            "rank": rank,
                            "doc_id": parent_id,
                            "parent_id": parent_id,
                            "filename": metadata_value(doc.metadata, "filename", "unknown"),
                            "section": metadata_value(doc.metadata, "section", "unknown"),
                            "retrieval_type": "vector_similarity",
                            "distance": distance_float,
                            "similarity_score": max(0.0, min(1.0, 1.0 - distance_float)) if distance_float is not None else None,
                        })
                        if len(parent_ids) >= 4:
                            break
                except (PyMongoError, OSError, RuntimeError, TimeoutError, ValueError) as exc:
                    raise RuntimeError(f"Vector retrieval failed: {exc}") from exc

                parent_ids.insert(0, "02_weather_thresholds_by_disease")
                if any(key in readings for key in ("soil_moisture_pct", "soil_moisture")):
                    parent_ids.append("21_soil_moisture_effects_by_disease")
                parent_ids.extend(crop_specific_parent_ids(crop))
                if "ragi" in crop.lower() or "finger millet" in crop.lower():
                    parent_ids.extend(["15_ragi_blast", "16_ragi_weather_uas_bengaluru_tables"])

            parents: list[Document] = []
            for doc_id in dict.fromkeys(parent_ids):
                record = collection.find_one({
                    "corpus": "sarva-mitra-rag",
                    "kind": "parent",
                    "metadata.doc_id": doc_id,
                })
                if record:
                    parents.append(Document(
                        page_content=record["text"],
                        metadata={**record["metadata"], "doc_id": doc_id},
                    ))

            parents = [
                doc for doc in parents
                if parent_is_compatible(doc.metadata["doc_id"], doc.page_content, crop)
            ]
            seen = {match["doc_id"] for match in matches}
            rank = len(matches) + 1
            for doc in parents:
                doc_id = doc.metadata["doc_id"]
                if doc_id not in seen:
                    matches.append({
                        "rank": rank,
                        "doc_id": doc_id,
                        "parent_id": doc_id,
                        "filename": doc.metadata.get("filename", "unknown"),
                        "section": "complete_parent",
                        "retrieval_type": "direct_required",
                        "distance": None,
                        "similarity_score": None,
                    })
                    rank += 1
                    seen.add(doc_id)
            self.last_retrieval["matches"] = matches
            self.last_retrieval["documents_sent"] = [
                {
                    "doc_id": doc.metadata["doc_id"],
                    "title": doc.metadata.get("title", "Unknown"),
                    "filename": doc.metadata.get("filename", "unknown"),
                    "section": "complete_parent",
                }
                for doc in parents
            ]
            return parents

    def answer(self, readings: dict, ml_output: int, crop: str, location: str,
               question: str, chat_history: list[dict], ml_prediction: dict) -> tuple[str, dict]:
        from langchain_core.messages import HumanMessage, SystemMessage
        documents = self.retrieve(readings, ml_output, crop, location, question)
        if not documents:
            raise RuntimeError("No relevant documents found")

        context_parts: list[str] = []
        remaining = 3200
        for doc in documents:
            text = doc.page_content[:900]
            block = (
                f"DOC_ID: {doc.metadata['doc_id']}\n"
                f"TITLE: {doc.metadata.get('title', 'Unknown')}\n"
                f"{text}"
            )
            if len(block) > remaining:
                block = block[:remaining]
            context_parts.append(block)
            remaining -= len(block)
            if remaining <= 0:
                break
        context = "\n\n".join(context_parts)
        history = "\n".join(
            f"{item['role'].upper()}: {item['content']}"
            for item in chat_history
        ) or "No previous conversation."
        human = (
            f"READINGS: {json.dumps(readings, ensure_ascii=False, sort_keys=True)}\n"
            f"ML_OUTPUT: {ml_output}\n"
            f"ML_PREDICTION: {json.dumps(ml_prediction, ensure_ascii=False, sort_keys=True)}\n"
            f"CROP: {crop}\nLOCATION: {location}\n"
            f"QUESTION: {question}\nPREVIOUS CHAT:\n{history}\n"
            f"RETRIEVED DOCUMENTS:\n{context}\n"
            "Return the human-readable advisory first, then exactly one JSON object "
            "marked BEGIN_STRUCTURED_JSON and END_STRUCTURED_JSON with keys "
            "response_mode, overview, model_interpretation, sensor_readings, "
            "possible_conditions, watch_list, recommendations, uncertainty, "
            "next_step, documents_used."
        )
        try:
            content = str(self.llm.invoke([
                SystemMessage(content=self.master_prompt),
                HumanMessage(content=human),
            ]).content)
        except APIError as exc:
            raise RuntimeError(f"Groq request failed: {exc}") from exc
        match = re.search(
            r"BEGIN_STRUCTURED_JSON\s*(\{[\s\S]*\})\s*END_STRUCTURED_JSON",
            content,
        )
        if not match:
            match = re.search(r"```json\s*(\{[\s\S]*\})\s*```", content)
        if match:
            try:
                structured = json.loads(match.group(1))
            except json.JSONDecodeError:
                structured = None
        else:
            structured = None
        if structured is None:
            structured = {
                "response_mode": "abnormality" if ml_output == 1 else "healthy",
                "overview": "Advice generated from retrieved documents.",
                "model_interpretation": "The model is a risk signal, not a diagnosis.",
                "sensor_readings": [],
                "possible_conditions": [],
                "watch_list": [],
                "recommendations": [],
                "uncertainty": ["Structured extraction was unavailable."],
                "next_step": "Inspect the plants and contact the local KVK or agriculture officer.",
                "documents_used": [doc.metadata["doc_id"] for doc in documents],
            }
        structured["response_mode"] = (
            "abnormality" if ml_output == 1 else "healthy"
        )
        answer = re.sub(
            r"\s*BEGIN_STRUCTURED_JSON\s*\{[\s\S]*\}\s*END_STRUCTURED_JSON\s*$",
            "",
            content,
        ).strip()
        answer = re.sub(
            r"\s*```json\s*\{[\s\S]*\}\s*```\s*$",
            "",
            answer,
        ).strip()
        return answer, structured
