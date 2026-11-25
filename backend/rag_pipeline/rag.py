from __future__ import annotations

import json
import logging
import re
import threading

logger = logging.getLogger("sarva_mitra_rag")

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
        GROQ_API_KEYS,
        mongodb_uri,
        RAG_USE_VECTOR_SEARCH,
        EMBEDDING_DIMENSION,
        OLLAMA_API_KEY,
        OLLAMA_BASE_URL,
        OLLAMA_MODEL,
        LLM_PROVIDER,
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
        GROQ_API_KEYS,
        mongodb_uri,
        RAG_USE_VECTOR_SEARCH,
        OLLAMA_API_KEY,
        OLLAMA_BASE_URL,
        OLLAMA_MODEL,
        LLM_PROVIDER,
    )

try:
    from .embeddings import FastEmbedEmbeddings
except ImportError:
    from embeddings import FastEmbedEmbeddings


def _extract_answer_prompt(raw_text: str) -> str:
    """Extract only PART B (the actual system instructions for the LLM) from 23_master_prompt.txt.
    Drops PART A (query builder) and PART C (developer retrieval notes), saving ~1,600 tokens."""
    if "PART B: ANSWER PROMPT" in raw_text:
        part_b = raw_text.split("PART B: ANSWER PROMPT", 1)[1]
        if "PART C: RETRIEVAL SETTINGS" in part_b:
            part_b = part_b.split("PART C: RETRIEVAL SETTINGS", 1)[0]
        part_b = re.sub(r"^\s*\(the main system prompt\)\s*", "", part_b)
        part_b = re.sub(r"^\s*SYSTEM:\s*", "", part_b)
        return part_b.strip()
    return raw_text.strip()


CHAT_SYSTEM_PROMPT = """You are Sarva Mitra, a knowledgeable, friendly, and practical AI agricultural advisor assisting farmers in India.
You are engaged in an interactive, ongoing conversation with a farmer regarding their specific crop, current microclimate telemetry, and agronomic management.

YOUR OBJECTIVE:
Directly address and answer the farmer's specific question using the retrieved agronomic reference documents and current telemetry context as factual background.

CORE INSTRUCTIONS:
1. DIRECT ANSWER & INTENT CLARIFICATION:
   - Provide an immediate, practical answer to the farmer's question.
   - Clarify User Intent: If the farmer asks a brief, colloquial, or ambiguous question (e.g. "yellow leaves", "spray time", "watering", "flower drop"), gently clarify the underlying practical intent first.
   - DO NOT repeat or re-dump the entire list of raw sensor numbers or print the rigid initial sensor diagnostic table unless the farmer explicitly asks to analyze raw telemetry values.
   - Keep your language empathetic, simple, and farmer-first (explain technical terms simply).
   - Keep your response focused and concise (300-400 words) so actionable steps stand out.

2. EVIDENCE-BASED GROUNDING & SAFETY RULES:
   - Ground every crop guideline, threshold, and recommendation in the retrieved reference documents. Cite documents and sections using (DOC_ID, S#).
   - Strict Chemical Safety: Never recommend specific synthetic pesticide brand names, commercial trade labels, or chemical doses. State that chemical applications must be confirmed with the local Krishi Vigyan Kendra (KVK) or State Agricultural Extension Officer.
   - Sensors show environmental favorability and stress risk—they never confirm an active biological infection without in-field visual diagnosis.

3. STRUCTURE OF YOUR RESPONSE:
   - **Direct Explanation & Practical Advice:** Clear guidance answering the farmer's query with citations.
   - **Immediate Field Checklist:** 2-3 specific visual signs to check on leaves, stems, flowers, or roots.
   - **Mandatory Follow-Up Section:** Always conclude your response with:
     ### 💡 Suggested Follow-Up Questions:
     - <Specific follow-up question 1 relevant to their crop, stage, and conditions>
     - <Specific follow-up question 2>
     - <Specific follow-up question 3>
"""


