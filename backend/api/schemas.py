"""
API Request and Response Pydantic Schemas
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.nlp_extraction.entity_models import StructuredMedicalRecord
from backend.validation.guardrail import ValidationReport
from backend.evaluation.latency_tracker import PipelineLatencies
from backend.evaluation.metrics_store import AggregatedMetrics


class ProcessReportResponse(BaseModel):
    success: bool = True
    file_name: str
    file_type: str
    extraction_method: str
    ocr_applied: bool
    page_count: int
    raw_text_snippet: str
    record: StructuredMedicalRecord
    structured_summary: str
    patient_explanation: str
    retrieved_context: List[Dict[str, Any]]
    validation: ValidationReport
    latencies: PipelineLatencies
    notes: Optional[str] = ""


class QARequest(BaseModel):
    question: str
    record: StructuredMedicalRecord


class QAResponse(BaseModel):
    question: str
    answer: str
    retrieved_citations: List[Dict[str, Any]]
    grounded: bool = True


class FeedbackRequest(BaseModel):
    report_name: str
    is_accurate: bool
    accuracy_rating: int = Field(5, ge=1, le=5)
    feedback_notes: Optional[str] = ""
    pipeline_latency_ms: float = 0.0
    guardrail_score: float = 100.0


class SystemHealthResponse(BaseModel):
    status: str
    gemini_configured: bool
    gemini_model: str
    tesseract_installed: bool
    tesseract_path: Optional[str] = None
    python_version: str
    knowledge_base_items: int
    sample_reports_count: int
