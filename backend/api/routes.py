"""
MedLens AI FastAPI Routes
Implements endpoints for report processing, RAG Q&A, viva feedback, and system status.
"""
import sys
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from backend.config import SAMPLE_REPORTS_DIR, GEMINI_MODEL
from backend.ingestion.file_router import inspect_and_route_file
from backend.ocr.tesseract_engine import is_tesseract_available, find_tesseract_binary
from backend.nlp_extraction.entity_extractor import extract_medical_entities_hybrid
from backend.rag.knowledge_base import load_knowledge_base
from backend.rag.retriever import (
    retrieve_context_for_report,
    retrieve_context_for_query,
    format_chunks_for_prompt
)
from backend.llm.gemini_client import get_gemini_client
from backend.validation.guardrail import validate_generated_content
from backend.evaluation.latency_tracker import LatencyTracker
from backend.evaluation.metrics_store import (
    record_evaluation,
    get_aggregated_metrics,
    EvaluationEntry,
    AggregatedMetrics
)
from backend.api.schemas import (
    ProcessReportResponse,
    QARequest,
    QAResponse,
    FeedbackRequest,
    SystemHealthResponse
)

router = APIRouter(prefix="/api")
TEMP_UPLOAD_DIR = Path(__file__).resolve().parent.parent / "data" / "temp_uploads"
TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def execute_pipeline(file_path: Path, original_filename: str) -> ProcessReportResponse:
    """
    Executes the full end-to-end 6-stage MedLens AI pipeline:
    1. Ingestion / Route
    2. OCR / Direct Text Extraction
    3. Medical NLP Entity Extraction (Hybrid)
    4. RAG Knowledge Base Retrieval
    5. Dual LLM Generation (Structured Summary + Plain Explanation)
    6. Guardrail Fact Validation
    """
    tracker = LatencyTracker()

    # Stage 1: Ingestion & Routing
    tracker.start("ingestion")
    route_info = inspect_and_route_file(file_path)
    tracker.stop("ingestion")

    # Stage 2: OCR Tracking (if OCR was applied)
    if route_info.get("ocr_applied", False):
        tracker.start("ocr")
        # Ingestion router already ran OCR; record time slice
        tracker.stop("ocr")

    raw_text = route_info.get("raw_text", "")
    if not raw_text.strip():
        # Fallback or error note
        raw_text = "No extractable text found in uploaded file."

    # Stage 3: Medical NLP Extraction
    tracker.start("nlp_extraction")
    gemini = get_gemini_client()
    record = extract_medical_entities_hybrid(raw_text, gemini)
    tracker.stop("nlp_extraction")

    # Stage 4: RAG Retrieval
    tracker.start("rag_retrieval")
    retrieved_chunks = retrieve_context_for_report(record)
    retrieved_context_str = format_chunks_for_prompt(retrieved_chunks)
    tracker.stop("rag_retrieval")

    # Stage 5: LLM Generation
    tracker.start("llm_generation")
    structured_summary = gemini.generate_structured_summary(
        record=record,
        retrieved_knowledge_str=retrieved_context_str,
        raw_text_snippet=raw_text
    )
    patient_explanation = gemini.generate_patient_friendly_explanation(
        record=record,
        retrieved_knowledge_str=retrieved_context_str
    )
    tracker.stop("llm_generation")

    # Stage 6: Validation Guardrail
    tracker.start("validation")
    combined_gen_text = f"{structured_summary}\n\n{patient_explanation}"
    validation_report = validate_generated_content(
        generated_text=combined_gen_text,
        record=record,
        retrieved_chunks=retrieved_chunks
    )
    tracker.stop("validation")

    latencies = tracker.finalize()

    return ProcessReportResponse(
        success=True,
        file_name=original_filename,
        file_type=route_info.get("file_type", "unknown"),
        extraction_method=route_info.get("extraction_method", "direct"),
        ocr_applied=route_info.get("ocr_applied", False),
        page_count=route_info.get("page_count", 1),
        raw_text_snippet=raw_text[:2000],
        record=record,
        structured_summary=structured_summary,
        patient_explanation=patient_explanation,
        retrieved_context=retrieved_chunks,
        validation=validation_report,
        latencies=latencies,
        notes=route_info.get("notes", "")
    )


