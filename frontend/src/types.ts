export type TestStatus = 
  | 'NORMAL'
  | 'HIGH'
  | 'LOW'
  | 'CRITICAL_HIGH'
  | 'CRITICAL_LOW'
  | 'ABNORMAL'
  | 'INCONCLUSIVE'
  | 'UNKNOWN';

export interface LabTestEntity {
  test_name: string;
  value: string;
  numeric_value?: number | null;
  unit: string;
  reference_range: string;
  ref_low?: number | null;
  ref_high?: number | null;
  status: TestStatus;
  category: string;
  clinical_note?: string | null;
}

export interface MedicationEntity {
  name: string;
  dosage: string;
  frequency: string;
  purpose?: string | null;
}

export interface FindingEntity {
  observation: string;
  severity: string;
  category?: string | null;
}

export interface PatientInfo {
  patient_name?: string | null;
  age?: string | null;
  gender?: string | null;
  report_date?: string | null;
  lab_name?: string | null;
}

export interface StructuredMedicalRecord {
  patient_info: PatientInfo;
  tests: LabTestEntity[];
  abnormal_tests: LabTestEntity[];
  medications: MedicationEntity[];
  findings: FindingEntity[];
  raw_text_length: number;
}

export interface FlaggedClaim {
  claim_text: string;
  flag_type: string;
  severity: string;
  explanation: string;
}

export interface VerifiedClaim {
  entity: string;
  reported_value: string;
  verified_in_text: string;
}

export interface ValidationReport {
  is_valid: boolean;
  factual_consistency_score: number;
  total_data_points_checked: number;
  verified_data_points: number;
  verified_claims: VerifiedClaim[];
  flagged_claims: FlaggedClaim[];
  audit_notes: string;
}

export interface PipelineLatencies {
  ingestion_ms: number;
  ocr_ms: number;
  nlp_extraction_ms: number;
  rag_retrieval_ms: number;
  llm_generation_ms: number;
  validation_ms: number;
  total_pipeline_ms: number;
}

export interface KnowledgeChunk {
  chunk_id: string;
  title: string;
  category: string;
  content: string;
  relevance_score: number;
}

export interface ProcessReportResponse {
  success: boolean;
  file_name: string;
  file_type: string;
  extraction_method: string;
  ocr_applied: boolean;
  page_count: number;
  raw_text_snippet: string;
  record: StructuredMedicalRecord;
  structured_summary: string;
  patient_explanation: string;
  retrieved_context: KnowledgeChunk[];
  validation: ValidationReport;
  latencies: PipelineLatencies;
  notes?: string;
}

export interface QAResponse {
  question: string;
  answer: string;
  retrieved_citations: KnowledgeChunk[];
  grounded: boolean;
}

export interface SystemHealthResponse {
  status: string;
  gemini_configured: boolean;
  gemini_model: string;
  tesseract_installed: boolean;
  tesseract_path?: string | null;
  python_version: string;
  knowledge_base_items: number;
  sample_reports_count: number;
}

export interface AggregatedMetrics {
  total_evaluations: number;
  accurate_count: number;
  inaccurate_count: number;
  reliability_percentage: number;
  average_user_rating: number;
  average_latency_ms: number;
  average_guardrail_score: number;
}
