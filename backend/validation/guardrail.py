"""
Fact Validation and Guardrail Layer
Verifies LLM-generated summaries and explanations against extracted report data
and retrieved knowledge base chunks to detect and flag hallucinations or inconsistencies.
"""
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.nlp_extraction.entity_models import StructuredMedicalRecord, TestStatus


class FlaggedClaim(BaseModel):
    claim_text: str = Field(..., description="The suspicious sentence or numerical statement")
    flag_type: str = Field(..., description="Numerical Discrepancy | Status Mismatch | Ungrounded Concept")
    severity: str = Field("Medium", description="Low | Medium | High")
    explanation: str = Field(..., description="Why this claim failed verification against report source data")


class VerifiedClaim(BaseModel):
    entity: str
    reported_value: str
    verified_in_text: str


class ValidationReport(BaseModel):
    is_valid: bool = Field(True, description="True if no critical hallucinations detected")
    factual_consistency_score: float = Field(100.0, description="Confidence / factual accuracy percentage (0-100%)")
    total_data_points_checked: int = 0
    verified_data_points: int = 0
    verified_claims: List[VerifiedClaim] = Field(default_factory=list)
    flagged_claims: List[FlaggedClaim] = Field(default_factory=list)
    audit_notes: str = ""


def extract_numerical_tokens(text: str) -> List[str]:
    """Finds all isolated numbers or percentages in text."""
    # Find numbers like 14.2, 120, 7.5%, etc.
    return re.findall(r"\b\d+(?:\.\d+)?%?\b", text)


def validate_generated_content(
    generated_text: str,
    record: StructuredMedicalRecord,
    retrieved_chunks: List[Dict[str, Any]]
) -> ValidationReport:
    """
    Cross-checks LLM generated content against:
    (a) Extracted report entities (tests, values, units, ranges, status)
    (b) Retrieved RAG knowledge chunks
    """
    flagged: List[FlaggedClaim] = []
    verified: List[VerifiedClaim] = []

    # Map of valid extracted numbers (test values, bounds, etc.)
    valid_numbers = set()
    for t in record.tests:
        if t.value:
            valid_numbers.add(t.value.strip())
            valid_numbers.add(t.value.strip() + "%")
        if t.numeric_value is not None:
            valid_numbers.add(str(t.numeric_value))
            # Integer representation if whole
            if t.numeric_value.is_integer():
                valid_numbers.add(str(int(t.numeric_value)))
        if t.ref_low is not None:
            valid_numbers.add(str(t.ref_low))
        if t.ref_high is not None:
            valid_numbers.add(str(t.ref_high))

    # Add patient age if known
    if record.patient_info.age:
        age_digits = re.findall(r"\d+", record.patient_info.age)
        for a in age_digits:
            valid_numbers.add(a)

    # Add date digits if known (e.g. 2026-09-15 -> 2026, 09, 9, 15)
    if record.patient_info.report_date:
        date_digits = re.findall(r"\d+", record.patient_info.report_date)
        for d in date_digits:
            valid_numbers.add(d)
            valid_numbers.add(str(int(d)))

    # Standard clinical reference numbers, dates, and common model strings
    common_thresholds = {
        "5.7", "6.4", "6.5", "70", "99", "100", "125", "126", "140", "150",
        "200", "40", "50", "60", "90", "120", "80", "11000", "4000", "450000",
        "150000", "2", "3", "30", "10", "1", "24", "48", "72", "365", "6",
        "2.5", "1.5", "2.0", "4.0", "3.5", "5.0", "2024", "2025", "2026"
    }
    all_allowed_numbers = valid_numbers.union(common_thresholds)

    # 1. Verify Entity Values & Status Consistency
    lower_gen = generated_text.lower()
    total_checks = 0

    for t in record.tests:
        total_checks += 1
        test_canonical_simple = t.test_name.split("(")[0].strip().lower()
        test_mentioned = (test_canonical_simple in lower_gen) or (t.value in generated_text)

        if test_mentioned:
            # Check if reported value matches
            if t.value in generated_text:
                verified.append(
                    VerifiedClaim(
                        entity=t.test_name,
                        reported_value=f"{t.value} {t.unit}",
                        verified_in_text=f"Confirmed match for {t.test_name} value ({t.value})"
                    )
                )

            # Check for Status Inversion (Hallucination)
            # E.g. test is NORMAL in report, but LLM wrote "elevated <test>" or "low <test>"
            if t.status == TestStatus.NORMAL:
                suspicious_patterns = [
                    f"elevated {test_canonical_simple}",
                    f"high {test_canonical_simple}",
                    f"low {test_canonical_simple}",
                    f"{test_canonical_simple} is high",
                    f"{test_canonical_simple} is elevated",
                    f"{test_canonical_simple} is low"
                ]
                for p in suspicious_patterns:
                    if p in lower_gen:
                        flagged.append(
                            FlaggedClaim(
                                claim_text=f"Report indicates {t.test_name} is NORMAL ({t.value} {t.unit}), but generated summary claims it is out-of-range.",
                                flag_type="Status Mismatch",
                                severity="High",
                                explanation=f"Source report confirmed {t.test_name} at {t.value} {t.unit} (within reference interval {t.reference_range})."
                            )
                        )
                        break

    # 2. Extract and inspect isolated numbers in the generated summary
    # Sentences containing numbers
    sentences = re.split(r"(?<=[.!?])\s+", generated_text)
    for sent in sentences:
        nums_in_sent = re.findall(r"\b\d+(?:\.\d+)?\b", sent)
        for num in nums_in_sent:
            # Skip bullet indices (e.g., 1., 2., 3.) or years (2024, 2025, 2026)
            if num in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "2024", "2025", "2026"]:
                continue
            if num not in all_allowed_numbers:
                # Potential ungrounded number
                total_checks += 1
                # If number doesn't appear in retrieved context either
                kb_text = " ".join([c["content"] for c in retrieved_chunks])
                if num not in kb_text:
                    flagged.append(
                        FlaggedClaim(
                            claim_text=sent.strip(),
                            flag_type="Numerical Discrepancy",
                            severity="Medium",
                            explanation=f"Number '{num}' does not match any value from the laboratory report or reference knowledge base."
                        )
                    )

    # 3. Compute Factual Consistency Score
    total_points = max(total_checks, 1)
    verified_count = len(verified)
    flagged_penalty = len(flagged) * 15.0  # 15% penalty per flagged issue
    score = max(0.0, min(100.0, 100.0 - flagged_penalty))

    is_valid = len([f for f in flagged if f.severity == "High"]) == 0

    audit_notes = (
        f"Verified {len(verified)} extracted entities. "
        f"Found {len(flagged)} potential discrepancies. "
        f"Overall factual consistency score: {score:.1f}%."
    )

    return ValidationReport(
        is_valid=is_valid,
        factual_consistency_score=score,
        total_data_points_checked=total_points,
        verified_data_points=verified_count,
        verified_claims=verified,
        flagged_claims=flagged,
        audit_notes=audit_notes
    )
