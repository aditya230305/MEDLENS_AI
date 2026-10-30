"""
Pipeline Latency Profiler
Instruments execution time across every stage of the MedLens AI processing pipeline.
"""
import time
from typing import Dict, Any
from pydantic import BaseModel, Field


class PipelineLatencies(BaseModel):
    ingestion_ms: float = 0.0
    ocr_ms: float = 0.0
    nlp_extraction_ms: float = 0.0
    rag_retrieval_ms: float = 0.0
    llm_generation_ms: float = 0.0
    validation_ms: float = 0.0
    total_pipeline_ms: float = 0.0


class LatencyTracker:
    def __init__(self):
        self.latencies = PipelineLatencies()
        self._start_times: Dict[str, float] = {}

    def start(self, stage_name: str):
        self._start_times[stage_name] = time.perf_counter()

    def stop(self, stage_name: str) -> float:
        start_t = self._start_times.get(stage_name)
        if start_t is None:
            return 0.0
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0
        field_name = f"{stage_name}_ms"
        if hasattr(self.latencies, field_name):
            setattr(self.latencies, field_name, round(elapsed_ms, 2))
        return elapsed_ms

    def finalize(self) -> PipelineLatencies:
        # Sum of stages
        stages_sum = (
            self.latencies.ingestion_ms +
            self.latencies.ocr_ms +
            self.latencies.nlp_extraction_ms +
            self.latencies.rag_retrieval_ms +
            self.latencies.llm_generation_ms +
            self.latencies.validation_ms
        )
        self.latencies.total_pipeline_ms = round(stages_sum, 2)
        return self.latencies
