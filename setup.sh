#!/usr/bin/env bash
# =============================================================================
# Sarva Mitra — Automated Setup Script for Linux, macOS, and WSL
# Developed by Team ANVEXA (ByteCrunchers-HUB/SARVA-MITRA)
# =============================================================================

set -e

echo "=========================================================="
echo "🌱 Sarva Mitra — Universal Farm Companion Setup"
echo "Team ANVEXA | https://github.com/ByteCrunchers-HUB/SARVA-MITRA"
echo "=========================================================="

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed or not in your PATH."
    echo "Please install Python 3.10, 3.11, or 3.12 and retry."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✅ Detected Python version: $PYTHON_VERSION"

# Setup virtual environment
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
else
    echo "ℹ️  Virtual environment already exists in $VENV_DIR."
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip and install dependencies
echo "⬇️  Upgrading pip and installing requirements from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating template .env..."
    cat << 'EOF' > .env
# SARVA MITRA ENVIRONMENT CONFIGURATION
MONGODB_URI="your_mongodb_atlas_connection_string"
MONGODB_DATABASE=soil-rag-db
MONGODB_COLLECTION=soil-rag-collection
MONGODB_VECTOR_INDEX=rag_vector_index

GROQ_API_KEY="your_groq_api_key"
GROQ_MODEL="openai/gpt-oss-120b"

WEATHERAPI_KEY="your_weatherapi_key"
TOMORROW_IO_API_KEY="your_tomorrow_io_key"
AGROMONITORING_API_KEY="your_agromonitoring_key"
OPENWEATHERMAP_API_KEY="your_openweather_key"

SARVA_MODEL_PATH=backend/ml_engine/models/sarva_mitra_risk_model.joblib
SARVA_STATIC_PATH=backend/ml_engine/models/static_features.csv
EOF
    echo "📝 Template .env created. Please update it with your API keys!"
else
    echo "✅ .env file found."
fi

echo ""
echo "=========================================================="
echo "🎉 Setup completed successfully!"
echo ""
echo "To activate your environment:"
echo "    source .venv/bin/activate"
echo ""
echo "To run the unified server (Web UI & API):"
echo "    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
echo "    👉 Web UI: http://localhost:8000/ui/"
echo "    👉 API Docs: http://localhost:8000/docs"
echo ""
echo "To run Streamlit UI:"
echo "    streamlit run frontend/app.py"
echo "=========================================================="
