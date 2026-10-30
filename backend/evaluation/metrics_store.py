"""
Evaluation Metrics Store
Records examiner feedback and aggregates accuracy, reliability, and latency statistics.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.config import METRICS_FILE

logger = logging.getLogger(__name__)


class EvaluationEntry(BaseModel):
    id: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    report_name: str
    is_accurate: bool
    accuracy_rating: int = Field(5, ge=1, le=5, description="1 to 5 rating scale")
    feedback_notes: Optional[str] = ""
    pipeline_latency_ms: float = 0.0
    guardrail_score: float = 100.0


class AggregatedMetrics(BaseModel):
    total_evaluations: int = 0
    accurate_count: int = 0
    inaccurate_count: int = 0
    reliability_percentage: float = 100.0
    average_user_rating: float = 5.0
    average_latency_ms: float = 0.0
    average_guardrail_score: float = 100.0
    evaluations: List[EvaluationEntry] = Field(default_factory=list)


def _load_raw_data() -> Dict[str, Any]:
    if METRICS_FILE.exists():
        try:
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading metrics file: {e}")
    return {"evaluations": []}


def record_evaluation(entry: EvaluationEntry) -> AggregatedMetrics:
    """Appends an evaluation record and saves to disk."""
    data = _load_raw_data()
    data.setdefault("evaluations", []).append(entry.model_dump())

    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return get_aggregated_metrics()


def get_aggregated_metrics() -> AggregatedMetrics:
    """Computes summary statistics across all recorded evaluations."""
    data = _load_raw_data()
    evals = [EvaluationEntry(**item) for item in data.get("evaluations", [])]

    if not evals:
        return AggregatedMetrics()

    total = len(evals)
    accurate = sum(1 for e in evals if e.is_accurate)
    inaccurate = total - accurate
    reliability = (accurate / total) * 100.0 if total > 0 else 100.0
    avg_rating = sum(e.accuracy_rating for e in evals) / total if total > 0 else 5.0
    avg_latency = sum(e.pipeline_latency_ms for e in evals) / total if total > 0 else 0.0
    avg_guardrail = sum(e.guardrail_score for e in evals) / total if total > 0 else 100.0

    return AggregatedMetrics(
        total_evaluations=total,
        accurate_count=accurate,
        inaccurate_count=inaccurate,
        reliability_percentage=round(reliability, 1),
        average_user_rating=round(avg_rating, 2),
        average_latency_ms=round(avg_latency, 1),
        average_guardrail_score=round(avg_guardrail, 1),
        evaluations=evals
    )
