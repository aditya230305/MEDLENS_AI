#!/usr/bin/env bash
# ==============================================================================
# MedLens AI — Unified Single Executable Startup Script
# B.Tech Major Project (7th Semester)
# ==============================================================================

set -e

# Terminal colors
BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}"
cat << "EOF"
  __  __          _ _                     _    ___ 
 |  \/  | ___  __| | |    ___ _ __  ___  / \  |_ _|
 | |\/| |/ _ \/ _` | |   / _ \ '_ \/ __|/ _ \  | | 
 | |  | |  __/ (_| | |__|  __/ | | \__ / ___ \ | | 
 |_|  |_|\___|\__,_|_____\___|_| |_|___/_/   \_\___|
EOF
echo -e "${NC}"
echo -e "${BOLD}Intelligent Medical Report Analysis, Generation & Summarization using LLM${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo ""

# Get directory where script is located
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# --- STEP 1: Check Python Environment ---
echo -e "${BOLD}[Stage 1/7] Validating Python Runtime...${NC}"

# Check or create virtual environment
if [ ! -d ".venv" ]; then
    echo -e " ${YELLOW}• Creating python virtual environment in .venv...${NC}"
    python3 -m venv .venv
fi

# Prioritize .venv python interpreter
if [ -f "$PROJECT_ROOT/.venv/bin/python3" ]; then
    PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python3"
else
    PYTHON_BIN="$(command -v python3 || command -v python)"
fi

PY_VERSION=$("$PYTHON_BIN" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
echo -e " ${GREEN}✓${NC} Python ${PY_VERSION} detected (${PYTHON_BIN})."
source .venv/bin/activate
echo -e " ${GREEN}✓${NC} Virtual environment activated (.venv)."

# --- STEP 2: Verify Python Dependencies ---
echo -e "\n${BOLD}[Stage 2/7] Checking Backend Dependencies...${NC}"
if ! "$PYTHON_BIN" -c "import fastapi, uvicorn, pydantic, pdfplumber, google.genai, reportlab" &> /dev/null; then
    echo -e " ${YELLOW}• Installing required Python packages from requirements.txt...${NC}"
    "$PYTHON_BIN" -m pip install -q -r requirements.txt
    echo -e " ${GREEN}✓${NC} Python packages installed successfully."
else
    echo -e " ${GREEN}✓${NC} All Python backend packages are verified."
fi

# --- STEP 3: Verify Configuration & API Key ---
echo -e "\n${BOLD}[Stage 3/7] Verifying Environment Configuration...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e " ${YELLOW}• Creating .env from .env.example template...${NC}"
        cp .env.example .env
    else
        touch .env
    fi
fi

if grep -q "GEMINI_API_KEY=" .env && [ -n "$(grep "GEMINI_API_KEY=" .env | cut -d '=' -f2)" ]; then
    echo -e " ${GREEN}✓${NC} Gemini API Key configured in .env."
else
    echo -e " ${YELLOW}⚠ Warning: GEMINI_API_KEY is not set in .env. Falling back to local clinical rules engine.${NC}"
fi

# Check Tesseract OCR
if command -v tesseract &> /dev/null; then
    echo -e " ${GREEN}✓${NC} Tesseract OCR engine found at: $(command -v tesseract)"
else
    echo -e " ${YELLOW}ℹ Note: Tesseract binary not found. Digital PDFs will use direct layout extraction.${NC}"
    echo -e "   (To enable OCR on scanned images, run: brew install tesseract)"
fi

# --- STEP 4: Initialize Medical Knowledge Base & Sample Reports ---
echo -e "\n${BOLD}[Stage 4/7] Initializing Medical Reference Corpus & Sample Reports...${NC}"
python3 -c "
from backend.rag.knowledge_base import initialize_knowledge_base
count = initialize_knowledge_base()
print(f' {chr(27)}[0;32m✓{chr(27)}[0m Knowledge base verified ({count} medical panels indexed).')
"

# Generate sample PDF reports if missing
if [ ! -f "backend/data/sample_reports/Sample_Diabetic_Lipid_Panel.pdf" ]; then
    echo -e " ${YELLOW}• Generating sample diagnostic PDF reports...${NC}"
    python3 backend/data/generate_samples.py
else
    echo -e " ${GREEN}✓${NC} Clinical sample reports verified (Diabetic/Lipid, Anemia/CBC, Normal Checkup)."
fi

# --- STEP 5: Verify Frontend Build ---
echo -e "\n${BOLD}[Stage 5/7] Checking Frontend Build...${NC}"
if [ ! -d "frontend/dist" ] || [ ! -f "frontend/dist/index.html" ]; then
    echo -e " ${YELLOW}• Building React + Tailwind CSS production bundle...${NC}"
    if command -v npm &> /dev/null; then
        cd frontend
        npm install -q
        npm run build
        cd "$PROJECT_ROOT"
        echo -e " ${GREEN}✓${NC} React frontend built successfully."
    else
        echo -e " ${RED}Error: npm is required to build the frontend.${NC}"
        exit 1
    fi
else
    echo -e " ${GREEN}✓${NC} React frontend bundle verified (frontend/dist)."
fi

# --- STEP 6 & 7: Launch Unified Application ---
echo -e "\n${BOLD}[Stage 6/7] Launching Unified Application Server...${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo -e "${GREEN}${BOLD}MedLens AI is now active and ready for your viva demonstration!${NC}"
echo -e "  🌐 ${BOLD}Web Application Dashboard:${NC} ${CYAN}http://localhost:8000${NC}"
echo -e "  📖 ${BOLD}Interactive Swagger API Docs:${NC} ${CYAN}http://localhost:8000/docs${NC}"
echo -e "${BLUE}======================================================================${NC}"
echo -e "Press ${YELLOW}Ctrl+C${NC} anytime to stop the server.\n"

# Open browser automatically on macOS / Linux after 1.5 seconds in background
(
    sleep 2
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "http://localhost:8000" 2>/dev/null || true
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "http://localhost:8000" 2>/dev/null || true
    fi
) &

# Run FastAPI backend using python
exec python3 -m backend.main
