import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


RAG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = RAG_DIR.parents[1]
DOCS_DIR = RAG_DIR / "docs"
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(RAG_DIR / ".env")


def mongodb_uri() -> str:
    uri = os.getenv("MONGODB_URI")
    if uri:
        return uri
    username = os.getenv("MONGODB_USERNAME")
    password = os.getenv("MONGODB_PASSWORD")
    if not username or not password:
        raise RuntimeError("MONGODB_URI or MONGODB_USERNAME/MONGODB_PASSWORD is required")
    host = os.getenv("MONGODB_HOST", "soil-rag-cluster.dzecwut.mongodb.net")
    from urllib.parse import quote_plus
    return f"mongodb+srv://{quote_plus(username)}:{quote_plus(password)}@{host}/"


MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "soil-rag-db")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "soil-rag-collection")
MONGODB_VECTOR_INDEX = os.getenv("MONGODB_VECTOR_INDEX", "rag_vector_index")
EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
HF_TOKEN = os.getenv("HF_TOKEN")
if HF_TOKEN:
    os.environ["HF_TOKEN"] = HF_TOKEN
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
ML_ENGINE_URL = os.getenv("ML_ENGINE_URL", "https://sarvamitra.onrender.com").rstrip("/")
CHAT_HISTORY_LIMIT = int(os.getenv("CHAT_HISTORY_LIMIT", "12"))
