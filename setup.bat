@echo off
REM =============================================================================
REM Sarva Mitra — Automated Setup Script for Windows
REM Developed by Team ANVEXA (ByteCrunchers-HUB/SARVA-MITRA)
REM =============================================================================

echo ==========================================================
echo 🌱 Sarva Mitra — Universal Farm Companion Setup
echo Team ANVEXA ^| https://github.com/ByteCrunchers-HUB/SARVA-MITRA
echo ==========================================================

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Python is not installed or not in your PATH.
    echo Please install Python 3.10, 3.11, or 3.12 and retry.
    pause
    exit /b 1
)

REM Setup virtual environment
if not exist ".venv" (
    echo 📦 Creating virtual environment in .venv...
    python -m venv .venv
) else (
    echo ℹ️ Virtual environment already exists in .venv.
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip and install requirements
echo ⬇️ Upgrading pip and installing dependencies from requirements.txt...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Check for .env file
if not exist ".env" (
    echo ⚠️ No .env file found. Creating template .env...
    (
        echo # SARVA MITRA ENVIRONMENT CONFIGURATION
        echo MONGODB_URI="your_mongodb_atlas_connection_string"
        echo MONGODB_DATABASE=soil-rag-db
        echo MONGODB_COLLECTION=soil-rag-collection
        echo MONGODB_VECTOR_INDEX=rag_vector_index
        echo.
        echo GROQ_API_KEY="your_groq_api_key"
        echo GROQ_MODEL="openai/gpt-oss-120b"
        echo.
        echo WEATHERAPI_KEY="your_weatherapi_key"
        echo TOMORROW_IO_API_KEY="your_tomorrow_io_key"
        echo AGROMONITORING_API_KEY="your_agromonitoring_key"
        echo OPENWEATHERMAP_API_KEY="your_openweather_key"
        echo.
        echo SARVA_MODEL_PATH=backend/ml_engine/models/sarva_mitra_risk_model.joblib
        echo SARVA_STATIC_PATH=backend/ml_engine/models/static_features.csv
    ) > .env
    echo 📝 Template .env created. Please update it with your API keys!
) else (
    echo ✅ .env file found.
)

echo.
echo ==========================================================
echo 🎉 Setup completed successfully!
echo.
echo To run the unified server (Web UI ^& API):
echo     uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
echo     👉 Web UI:  http://localhost:8000/ui/
echo     👉 API Docs: http://localhost:8000/docs
echo.
echo To run Streamlit UI:
echo     streamlit run frontend/app.py
echo ==========================================================
pause
