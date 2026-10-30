"""
Regex Patterns and Clinical Heuristics for Medical Entity Extraction
Provides deterministic pattern matching for lab test parameters, units, reference intervals, and flags.
"""
import re
from typing import Optional, Tuple, Dict, Any, List
from backend.nlp_extraction.entity_models import TestStatus, LabCategory

# Units commonly found in diagnostic lab reports
COMMON_UNITS = [
    r"mg/dL", r"g/dL", r"mmol/L", r"µmol/L", r"umol/L", r"mEq/L",
    r"uIU/mL", r"µIU/mL", r"mIU/L", r"IU/L", r"U/L",
    r"fL", r"fl", r"pg", r"ng/mL", r"ng/dL", r"µg/dL", r"ug/dL",
    r"cells/mcL", r"cells/cumm", r"cells/mm3", r"/cumm", r"/mcL",
    r"x10\^3/uL", r"x10\^6/uL", r"10\^3/uL", r"10\^6/uL",
    r"10\*3/uL", r"10\*6/uL", r"K/uL", r"M/uL",
    r"%", r"sec", r"seconds", r"ratio", r"index", r"mg/L"
]

UNIT_REGEX_STR = r"(?:" + "|".join(re.escape(u) for u in COMMON_UNITS) + r")"
UNIT_REGEX = re.compile(UNIT_REGEX_STR, re.IGNORECASE)