def compact_chat_history(chat_history: list[dict], max_turns: int = 3) -> str:
    """Sanitizes and summarizes conversational history to prevent token explosion.
    - Strips previous error messages.
    - Strips large JSON blocks from assistant turns.
    - Caps previous assistant answers to 220 chars.
    - Retains only the most recent max_turns interactions.
    """
    if not chat_history:
        return "No previous conversation."
    cleaned: list[str] = []
    for item in chat_history:
        role = item.get("role", "user").lower()
        content = (item.get("content") or "").strip()
        if not content:
            continue
        if "Apologies, an error occurred" in content or "413" in content or "rate_limit_exceeded" in content:
            continue
        if role == "assistant":
            # Strip structured json blocks
            content = re.sub(r"BEGIN_STRUCTURED_JSON[\s\S]*?END_STRUCTURED_JSON", "", content).strip()
            content = re.sub(r"```json[\s\S]*?```", "", content).strip()
            if len(content) > 220:
                content = content[:220].rstrip() + "..."
            cleaned.append(f"ASSISTANT: {content}")
        else:
            if len(content) > 200:
                content = content[:200].rstrip() + "..."
            cleaned.append(f"USER: {content}")

    # Keep only the last max_turns exchanges (user + assistant)
    recent = cleaned[-(max_turns * 2):]
    return "\n".join(recent) if recent else "No previous conversation."


_embeddings = None
_groq_key_lock = threading.Lock()
_groq_key_index = 0


def next_groq_api_key() -> str:
    global _groq_key_index
    if not GROQ_API_KEYS:
        raise RuntimeError("Set GROQ_API_KEY in the root .env")
    with _groq_key_lock:
        key = GROQ_API_KEYS[_groq_key_index % len(GROQ_API_KEYS)]
        _groq_key_index = (_groq_key_index + 1) % len(GROQ_API_KEYS)
        return key


def call_ollama_llm(
    messages: list[dict],
    max_tokens: int = 1000,
    temperature: float = 0.0,
) -> str | None:
    """Invokes Ollama using the official OpenAI-compatible endpoint.
    Returns generated content string or None if unsuccessful."""
    if not OLLAMA_API_KEY:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key=OLLAMA_API_KEY,
        )
        completion = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        if completion and completion.choices:
            text = (completion.choices[0].message.content or "").strip()
            if text:
                return text
    except Exception as exc:
        import logging
        logging.getLogger("sarva_mitra_rag").warning(
            "Ollama request to %s (model: %s) failed: %s. Falling back to Groq.",
            OLLAMA_BASE_URL,
            OLLAMA_MODEL,
            exc,
        )
    return None


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
            "crop_stage_tomato",
            "irrigation_tomato",
            "stress_vs_disease",
        ]
    if "chilli" in crop_name or "chili" in crop_name:
        return [
            "chilli_field_checklist",
            "chilli_soil_moisture_ka",
            "chilli_nutrient_deficiencies",
            "chilli_heat_ka",
            "chilli_viral_diseases",
            "chilli_wilt_damping_off",
            "chilli_bacterial_leaf_spot",
            "crop_stage_chilli",
            "irrigation_chilli",
            "stress_vs_disease",
        ]
    if "ragi" in crop_name or "finger millet" in crop_name:
        return [
            "ragi_field_checklist",
            "ragi_soil_moisture_ka",
            "ragi_blast_detailed",
            "ragi_foliar_comparison",
            "crop_stage_ragi",
            "irrigation_ragi",
            "stress_vs_disease",
        ]
    return []


def low_risk_crop_parent_ids(crop: str) -> list[str]:
    crop_name = crop.lower()
    if "tomato" in crop_name:
        return [
            "tomato_field_checklist",
            "tomato_soil_moisture_bands",
            "19_heat_stress_fruit_set_tomato",
            "irrigation_tomato",
        ]
    if "chilli" in crop_name or "chili" in crop_name:
        return [
            "chilli_field_checklist",
            "chilli_soil_moisture_ka",
            "chilli_heat_ka",
            "irrigation_chilli",
        ]
    if "ragi" in crop_name or "finger millet" in crop_name:
        return [
            "ragi_field_checklist",
            "ragi_soil_moisture_ka",
            "irrigation_ragi",
            "crop_stage_ragi",
        ]
    return []


