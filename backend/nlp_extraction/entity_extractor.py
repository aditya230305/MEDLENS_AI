"""
Hybrid Medical Entity Extractor
Combines deterministic regex heuristics with LLM-based structured JSON extraction.
"""
import re
import json
import logging
from typing import List, Dict, Any, Optional
from backend.nlp_extraction.entity_models import (
    StructuredMedicalRecord,
    LabTestEntity,
    MedicationEntity,
    FindingEntity,
    PatientInfo,
    TestStatus,
    LabCategory
)
from backend.nlp_extraction.regex_patterns import (
    STANDARD_TEST_DICTIONARY,
    parse_reference_range,
    evaluate_test_status,
    UNIT_REGEX
)

logger = logging.getLogger(__name__)


def extract_patient_info_regex(text: str) -> PatientInfo:
    """Extracts basic patient demographics from text using pattern matching."""
    info = PatientInfo()

    name_patterns = [
        r"(?:Patient\s*Name|Patient\s*NAME|Pt\s*Name|Name)\s*[:\-]?\s*([A-Z][A-Za-z.\s'-]{2,60}?)(?=\s*(?:\||\n|$|(?:Age|Sex|Gender)|Registered|Collected|Reported|Patient\s*ID))",
        r"(?:Patient\s*Name|Patient\s*NAME|Pt\s*Name|Name)\s*[:\-]?\s*([A-Z][A-Za-z.\s'-]{2,60})(?=\s*\|\s*(?:Age|Gender|Sex)|\s*(?:\n|$))"
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = re.sub(r"\s+", " ", match.group(1)).strip()
            if candidate and not candidate.lower().startswith("age") and not candidate.lower().startswith("sex") and not candidate.lower().startswith("gender"):
                info.patient_name = candidate
                break

    age_sex_patterns = [
        r"Age\s*/?\s*Sex\s*[:\-]?\s*(\d{1,3})\s*(?:Y|Yrs|Years|Yr)?\s*/\s*(Male|Female|M|F)\b",
        r"Age\s*/?\s*Gender\s*[:\-]?\s*(\d{1,3})\s*(?:Y|Yrs|Years|Yr)?\s*/\s*(Male|Female|M|F)\b",
        r"Age\s*[:\-]?\s*(\d{1,3})\s*(?:Y|Yrs|Years|Yr)?\s*(?:/|,|\|)\s*(Male|Female|M|F)\b",
        r"Age\s*[:\-]?\s*(\d{1,3})\s*(?:Y|Yrs|Years|Yr)?\s*(?:\|\s*)?(?:Sex|Gender)\s*[:\-]?\s*(Male|Female|M|F)\b"
    ]
    for pattern in age_sex_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info.age = match.group(1)
            gender = match.group(2)
            normalized = gender.upper()
            info.gender = "Male" if normalized in ["M", "MALE"] else "Female" if normalized in ["F", "FEMALE"] else gender.title()
            break

    if info.age is None:
        age_match = re.search(r"\b(?:Age)\s*[:\-]?\s*(\d{1,3})\s*(?:Y|Yrs|Years|Yr)?\b", text, re.IGNORECASE)
        if age_match:
            info.age = age_match.group(1)

    if info.gender is None:
        gender_match = re.search(r"\b(?:Gender|Sex)\s*[:\-]?\s*(Male|Female|M|F)\b", text, re.IGNORECASE)
        if gender_match:
            g = gender_match.group(1).upper()
            info.gender = "Male" if g in ["M", "MALE"] else "Female" if g in ["F", "FEMALE"] else gender_match.group(1).title()

    date_match = re.search(r"(?:Report\s*Date|Collection\s*Date|Date|Reported|Collected|Registered)\s*[:\-]?\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text, re.IGNORECASE)
    if date_match:
        info.report_date = date_match.group(1).strip()

    lab_match = re.search(r"([A-Z0-9\s&]{4,45}(?:DIAGNOSTICS|LABORATORY|LABORATORIES|HEALTHCARE|CLINIC|HOSPITAL))", text)
    if lab_match:
        cand_lab = lab_match.group(1).strip()
        cand_lab = re.sub(r"^(?:NORMAL|TEST|PAGE|RESULT)\s+", "", cand_lab, flags=re.IGNORECASE).strip()
        info.lab_name = cand_lab

    return info


def extract_lab_tests_regex(text: str) -> List[LabTestEntity]:
    """
    Parses lab test rows from medical report text using dictionary keywords,
    pipe-delimited table rows, units, and reference intervals.
    Supports qualitative values such as TRACE, NEGATIVE, POSITIVE, OXALATE +, and NO GROWTH.
    """
    detected_tests: List[LabTestEntity] = []
    lines = text.split("\n")
    current_page = 1

    def add_test(test_name: str, value: str, unit: str = "", reference_range: str = "", numeric_value: Optional[float] = None,
                 ref_low: Optional[float] = None, ref_high: Optional[float] = None, status: TestStatus = TestStatus.UNKNOWN,
                 category: LabCategory = LabCategory.OTHER, section: Optional[str] = None, page: Optional[int] = None,
                 source: Optional[str] = None, flag: Optional[str] = None) -> None:
        if not test_name or not value:
            return
        for existing in detected_tests:
            if existing.test_name.strip().lower() == test_name.strip().lower() and existing.value.strip().lower() == value.strip().lower():
                return
        detected_tests.append(
            LabTestEntity(
                test_name=test_name.strip(),
                value=value.strip(),
                numeric_value=numeric_value,
                unit=unit.strip(),
                reference_range=reference_range.strip(),
                ref_low=ref_low,
                ref_high=ref_high,
                status=status,
                category=category,
                section=section,
                page=page,
                source=source,
                flag=flag
            )
        )

    for line_index, line in enumerate(lines):
        cleaned_line = line.strip()
        if re.match(r"^---\s*Page\s*\d+\s*---", cleaned_line, re.IGNORECASE):
            current_page = int(re.search(r"\d+", cleaned_line).group(0)) if re.search(r"\d+", cleaned_line) else current_page
            continue
        if not cleaned_line or len(cleaned_line) < 3:
            continue

        if "|" in cleaned_line:
            parts = [p.strip() for p in cleaned_line.split("|")]
            if any(h in parts[0].lower() for h in ["test name", "parameter", "patient name", "referred by"]):
                continue
            if len(parts) >= 2:
                candidate_name = parts[0]
                candidate_val = parts[1]
                candidate_unit = parts[2] if len(parts) >= 3 else ""
                candidate_ref = parts[3] if len(parts) >= 4 else ""
                candidate_flag = parts[4] if len(parts) >= 5 else ""

                num_match = re.search(r"(\d+(?:\.\d+)?)", candidate_val)
                if num_match:
                    num_val = float(num_match.group(1))
                    ref_low, ref_high = parse_reference_range(candidate_ref)
                    status = evaluate_test_status(num_val, ref_low, ref_high, candidate_flag)
                    cat = LabCategory.OTHER
                    lower_cand = candidate_name.lower()
                    for _, test_def in STANDARD_TEST_DICTIONARY.items():
                        if any(kw in lower_cand for kw in test_def["keywords"]):
                            cat = test_def["category"]
                            break
                    add_test(candidate_name, num_match.group(1), candidate_unit, candidate_ref, num_val, ref_low, ref_high, status, cat, page=current_page, source="pipe_table", flag=candidate_flag)
                    continue

                # Qualitative pipe-table values like "TRACE", "NEGATIVE", "NO GROWTH"
                if candidate_val and re.search(r"(?:TRACE|NIL|NEGATIVE|POSITIVE|NO\s*GROWTH|OXALATE|PUS|RBC|CASTS|BACTERIA)", candidate_val, re.IGNORECASE):
                    cat = LabCategory.OTHER
                    lower_cand = candidate_name.lower()
                    for _, test_def in STANDARD_TEST_DICTIONARY.items():
                        if any(kw in lower_cand for kw in test_def["keywords"]):
                            cat = test_def["category"]
                            break
                    add_test(candidate_name, candidate_val, candidate_unit, candidate_ref, None, None, None, TestStatus.UNKNOWN, cat, page=current_page, source="pipe_table", flag=candidate_flag)
                    continue

        lower_line = cleaned_line.lower()
        for _, test_def in STANDARD_TEST_DICTIONARY.items():
            matched_keyword = None
            for kw in test_def["keywords"]:
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, lower_line):
                    if kw in ["hb", "hemoglobin"] and "hba1c" in lower_line:
                        continue
                    matched_keyword = kw
                    break
            if not matched_keyword:
                continue

            # Generic patient-level/urinalysis fields like 'Epithelial Cells: 8-10 /HPF'
            if re.search(rf"\b{re.escape(matched_keyword)}\b.*?(\d+\s*(?:-\s*\d+)?\s*(?:/\w+|\w+)?|TRACE|NIL|NEGATIVE|POSITIVE|OXALATE\s*\+|NO\s*GROWTH)", cleaned_line, re.IGNORECASE):
                value_match = re.search(r"(?:(?:\d+(?:\.\d+)?)\s*(?:-\s*\d+)?(?:\s*/\s*[A-Za-z]+)?|TRACE|NIL|NEGATIVE|POSITIVE|OXALATE\s*\+|NO\s*GROWTH)", cleaned_line, re.IGNORECASE)
                if value_match:
                    result_val_str = value_match.group(0).strip()
                    num_val = None
                    num_match = re.search(r"\d+(?:\.\d+)?", result_val_str)
                    if num_match:
                        num_val = float(num_match.group(0))
                    unit_match = UNIT_REGEX.search(cleaned_line)
                    unit = unit_match.group(0) if unit_match else ""
                    ref_low, ref_high = None, None
                    ref_range_str = ""
                    range_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)", cleaned_line)
                    if range_match:
                        ref_range_str = range_match.group(0)
                        ref_low, ref_high = parse_reference_range(ref_range_str)
                    else:
                        explicit_match = re.search(r"(?:Reference|Ref)\s*[:\-]?\s*(.+)", cleaned_line, re.IGNORECASE)
                        if explicit_match:
                            ref_range_str = explicit_match.group(1).strip()
                            ref_low, ref_high = parse_reference_range(ref_range_str)
                        else:
                            ref_range_str = test_def.get("default_range", "")
                            ref_low, ref_high = parse_reference_range(ref_range_str)
                    status = evaluate_test_status(num_val, ref_low, ref_high, qualitative_value=result_val_str)
                    norm_key = re.sub(r"[\(\)\s\-_]", "", test_def["canonical"].split("(")[0].lower())
                    already_exists = any(norm_key in re.sub(r"[\(\)\s\-_]", "", t.test_name.lower()) for t in detected_tests)
                    if not already_exists:
                        add_test(test_def["canonical"], result_val_str, unit, ref_range_str, num_val, ref_low, ref_high, status, test_def["category"], section="unknown", page=current_page, source="line_match")
                    break

    # Additional generic extraction for qualitative lab values not tied to standard dictionary and for 'Culture Result: NO GROWTH...'
    for line_index, line in enumerate(lines):
        cleaned_line = line.strip()
        if not cleaned_line:
            continue
        if re.search(r"(?:Culture\s*Result|Result)\s*[:\-]?\s*(NO\s*GROWTH.*)", cleaned_line, re.IGNORECASE):
            value = re.search(r"(?:Culture\s*Result|Result)\s*[:\-]?\s*(.*)", cleaned_line, re.IGNORECASE)
            if value:
                result_text = value.group(1).strip()
                add_test("Culture Result", result_text, "", "", None, None, None, TestStatus.UNKNOWN, LabCategory.OTHER, section="Culture & Sensitivity", page=current_page, source="qualitative_rule")
        if re.search(r"(?:Epithelial\s*Cells|Pus\s*Cells|RBCs|Crystals|Protein|Nitrite|Leucocyte\s*Esterase|Specific\s*Gravity|Reducing\s*Sugar|Bacteria|Others)\s*[:\-]", cleaned_line, re.IGNORECASE):
            test_name_match = re.search(r"([A-Za-z][A-Za-z\s/()&-]{2,40})\s*[:\-]", cleaned_line)
            if test_name_match:
                test_name = test_name_match.group(1).strip()
                value_match = re.search(r"[:\-]\s*(.*)$", cleaned_line)
                if value_match:
                    value_text = value_match.group(1).strip()
                    if value_text:
                        ref_text = ""
                        for next_line in lines[line_index + 1: line_index + 3]:
                            ref_match = re.search(r"(?:Reference|Ref)\s*[:\-]?\s*(.*)", next_line.strip(), re.IGNORECASE)
                            if ref_match:
                                ref_text = ref_match.group(1).strip()
                                break
                        numeric_value = None
                        ref_low = None
                        ref_high = None
                        num_match = re.search(r"\d+(?:\.\d+)?", value_text)
                        if num_match:
                            numeric_value = float(num_match.group(0))
                        if ref_text:
                            ref_low, ref_high = parse_reference_range(ref_text)
                        status = evaluate_test_status(numeric_value, ref_low, ref_high, qualitative_value=value_text)
                        add_test(test_name, value_text, "", ref_text, numeric_value, ref_low, ref_high, status, LabCategory.URINALYSIS, section="Urine Routine Examination", page=current_page, source="generic_urinalysis")

    return detected_tests