# Patterns for reference intervals:
# "70 - 99", "13.5 to 17.5", "< 200", "<= 5.7", "> 40", ">= 60", "0.5 - 1.2"
RANGE_PATTERNS = [
    # Explicit range: min - max or min to max
    re.compile(r"(\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
    # Upper bound only: < 200, <= 100, Less than 200
    re.compile(r"(?:<|<=|less\s+than)\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
    # Lower bound only: > 40, >= 60, Greater than 40
    re.compile(r"(?:>|>=|greater\s+than)\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
]

# Patterns for status flags in reports
HIGH_FLAG_REGEX = re.compile(r"\b(HIGH|H|\*H|\*HIGH|CRITICAL\s+HIGH|\bH\b)\b|\*", re.IGNORECASE)
LOW_FLAG_REGEX = re.compile(r"\b(LOW|L|\*L|\*LOW|CRITICAL\s+LOW|\bL\b)\b", re.IGNORECASE)

# Dictionary of standard medical tests with canonical names, categories, and keywords
STANDARD_TEST_DICTIONARY: Dict[str, Dict[str, Any]] = {
    # Diabetes / Glycemic Markers (placed before hemoglobin so HbA1c is prioritized)
    "hba1c": {
        "canonical": "Glycated Hemoglobin (HbA1c)",
        "category": LabCategory.DIABETES_MARKERS,
        "default_unit": "%",
        "default_range": "< 5.7",
        "keywords": ["glycated hemoglobin", "glycohemoglobin", "hba1c", "a1c"]
    },
    "fasting_glucose": {
        "canonical": "Fasting Blood Glucose (FBS)",
        "category": LabCategory.DIABETES_MARKERS,
        "default_unit": "mg/dL",
        "default_range": "70 - 99",
        "keywords": ["fasting blood sugar", "fasting glucose", "fbs", "glucose fasting", "glucose - fasting"]
    },
    "postprandial_glucose": {
        "canonical": "Postprandial Blood Glucose (PPBS)",
        "category": LabCategory.DIABETES_MARKERS,
        "default_unit": "mg/dL",
        "default_range": "< 140",
        "keywords": ["postprandial blood glucose", "postprandial glucose", "post prandial", "ppbs", "glucose pp", "2 hr post glucose"]
    },

    # Complete Blood Count (CBC)
    "hemoglobin": {
        "canonical": "Hemoglobin (Hb)",
        "category": LabCategory.HEMATOLOGY,
        "default_unit": "g/dL",
        "default_range": "13.0 - 17.0",
        "keywords": ["hemoglobin", "haemoglobin", "total hemoglobin", "hgb", r"\bhb\b"]
    },

    # Lipid Profile
    "total_cholesterol": {
        "canonical": "Total Cholesterol",
        "category": LabCategory.LIPID_PROFILE,
        "default_unit": "mg/dL",
        "default_range": "< 200",
        "keywords": ["total cholesterol", "cholesterol total", "serum cholesterol"]
    },
    "triglycerides": {
        "canonical": "Triglycerides",
        "category": LabCategory.LIPID_PROFILE,
        "default_unit": "mg/dL",
        "default_range": "< 150",
        "keywords": ["triglycerides", "serum triglycerides", "tg"]
    },
    "hdl": {
        "canonical": "HDL Cholesterol (Good Cholesterol)",
        "category": LabCategory.LIPID_PROFILE,
        "default_unit": "mg/dL",
        "default_range": "> 40",
        "keywords": ["hdl cholesterol", "high density lipoprotein", "hdl-c", "serum hdl"]
    },
    "ldl": {
        "canonical": "LDL Cholesterol (Bad Cholesterol)",
        "category": LabCategory.LIPID_PROFILE,
        "default_unit": "mg/dL",
        "default_range": "< 100",
        "keywords": ["ldl cholesterol", "low density lipoprotein", "ldl-c", "serum ldl"]
    },
    "vldl": {
        "canonical": "VLDL Cholesterol",
        "category": LabCategory.LIPID_PROFILE,
        "default_unit": "mg/dL",
        "default_range": "< 30",
        "keywords": ["vldl cholesterol", "very low density lipoprotein", "vldl"]
    },

    # Kidney Function / Renal
    "serum_creatinine": {
        "canonical": "Serum Creatinine",
        "category": LabCategory.KIDNEY_FUNCTION,
        "default_unit": "mg/dL",
        "default_range": "0.7 - 1.3",
        "keywords": ["creatinine", "serum creatinine", "s. creatinine"]
    },
    "bun": {
        "canonical": "Blood Urea Nitrogen (BUN)",
        "category": LabCategory.KIDNEY_FUNCTION,
        "default_unit": "mg/dL",
        "default_range": "7 - 20",
        "keywords": ["blood urea nitrogen", "bun", "urea nitrogen", "blood urea"]
    },
    "egfr": {
        "canonical": "Estimated GFR (eGFR)",
        "category": LabCategory.KIDNEY_FUNCTION,
        "default_unit": "mL/min/1.73m2",
        "default_range": ">= 90",
        "keywords": ["egfr", "estimated glomerular filtration rate", "gfr"]
    },
    "uric_acid": {
        "canonical": "Serum Uric Acid",
        "category": LabCategory.KIDNEY_FUNCTION,
        "default_unit": "mg/dL",
        "default_range": "3.5 - 7.2",
        "keywords": ["uric acid", "serum uric acid"]
    },

    # Liver Function (LFT)
    "alt_sgpt": {
        "canonical": "Alanine Aminotransferase (ALT / SGPT)",
        "category": LabCategory.LIVER_FUNCTION,
        "default_unit": "U/L",
        "default_range": "7 - 56",
        "keywords": ["alt", "sgpt", "alanine aminotransferase", "alanine transaminase"]
    },
    "ast_sgot": {
        "canonical": "Aspartate Aminotransferase (AST / SGOT)",
        "category": LabCategory.LIVER_FUNCTION,
        "default_unit": "U/L",
        "default_range": "10 - 40",
        "keywords": ["ast", "sgot", "aspartate aminotransferase", "aspartate transaminase"]
    },
    "alp": {
        "canonical": "Alkaline Phosphatase (ALP)",
        "category": LabCategory.LIVER_FUNCTION,
        "default_unit": "U/L",
        "default_range": "44 - 147",
        "keywords": ["alkaline phosphatase", "alp", "alk phos"]
    },
    "total_bilirubin": {
        "canonical": "Total Bilirubin",
        "category": LabCategory.LIVER_FUNCTION,
        "default_unit": "mg/dL",
        "default_range": "0.1 - 1.2",
        "keywords": ["total bilirubin", "bilirubin total", "serum bilirubin"]
    },
    "total_protein": {
        "canonical": "Total Protein",
        "category": LabCategory.LIVER_FUNCTION,
        "default_unit": "g/dL",
        "default_range": "6.0 - 8.3",
        "keywords": ["total protein", "serum protein", "protein total"]
    },
    "albumin": {
        "canonical": "Serum Albumin",
        "category": LabCategory.LIVER_FUNCTION,
        "default_unit": "g/dL",
        "default_range": "3.5 - 5.0",
        "keywords": ["albumin", "serum albumin"]
    },

    # Thyroid Profile
    "tsh": {
        "canonical": "Thyroid Stimulating Hormone (TSH)",
        "category": LabCategory.THYROID_PROFILE,
        "default_unit": "uIU/mL",
        "default_range": "0.4 - 4.0",
        "keywords": ["tsh", "thyroid stimulating hormone", "ultrasensitive tsh"]
    },
    "free_t3": {
        "canonical": "Free T3 (Triiodothyronine)",
        "category": LabCategory.THYROID_PROFILE,
        "default_unit": "pg/mL",
        "default_range": "2.3 - 4.2",
        "keywords": ["free t3", "ft3"]
    },
    "free_t4": {
        "canonical": "Free T4 (Thyroxine)",
        "category": LabCategory.THYROID_PROFILE,
        "default_unit": "ng/dL",
        "default_range": "0.8 - 1.8",
        "keywords": ["free t4", "ft4"]
    }
}


def parse_reference_range(range_str: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Parses a reference interval string into numerical (low, high) bounds.
    Examples:
        "70 - 99" -> (70.0, 99.0)
        "< 200" -> (None, 200.0)
        "> 40" -> (40.0, None)
    """
    if not range_str or not range_str.strip():
        return None, None

    clean = range_str.strip()

    # Case 1: min - max
    m1 = RANGE_PATTERNS[0].search(clean)
    if m1:
        try:
            return float(m1.group(1)), float(m1.group(2))
        except ValueError:
            pass

    # Case 2: Upper bound only (< 200)
    m2 = RANGE_PATTERNS[1].search(clean)
    if m2:
        try:
            return None, float(m2.group(1))
        except ValueError:
            pass

    # Case 3: Lower bound only (> 40)
    m3 = RANGE_PATTERNS[2].search(clean)
    if m3:
        try:
            return float(m3.group(1)), None
        except ValueError:
            pass

    return None, None


def evaluate_test_status(
    numeric_value: Optional[float],
    ref_low: Optional[float],
    ref_high: Optional[float],
    explicit_flag: str = "",
    qualitative_value: Optional[str] = None
) -> TestStatus:
    """
    Determines if a lab test value is NORMAL, HIGH, LOW, or CRITICAL.
    Supports both numeric ranges and qualitative values like TRACE, NIL, NEGATIVE, POSITIVE, OXALATE +, and NO GROWTH.
    """
    flag_upper = (explicit_flag or "").upper()
    value_upper = (qualitative_value or "").upper()

    if "CRITICAL" in flag_upper:
        return TestStatus.CRITICAL_HIGH if "HIGH" in flag_upper or "H" in flag_upper else TestStatus.CRITICAL_LOW

    if numeric_value is not None:
        if ref_high is not None and numeric_value > ref_high:
            return TestStatus.HIGH
        if ref_low is not None and numeric_value < ref_low:
            return TestStatus.LOW
        if ref_low is not None or ref_high is not None:
            return TestStatus.NORMAL

    if HIGH_FLAG_REGEX.search(flag_upper):
        return TestStatus.HIGH
    if LOW_FLAG_REGEX.search(flag_upper):
        return TestStatus.LOW

    if value_upper:
        if any(token in value_upper for token in ["TRACE", "POSITIVE", "PRESENT", "+", "ABNORMAL", "OXALATE +"]):
            return TestStatus.ABNORMAL
        if any(token in value_upper for token in ["NEGATIVE", "NIL", "NONE", "NO GROWTH", "NOT SEEN", "NORMAL"]):
            return TestStatus.NORMAL

    return TestStatus.NORMAL