def clean_advisory_text(text: str) -> str:
    """Strips machine-readable structured JSON, delimiters, and codeblocks from advisory text."""
    if not text:
        return ""
    # 1. Strip complete or unclosed BEGIN_STRUCTURED_JSON blocks
    cleaned = re.sub(r"BEGIN_STRUCTURED_JSON[\s\S]*?END_STRUCTURED_JSON", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"BEGIN_STRUCTURED_JSON[\s\S]*$", "", cleaned, flags=re.IGNORECASE)
    # 2. Strip code block json (complete or unclosed only when containing JSON '{')
    cleaned = re.sub(r"```(?:json)?\s*\{[\s\S]*?\}\s*```", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```(?:json)?\s*\{[\s\S]*$", "", cleaned, flags=re.IGNORECASE)
    # 3. Strip standalone JSON objects with response_mode or overview to end of text
    cleaned = re.sub(r'\{\s*"response_mode"[\s\S]*$', '', cleaned, flags=re.IGNORECASE)
    # 4. Remove standalone markers
    cleaned = re.sub(r"END_STRUCTURED_JSON", "", cleaned, flags=re.IGNORECASE)
    # 5. If wrapped in markdown code fence (```markdown ... ```), strip the wrapper fences but keep content
    cleaned = re.sub(r"^```(?:markdown)?\s*\n", "", cleaned.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\n```\s*$", "", cleaned.strip())
    return cleaned.strip()


def load_local_parent_document(doc_id: str) -> Document | None:
    """Loads a parent document directly from the local DOCS_DIR if MongoDB Atlas is unavailable."""
    for candidate in [f"{doc_id}.txt", doc_id]:
        p = DOCS_DIR / candidate
        if p.exists() and p.is_file():
            try:
                content = p.read_text(encoding="utf-8")
                title = doc_id.replace("_", " ").title()
                for line in content.splitlines()[:6]:
                    if line.startswith("TITLE:"):
                        title = line.replace("TITLE:", "").strip()
                return Document(
                    page_content=content,
                    metadata={
                        "doc_id": doc_id,
                        "title": title,
                        "filename": p.name,
                        "section": "complete_parent",
                    }
                )
            except Exception:
                pass
    for p in DOCS_DIR.glob("*.txt"):
        if doc_id.lower() in p.stem.lower():
            try:
                content = p.read_text(encoding="utf-8")
                title = p.stem.replace("_", " ").title()
                for line in content.splitlines()[:6]:
                    if line.startswith("TITLE:"):
                        title = line.replace("TITLE:", "").strip()
                return Document(
                    page_content=content,
                    metadata={
                        "doc_id": p.stem,
                        "title": title,
                        "filename": p.name,
                        "section": "complete_parent",
                    }
                )
            except Exception:
                pass
    return None