def extract_medications_regex(text: str) -> List[MedicationEntity]:
    """Detects commonly prescribed medications in clinical impressions or treatment sections."""
    meds: List[MedicationEntity] = []
    common_drugs = [
        ("Metformin", "Anti-diabetic", ["metformin", "glycomet"]),
        ("Atorvastatin", "Cholesterol-lowering (Statin)", ["atorvastatin", "lipitor"]),
        ("Lisinopril", "ACE inhibitor for blood pressure", ["lisinopril"]),
        ("Amlodipine", "Calcium channel blocker for blood pressure", ["amlodipine", "norvasc"]),
        ("Levothyroxine", "Thyroid hormone replacement", ["levothyroxine", "synthroid", "thyronorm"]),
        ("Omeprazole", "Proton-pump inhibitor for acid reflux", ["omeprazole", "prilosec"]),
        ("Aspirin", "Anti-platelet blood thinner", ["aspirin", "ecosprin"]),
        ("Losartan", "ARB for blood pressure/kidney protection", ["losartan", "cozaar"]),
        ("Metoprolol", "Beta blocker for hypertension/heart rate", ["metoprolol", "lopressor"]),
        ("Glimepiride", "Sulfonylurea for diabetes", ["glimepiride", "amaryl"])
    ]

    lower_text = text.lower()
    for name, purpose, aliases in common_drugs:
        for alias in aliases:
            match = re.search(r"\b" + re.escape(alias) + r"\b(?:\s*(\d+\s*(?:mg|mcg|g)))?", lower_text)
            if match:
                dosage = match.group(1) or ""
                meds.append(
                    MedicationEntity(
                        name=name,
                        dosage=dosage.strip(),
                        frequency="As prescribed",
                        purpose=purpose
                    )
                )
                break

    return meds


