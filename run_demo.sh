#!/bin/bash
# ==============================================================================
# MedLens AI — One-Click Startup Script for B.Tech Major Project Demo
# ==============================================================================

echo "======================================================================"
echo "🩺 Starting MedLens AI — Intelligent Medical Report Analysis System"
echo "======================================================================"

# Determine workspace root
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Check .env
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Ensure samples are generated
if [ ! -d "backend/data/sample_reports" ] || [ -z "$(ls -A backend/data/sample_reports/*.pdf 2>/dev/null)" ]; then
    echo "Generating sample medical reports..."
    python3 backend/data/generate_samples.py
fi

# Rebuild frontend if dist does not exist
if [ ! -d "frontend/dist" ]; then
    echo "Building React frontend..."
    cd frontend && npm install && npm run build && cd ..
fi

echo ""
echo "🚀 Starting FastAPI Backend & Unified Dashboard Server on http://localhost:8000"
echo "📖 Swagger API Documentation: http://localhost:8000/docs"
echo "----------------------------------------------------------------------"
echo "Press Ctrl+C to stop the server."
echo ""

exec python3 -m backend.main
