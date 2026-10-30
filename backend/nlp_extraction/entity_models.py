"""
Medical Entity Data Models
Pydantic schemas for structured extraction of lab tests, medications, and findings.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class TestStatus(str, Enum):
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    LOW = "LOW"
    CRITICAL_HIGH = "CRITICAL_HIGH"
    CRITICAL_LOW = "CRITICAL_LOW"
    ABNORMAL = "ABNORMAL"
    INCONCLUSIVE = "INCONCLUSIVE"
    UNKNOWN = "UNKNOWN"


class LabCategory(str, Enum):
    HEMATOLOGY = "Hematology"
    BIOCHEMISTRY = "Biochemistry"
    LIPID_PROFILE = "Lipid Profile"
    DIABETES_MARKERS = "Diabetes Markers"
    LIVER_FUNCTION = "Liver Function"
    KIDNEY_FUNCTION = "Kidney Function"
    THYROID_PROFILE = "Thyroid Profile"
    ELECTROLYTES = "Electrolytes"
    URINALYSIS = "Urinalysis"
    CARDIAC = "Cardiac Markers"
    OTHER = "General / Other"


class LabTestEntity(BaseModel):
    test_name: str = Field(..., description="Standardized or extracted name of the medical test")
    value: str = Field(..., description="Numerical or qualitative result value")
    numeric_value: Optional[float] = Field(None, description="Parsed numeric value if applicable")
    unit: str = Field("", description="Measurement unit (e.g., mg/dL, g/dL, mmol/L)")
    reference_range: str = Field("", description="Reference normal interval (e.g., 70-99, < 200)")
    ref_low: Optional[float] = Field(None, description="Lower bound of reference range")
    ref_high: Optional[float] = Field(None, description="Upper bound of reference range")
    status: TestStatus = Field(TestStatus.NORMAL, description="Evaluation of value against reference interval")
    category: LabCategory = Field(LabCategory.OTHER, description="Clinical category of test")
    section: Optional[str] = Field(None, description="Section or heading associated with the result")
    page: Optional[int] = Field(None, description="Source page number in the original document")
    source: Optional[str] = Field(None, description="Original source or extraction method")
    clinical_note: Optional[str] = Field(None, description="Brief note on what this test reflects")
    flag: Optional[str] = Field(None, description="Explicit qualitative flag when present, such as TRACE, NIL, POSITIVE, or NO GROWTH")


class MedicationEntity(BaseModel):
    name: str = Field(..., description="Name of the medication or drug")
    dosage: str = Field("", description="Strength or dosage (e.g. 500mg, 10mg)")
    frequency: str = Field("", description="Dosing schedule (e.g. Once daily, BID)")
    purpose: Optional[str] = Field(None, description="Indication or therapeutic goal")


class FindingEntity(BaseModel):
    observation: str = Field(..., description="Clinical observation, comment, or impression")
    severity: str = Field("Info", description="Severity: Info, Mild, Moderate, Severe")
    category: Optional[str] = Field(None, description="Relevant body system or area")


class PatientInfo(BaseModel):
    patient_name: Optional[str] = Field(None, description="Name or identifier of the patient")
    age: Optional[str] = Field(None, description="Age of the patient")
    gender: Optional[str] = Field(None, description="Gender/Sex of the patient")
    report_date: Optional[str] = Field(None, description="Date the report was issued/specimen collected")
    lab_name: Optional[str] = Field(None, description="Name of the diagnostic laboratory or hospital")


class StructuredMedicalRecord(BaseModel):
    patient_info: PatientInfo = Field(default_factory=PatientInfo)
    tests: List[LabTestEntity] = Field(default_factory=list, description="All identified lab tests")
    abnormal_tests: List[LabTestEntity] = Field(default_factory=list, description="Only tests with HIGH or LOW flags")
    medications: List[MedicationEntity] = Field(default_factory=list, description="Detected medications")
    findings: List[FindingEntity] = Field(default_factory=list, description="Clinical impressions and findings")
    raw_text_length: int = Field(0, description="Total characters in raw extracted text")