def extract_medical_entities_hybrid(
    raw_text: str,
    gemini_client: Optional[Any] = None
) -> StructuredMedicalRecord:
    """
    Executes hybrid entity extraction:
    1. Deterministic Regex Parsing (exact numbers, units, ranges)
    2. Optional Gemini LLM Structured Enrichment (if API client is available)
    3. Merges and deduplicates into StructuredMedicalRecord
    """
    # 1. Regex Pass
    patient_info = extract_patient_info_regex(raw_text)
    tests = extract_lab_tests_regex(raw_text)
    meds = extract_medications_regex(raw_text)
    findings: List[FindingEntity] = []

    # 2. LLM Enhancement (if Gemini client is available and active)
    if gemini_client and getattr(gemini_client, "is_available", lambda: False)():
        try:
            llm_record = gemini_client.extract_structured_entities(raw_text)
            if llm_record:
                # Merge patient info if missing
                if not patient_info.patient_name and llm_record.patient_info.patient_name:
                    patient_info = llm_record.patient_info

                # Merge any tests discovered by LLM not caught by regex
                existing_names = {t.test_name.lower() for t in tests}
                for t in llm_record.tests:
                    if t.test_name.lower() not in existing_names:
                        # Re-evaluate status just in case
                        if t.ref_low is None or t.ref_high is None:
                            low, high = parse_reference_range(t.reference_range)
                            t.ref_low = low
                            t.ref_high = high
                        t.status = evaluate_test_status(t.numeric_value, t.ref_low, t.ref_high)
                        tests.append(t)
                        existing_names.add(t.test_name.lower())

                # Merge medications and findings
                if llm_record.medications:
                    meds = llm_record.medications
                if llm_record.findings:
                    findings = llm_record.findings
        except Exception as e:
            logger.warning(f"LLM extraction pass skipped or failed, using regex results: {e}")

    # Calculate abnormal tests
    abnormal = [t for t in tests if t.status in [TestStatus.HIGH, TestStatus.LOW, TestStatus.CRITICAL_HIGH, TestStatus.CRITICAL_LOW, TestStatus.ABNORMAL]]

    # If no findings were provided by LLM, generate baseline clinical observations from abnormal tests
    if not findings and abnormal:
        for ab in abnormal:
            direction = "elevated" if "HIGH" in ab.status.value else "depressed/low"
            findings.append(
                FindingEntity(
                    observation=f"{ab.test_name} is {direction} at {ab.value} {ab.unit} (Normal interval: {ab.reference_range}).",
                    severity="Moderate" if "CRITICAL" not in ab.status.value else "Severe",
                    category=ab.category.value
                )
            )

    return StructuredMedicalRecord(
        patient_info=patient_info,
        tests=tests,
        abnormal_tests=abnormal,
        medications=meds,
        findings=findings,
        raw_text_length=len(raw_text)
    )
