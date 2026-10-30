"""
MedLens AI Backend Server Entrypoint
FastAPI application with CORS, API routers, and health monitoring.
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import HOST, PORT, DEBUG, BASE_DIR
from backend.api.routes import router as api_router
from backend.rag.knowledge_base import initialize_knowledge_base

app = FastAPI(
    title="MedLens AI — Intelligent Medical Report Analysis API",
    description=(
        "Backend engine for OCR ingestion, medical NLP entity extraction, "
        "RAG knowledge grounding, structured clinical summarization, "
        "patient-friendly plain language translation, and fact validation."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for local Vite React frontend (ports 5173, 3000, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

# Mount frontend static build directory if present
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")


@app.on_event("startup")
async def startup_event():
    """Initializes knowledge base and dependencies on startup."""
    initialize_knowledge_base()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=DEBUG)