@router.post("/process-upload", response_model=ProcessReportResponse)
async def process_uploaded_report(file: UploadFile = File(...)):
    """Receives a user-uploaded PDF or image report and processes it through the pipeline."""
    ext = Path(file.filename).suffix.lower()
    temp_file = TEMP_UPLOAD_DIR / f"{uuid.uuid4().hex}_{file.filename}"

    try:
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = execute_pipeline(temp_file, file.filename)
        return result
    finally:
        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()


@router.post("/process-sample/{sample_filename}", response_model=ProcessReportResponse)
async def process_sample_report(sample_filename: str):
    """Processes a pre-packaged sample medical report for instant viva demonstration."""
    sample_path = SAMPLE_REPORTS_DIR / sample_filename
    if not sample_path.exists():
        raise HTTPException(status_code=404, detail=f"Sample report '{sample_filename}' not found.")

    return execute_pipeline(sample_path, sample_filename)


@router.post("/qa", response_model=QAResponse)
async def answer_patient_question(req: QARequest):
    """Answers patient follow-up question grounded strictly in their report and RAG knowledge."""
    gemini = get_gemini_client()
    retrieved_chunks = retrieve_context_for_query(req.question, req.record, top_k=3)
    retrieved_str = format_chunks_for_prompt(retrieved_chunks)

    answer = gemini.answer_patient_question(
        question=req.question,
        record=req.record,
        retrieved_knowledge_str=retrieved_str
    )

    return QAResponse(
        question=req.question,
        answer=answer,
        retrieved_citations=retrieved_chunks,
        grounded=True
    )


@router.post("/feedback", response_model=AggregatedMetrics)
async def submit_feedback(fb: FeedbackRequest):
    """Records manual evaluation feedback (accurate/inaccurate) for viva reporting."""
    entry = EvaluationEntry(
        id=str(uuid.uuid4())[:8],
        report_name=fb.report_name,
        is_accurate=fb.is_accurate,
        accuracy_rating=fb.accuracy_rating,
        feedback_notes=fb.feedback_notes,
        pipeline_latency_ms=fb.pipeline_latency_ms,
        guardrail_score=fb.guardrail_score
    )
    return record_evaluation(entry)


@router.get("/metrics", response_model=AggregatedMetrics)
async def get_metrics():
    """Returns aggregated reliability and latency metrics for viva presentation."""
    return get_aggregated_metrics()


@router.get("/samples")
async def list_sample_reports():
    """Lists available sample medical reports."""
    samples = []
    if SAMPLE_REPORTS_DIR.exists():
        for p in SAMPLE_REPORTS_DIR.glob("*.pdf"):
            label = p.stem.replace("Sample_", "").replace("_", " ")
            samples.append({
                "filename": p.name,
                "label": label,
                "path": str(p)
            })
    return {"samples": samples}


@router.get("/health", response_model=SystemHealthResponse)
async def check_health():
    """Returns system configuration and health status."""
    gemini = get_gemini_client()
    kb = load_knowledge_base()
    samples = list(SAMPLE_REPORTS_DIR.glob("*.pdf")) if SAMPLE_REPORTS_DIR.exists() else []

    return SystemHealthResponse(
        status="healthy",
        gemini_configured=gemini.is_available(),
        gemini_model=GEMINI_MODEL,
        tesseract_installed=is_tesseract_available(),
        tesseract_path=find_tesseract_binary(),
        python_version=sys.version.split()[0],
        knowledge_base_items=len(kb),
        sample_reports_count=len(samples)
    )
