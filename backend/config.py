"""
MedLens AI Configuration Module
Loads application configuration and environment variables.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
DATA_DIR = BACKEND_DIR / "data"
KNOWLEDGE_CORPUS_DIR = DATA_DIR / "knowledge_corpus"
SAMPLE_REPORTS_DIR = DATA_DIR / "sample_reports"
METRICS_FILE = DATA_DIR / "evaluation_metrics.json"

# Load .env file from project root
ENV_FILE = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE)

# API Keys & LLM settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()

# OCR Settings
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "").strip()

# App settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("ENVIRONMENT", "development").lower() == "development"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
KNOWLEDGE_CORPUS_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