class RAGPipeline:
    def __init__(self, collection_name: str | None = None) -> None:
        self.collection_name = collection_name
        self.last_retrieval = {"query": "", "matches": [], "documents_sent": []}
        self.last_summary: str = ""
        self._summary_cache: dict[str, str] = {}
        self.embeddings = None
        if RAG_USE_VECTOR_SEARCH:
            global _embeddings
            if _embeddings is None:
                _embeddings = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)
            self.embeddings = _embeddings
        if not GROQ_API_KEYS and not OLLAMA_API_KEY:
            raise RuntimeError("Set OLLAMA_KEY or GROQ_API_KEY in the root .env")
        raw_prompt = (DOCS_DIR / "23_master_prompt.txt").read_text(encoding="utf-8")
        self.master_prompt = _extract_answer_prompt(raw_prompt)
        self.chat_prompt = CHAT_SYSTEM_PROMPT

    def summarize_history(self, older_messages: list[dict], existing_summary: str = "") -> str:
        """Uses an LLM call to progressively summarize older conversational turns into concise agronomic notes.
        This prevents context loss over long chat sessions while strictly bounding the prompt token size."""
        if not older_messages:
            return existing_summary

        lines = []
        for msg in older_messages:
            role = msg.get("role", "user").upper()
            content = (msg.get("content") or "").strip()
            if not content or "Apologies, an error occurred" in content or "Error code: 413" in content:
                continue
            if role == "ASSISTANT":
                content = re.sub(r"BEGIN_STRUCTURED_JSON[\s\S]*?END_STRUCTURED_JSON", "", content).strip()
                content = re.sub(r"```json[\s\S]*?```", "", content).strip()
                if len(content) > 250:
                    content = content[:250].rstrip() + "..."
            else:
                if len(content) > 180:
                    content = content[:180].rstrip() + "..."
            lines.append(f"{role}: {content}")

        if not lines:
            return existing_summary

        dialogue = "\n".join(lines)
        cache_key = f"{existing_summary}::{dialogue}"
        if cache_key in self._summary_cache:
            return self._summary_cache[cache_key]

        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage, SystemMessage

        summary_system = (
            "You are an agronomic conversation summarizer. "
            "Condense the following conversation between a farmer and an agronomic advisor into 2-3 concise bullet points. "
            "Preserve key context: crop, farmer questions, symptoms observed, sensor values, and recommendations given. "
            "Keep it strictly under 80 words. Do not fabricate."
        )

        user_content = (
            f"Previous Summary:\n{existing_summary}\n\nNew Turns to Integrate:\n{dialogue}"
            if existing_summary
            else f"Conversation to summarize:\n{dialogue}"
        )

        # 1. Try Ollama first (OpenAI-compatible) if configured
        if LLM_PROVIDER == "ollama" or OLLAMA_API_KEY:
            ollama_summary = call_ollama_llm(
                messages=[
                    {"role": "system", "content": summary_system},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=300,
                temperature=0.0,
            )
            if ollama_summary and len(ollama_summary) > 10:
                self._summary_cache[cache_key] = ollama_summary
                return ollama_summary

        # 2. Existing Groq cluster (kept intact as primary or fallback)
        for _ in range(len(GROQ_API_KEYS)):
            try:
                llm = ChatGroq(
                    api_key=next_groq_api_key(),
                    model=GROQ_MODEL,
                    temperature=0,
                    max_tokens=300,
                )
                res = str(llm.invoke([
                    SystemMessage(content=summary_system),
                    HumanMessage(content=user_content),
                ]).content).strip()
                if res and len(res) > 10:
                    self._summary_cache[cache_key] = res
                    return res
            except Exception:
                continue

        # Robust programmatic fallback if summarization LLM call encounters transient rate limits
        user_queries = [
            m.get("content", "")[:120].strip()
            for m in older_messages
            if str(m.get("role", "")).lower() == "user"
        ]
        fallback = (existing_summary + "; " if existing_summary else "") + "Earlier farmer queries: " + "; ".join(user_queries[:3])
        if fallback:
            self._summary_cache[cache_key] = fallback
            return fallback
        return existing_summary

    def prepare_conversation_context(
        self,
        chat_history: list[dict],
        k_recent_turns: int = 2,
        existing_summary: str = "",
    ) -> tuple[str, str]:
        """Progressively summarizes conversation history with an LLM call when turns exceed k_recent_turns."""
        if not chat_history:
            return "No previous conversation.", existing_summary

        valid_history = [
            m for m in chat_history
            if (m.get("content") or "").strip()
            and not str(m.get("content", "")).startswith("Apologies, an error occurred")
            and "Error code: 413" not in str(m.get("content", ""))
        ]

        buffer_msg_count = k_recent_turns * 2

        if len(valid_history) <= buffer_msg_count:
            recent_lines = []
            for item in valid_history:
                role = item.get("role", "user").upper()
                c = (item.get("content") or "").strip()
                if role == "ASSISTANT":
                    c = re.sub(r"BEGIN_STRUCTURED_JSON[\s\S]*?END_STRUCTURED_JSON", "", c).strip()
                    c = re.sub(r"```json[\s\S]*?```", "", c).strip()
                    if len(c) > 220:
                        c = c[:220].rstrip() + "..."
                else:
                    if len(c) > 180:
                        c = c[:180].rstrip() + "..."
                recent_lines.append(f"{role}: {c}")
            return "\n".join(recent_lines), existing_summary

        older_messages = valid_history[:-buffer_msg_count]
        recent_messages = valid_history[-buffer_msg_count:]

        updated_summary = self.summarize_history(older_messages, existing_summary)

        recent_lines = []
        for item in recent_messages:
            role = item.get("role", "user").upper()
            c = (item.get("content") or "").strip()
            if role == "ASSISTANT":
                c = re.sub(r"BEGIN_STRUCTURED_JSON[\s\S]*?END_STRUCTURED_JSON", "", c).strip()
                c = re.sub(r"```json[\s\S]*?```", "", c).strip()
                if len(c) > 220:
                    c = c[:220].rstrip() + "..."
            else:
                if len(c) > 180:
                    c = c[:180].rstrip() + "..."
            recent_lines.append(f"{role}: {c}")

        formatted = (
            f"SUMMARY OF PREVIOUS CONVERSATION:\n{updated_summary}\n\n"
            f"RECENT CONVERSATION TURNS:\n" + "\n".join(recent_lines)
        )
        return formatted, updated_summary

    def retrieve(self, readings: dict, ml_output: int, crop: str, location: str, question: str) -> list[Document]:
        parent_ids: list[str] = []
        matches: list[dict] = []
        collection = None
        client = None

        if RAG_USE_VECTOR_SEARCH:
            try:
                uri = mongodb_uri()
                client = MongoClient(
                    uri,
                    serverSelectionTimeoutMS=2000,
                    connectTimeoutMS=2000,
                    socketTimeoutMS=3000,
                )
                client.admin.command('ping')
                collection = client[MONGODB_DATABASE][self.collection_name or MONGODB_COLLECTION]
            except Exception as mongo_err:
                logger.warning("MongoDB Atlas cluster unavailable (%s). Falling back seamlessly to local document repository.", mongo_err)
                collection = None
                if client:
                    try:
                        client.close()
                    except Exception:
                        pass
                client = None

        try:
            if collection is not None:
                child = collection.find_one({
                    "corpus": "sarva-mitra-rag",
                    "kind": "child",
                })
                if child:
                    metadata = child.get("metadata", {})
                    indexed_model = metadata.get("embedding_model")
                    indexed_dimension = metadata.get("embedding_dimension")
                    if indexed_model and indexed_model != EMBEDDING_MODEL:
                        logger.warning("Indexed with %s, but runtime uses %s", indexed_model, EMBEDDING_MODEL)
                    if indexed_dimension and indexed_dimension != EMBEDDING_DIMENSION:
                        logger.warning("Indexed at %s dimensions, but runtime uses %s", indexed_dimension, EMBEDDING_DIMENSION)

                if ml_output == 0:
                    parent_ids = [
                        "22_healthy_state_betterments",
                        "24_field_hygiene",
                        "21_soil_moisture_effects_by_disease",
                        "19_heat_stress_fruit_set_tomato",
                        "20_soil_salinity_ec_tomato",
                    ]
                    parent_ids.extend(low_risk_crop_parent_ids(crop))
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
                    except Exception as vec_err:
                        logger.warning("MongoDB vector search failed (%s), proceeding to keyword/curated document fallback.", vec_err)
            else:
                # Local repository curated document selection
                if ml_output == 0:
                    parent_ids = [
                        "22_healthy_state_betterments",
                        "24_field_hygiene",
                        "21_soil_moisture_effects_by_disease",
                        "19_heat_stress_fruit_set_tomato",
                        "20_soil_salinity_ec_tomato",
                    ]
                    parent_ids.extend(low_risk_crop_parent_ids(crop))

            # Add crop-specific, weather threshold and topic documents
            parent_ids.insert(0, "02_weather_thresholds_by_disease")
            if any(key in readings for key in ("soil_moisture_pct", "soil_moisture")):
                parent_ids.append("21_soil_moisture_effects_by_disease")
            parent_ids.extend(crop_specific_parent_ids(crop))

            crop_lower = (crop or "").lower()
            q_lower = (question or "").lower()

            if "tomato" in crop_lower:
                parent_ids.extend([
                    "crop_stage_tomato",
                    "irrigation_tomato",
                    "tomato_soil_moisture_bands",
                    "tomato_nutrient_deficiencies",
                    "tomato_blight_leafspot_comparison",
                    "pest_whitefly",
                    "pest_fruit_borer",
                    "pest_armyworm_mite",
                    "viral_vector_confirmation",
                    "nutrient_discrimination",
                ])
            elif "chilli" in crop_lower or "chili" in crop_lower:
                parent_ids.extend([
                    "crop_stage_chilli",
                    "irrigation_chilli",
                    "chilli_soil_moisture_ka",
                    "chilli_nutrient_deficiencies",
                    "chilli_viral_diseases",
                    "chilli_bacterial_leaf_spot",
                    "pest_aphids_thrips",
                    "chilli_wilt_damping_off",
                    "chilli_field_checklist",
                ])
            elif "ragi" in crop_lower or "millet" in crop_lower:
                parent_ids.extend([
                    "crop_stage_ragi",
                    "irrigation_ragi",
                    "ragi_soil_moisture_ka",
                    "15_ragi_blast",
                    "ragi_blast_detailed",
                    "ragi_field_checklist",
                ])

            # Question topic-directed document inclusion
            if any(w in q_lower for w in ("fertiliz", "calcium", "nutrient", "npk", "spray", "flower drop")):
                parent_ids.extend(["fertiliser_guidance", "nutrient_discrimination"])
                if "chilli" in crop_lower:
                    parent_ids.append("chilli_nutrient_deficiencies")
                elif "tomato" in crop_lower:
                    parent_ids.append("tomato_nutrient_deficiencies")
            if any(w in q_lower for w in ("irrigat", "water", "moist", "band")):
                if "tomato" in crop_lower:
                    parent_ids.extend(["irrigation_tomato", "tomato_soil_moisture_bands"])
                elif "chilli" in crop_lower:
                    parent_ids.extend(["irrigation_chilli", "chilli_soil_moisture_ka"])
                elif "ragi" in crop_lower:
                    parent_ids.extend(["irrigation_ragi", "ragi_soil_moisture_ka"])
            if any(w in q_lower for w in ("disease", "pest", "blight", "spot", "curl", "yellow", "wilt", "rot")):
                parent_ids.extend(["stress_vs_disease", "viral_vector_confirmation"])

            parents: list[Document] = []
            for doc_id in dict.fromkeys(parent_ids):
                doc = None
                if collection is not None:
                    try:
                        record = collection.find_one({
                            "corpus": "sarva-mitra-rag",
                            "kind": "parent",
                            "metadata.doc_id": doc_id,
                        })
                        if record:
                            doc = Document(
                                page_content=record["text"],
                                metadata={**record["metadata"], "doc_id": doc_id},
                            )
                    except Exception:
                        doc = None
                if not doc:
                    doc = load_local_parent_document(doc_id)
                if doc:
                    parents.append(doc)

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
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    pass

    def answer(self, readings: dict, ml_output: int, crop: str, location: str,
               question: str, chat_history: list[dict], ml_prediction: dict,
               existing_summary: str = "", k_recent_turns: int = 2,
               mode: str = "report") -> tuple[str, dict]:
        from langchain_core.messages import HumanMessage, SystemMessage
        documents = self.retrieve(readings, ml_output, crop, location, question)
        if not documents:
            raise RuntimeError("No relevant documents found")

        context_parts: list[str] = []
        remaining = 1800
        for doc in documents:
            text = doc.page_content[:600]
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
        history, updated_summary = self.prepare_conversation_context(
            chat_history=chat_history,
            k_recent_turns=k_recent_turns,
            existing_summary=existing_summary or self.last_summary,
        )
        self.last_summary = updated_summary

        if mode == "chat":
            system_prompt = self.chat_prompt
            human = (
                f"FARM & SENSOR CONTEXT:\n"
                f"- Crop: {crop}\n"
                f"- Location: {location}\n"
                f"- Current Sensor Readings: Temperature: {readings.get('temperature_c', 'N/A')}°C, Humidity: {readings.get('humidity_pct', 'N/A')}%, Soil Moisture: {readings.get('soil_moisture_pct', 'N/A')}%, Rainfall: {readings.get('rainfall_mm', 'N/A')}mm\n"
                f"- ML Pathogen Risk: {readings.get('risk_level', 'N/A')} ({readings.get('risk_pct', 'N/A')}%)\n\n"
                f"FARMER'S QUESTION:\n{question}\n\n"
                f"CONVERSATION CONTEXT:\n{history}\n\n"
                f"RETRIEVED AGRONOMIC DOCUMENTS:\n{context}\n\n"
                "INSTRUCTIONS: Answer the farmer's question directly. Clarify their intent if colloquial or ambiguous. "
                "Ground all advice in the retrieved documents using citations (DOC_ID, S#). Do NOT re-dump raw sensor numbers. "
                "At the end, always include '### 💡 Suggested Follow-Up Questions:' with 2-3 specific follow-up questions."
            )
        else:
            system_prompt = self.master_prompt
            human = (
                f"READINGS: {json.dumps(readings, ensure_ascii=False, sort_keys=True)}\n"
                f"ML_OUTPUT: {ml_output}\n"
                f"ML_PREDICTION: {json.dumps(ml_prediction, ensure_ascii=False, sort_keys=True)}\n"
                f"CROP: {crop}\nLOCATION: {location}\n"
                f"QUESTION: {question}\nPREVIOUS CHAT:\n{history}\n"
                f"RETRIEVED DOCUMENTS:\n{context}\n\n"
                "INSTRUCTIONS:\n"
                "Generate a complete, professional agronomic field advisory report in clean Markdown covering:\n"
                "1. Executive Microclimate & Pathogen Risk Assessment (exact readings, status, model risk index)\n"
                "2. High-Priority Field Scouting & Disease Checklist formatted as a clean Markdown table with columns: | Crop Disease / Suspect Pathogen | Diagnostic Symptoms in Field | Priority Level |\n"
                "3. Practical Agronomic Field Interventions formatted as a clean Markdown table with columns: | Management Area | Recommended Field Action | Operational Timing |\n"
                "4. Preventive Non-Chemical & Biological Plant Protection (hygiene, bioprotectants, traps)\n"
                "5. Critical Boundaries & Local KVK Extension Advisory (limitations, laboratory diagnostics)\n"
                "Format tables using standard Markdown pipe syntax (`| Col 1 | Col 2 |`). Do NOT output raw JSON blocks, codeblocks, or delimiter tags. Deliver the complete advisory report with full sentences."
            )
        last_error: Exception | None = None
        content = ""

        max_gen_tokens = 2048
        # 1. Try Ollama first (OpenAI-compatible) if configured
        if LLM_PROVIDER == "ollama" or OLLAMA_API_KEY:
            ollama_ans = call_ollama_llm(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": human},
                ],
                max_tokens=max_gen_tokens,
                temperature=0.0,
            )
            if ollama_ans and len(ollama_ans) > 20:
                content = ollama_ans

        # 2. Existing Groq cluster (kept intact as primary or fallback)
        if not content:
            from langchain_groq import ChatGroq
            for _ in range(len(GROQ_API_KEYS)):
                current_key = next_groq_api_key()
                try:
                    llm = ChatGroq(
                        api_key=current_key,
                        model=GROQ_MODEL,
                        temperature=0,
                        max_tokens=max_gen_tokens,
                    )
                    raw_res = llm.invoke([
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=human),
                    ])
                    res_text = str(raw_res.content).strip() if raw_res and raw_res.content else ""
                    if res_text:
                        content = res_text
                        break
                except Exception as exc:
                    last_error = exc
                    err_str = str(exc)
                    # Handle TPM limit (413 / Request too large) with prompt compression on next key
                    if "413" in err_str or "Request too large" in err_str:
                        try:
                            if mode == "chat":
                                fallback_prompt = self.chat_prompt[:1800]
                                fallback_human = (
                                    f"CROP: {crop} | LOCATION: {location}\n"
                                    f"QUESTION: {question}\n"
                                    f"DOCS: {context[:800]}\n"
                                    "Answer directly with citations (DOC_ID, S#). Conclude with '### 💡 Suggested Follow-Up Questions:'."
                                )
                            else:
                                fallback_prompt = self.master_prompt[:1800]
                                fallback_human = (
                                    f"READINGS: {json.dumps(readings, ensure_ascii=False, sort_keys=True)}\n"
                                    f"ML_OUTPUT: {ml_output}\n"
                                    f"CROP: {crop}\nLOCATION: {location}\n"
                                    f"QUESTION: {question}\n"
                                    f"RETRIEVED DOCUMENTS:\n{context[:900]}\n"
                                    "Return advisory with citations (DOC_ID, S#) followed by BEGIN_STRUCTURED_JSON and END_STRUCTURED_JSON."
                                )
                            fallback_llm = ChatGroq(
                                api_key=next_groq_api_key(),
                                model=GROQ_MODEL,
                                temperature=0,
                                max_tokens=800,
                            )
                            raw_fb = fallback_llm.invoke([
                                SystemMessage(content=fallback_prompt),
                                HumanMessage(content=fallback_human),
                            ])
                            res_fb = str(raw_fb.content).strip() if raw_fb and raw_fb.content else ""
                            if res_fb:
                                content = res_fb
                                break
                        except Exception as fallback_exc:
                            last_error = fallback_exc
        if not content:
            raise RuntimeError(f"Advisory generation failed: {last_error or 'No response from Ollama or Groq'}")
        match = re.search(
            r"BEGIN_STRUCTURED_JSON\s*(\{[\s\S]*?\})\s*(?:END_STRUCTURED_JSON|$)",
            content,
        )
        if not match:
            match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", content)
        if match:
            try:
                structured = json.loads(match.group(1))
            except json.JSONDecodeError:
                structured = None
        else:
            structured = None
        if structured is None:
            structured = {
                "response_mode": "chat" if mode == "chat" else ("abnormality" if ml_output == 1 else "healthy"),
                "overview": "Conversational agronomic guidance." if mode == "chat" else "Advice generated from retrieved documents.",
                "model_interpretation": "The model is a risk signal, not a diagnosis.",
                "sensor_readings": [],
                "possible_conditions": [],
                "watch_list": [],
                "recommendations": [],
                "uncertainty": ["Field verification required."],
                "next_step": "Inspect the plants and contact the local KVK or agriculture officer.",
                "documents_used": [doc.metadata["doc_id"] for doc in documents],
            }
        if mode != "chat":
            structured["response_mode"] = (
                "abnormality" if ml_output == 1 else "healthy"
            )
        answer = clean_advisory_text(content)
        return answer, structured
