"""
Google Gemini API Client Module
Interacts with Google Gemini (gemini-2.5-flash / gemini-1.5-flash) for medical analysis,
summarization, patient explanation, and Q&A.
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
from google import genai
from google.genai import types

from backend.config import GEMINI_API_KEY, GEMINI_MODEL
from backend.nlp_extraction.entity_models import (
    StructuredMedicalRecord,
    LabTestEntity,
    MedicationEntity,
    FindingEntity,
    PatientInfo,
    TestStatus,
    LabCategory
)
from backend.llm.prompt_templates import (
    STRUCTURED_SUMMARY_SYSTEM,
    STRUCTURED_SUMMARY_USER_TEMPLATE,
    PATIENT_FRIENDLY_SYSTEM,
    PATIENT_FRIENDLY_USER_TEMPLATE,
    QA_SYSTEM_PROMPT,
    QA_USER_TEMPLATE
)

logger = logging.getLogger(__name__)


class GeminiMedicalClient:
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "").strip()
        self.model_name = model_name or GEMINI_MODEL or "gemini-3.5-flash"
        self.fallback_models = [self.model_name, "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.8-flash"]
        self._client = None

        if self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                self._client = None

    def _generate_with_fallback(self, contents: Any, config: Optional[types.GenerateContentConfig] = None) -> str:
        """Attempts generation with configured model, falling back to alternates on temporary errors."""
        last_error = None
        for model in self.fallback_models:
            try:
                response = self._client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
                return response.text.strip()
            except Exception as e:
                last_error = e
                logger.warning(f"Model {model} failed: {e}. Trying alternate model...")
        raise last_error

    def is_available(self) -> bool:
        """Returns True if a valid Gemini API key is configured."""
        return self._client is not None and bool(self.api_key)

    def generate_structured_summary(
        self,
        record: StructuredMedicalRecord,
        retrieved_knowledge_str: str,
        raw_text_snippet: str
    ) -> str:
        """Generates a concise, structured clinical summary using Gemini."""
        if not self.is_available():
            return self._generate_fallback_clinical_summary(record)

        # Prepare prompt inputs
        patient_str = f"Name: {record.patient_info.patient_name or 'Not specified'}, Age: {record.patient_info.age or 'N/A'}, Gender: {record.patient_info.gender or 'N/A'}, Date: {record.patient_info.report_date or 'N/A'}"
        
        abnormal_list = "\n".join([
            f"- {t.test_name}: {t.value} {t.unit} (Normal Range: {t.reference_range}) -> Status: {t.status.value}"
            for t in record.abnormal_tests
        ]) or "No abnormal parameters flagged."

        all_list = "\n".join([
            f"- {t.test_name}: {t.value} {t.unit} (Ref: {t.reference_range}) [{t.status.value}]"
            for t in record.tests
        ]) or "No individual lab tests identified."

        meds_findings = "Medications:\n" + ("\n".join([f"- {m.name} ({m.dosage})" for m in record.medications]) or "None noted.")
        meds_findings += "\nFindings:\n" + ("\n".join([f"- {f.observation} [{f.severity}]" for f in record.findings]) or "None noted.")

        user_content = STRUCTURED_SUMMARY_USER_TEMPLATE.format(
            patient_info=patient_str,
            abnormal_tests_list=abnormal_list,
            all_tests_list=all_list,
            medications_and_findings=meds_findings,
            retrieved_knowledge=retrieved_knowledge_str,
            raw_text_snippet=raw_text_snippet[:1500]
        )

        try:
            return self._generate_with_fallback(
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=STRUCTURED_SUMMARY_SYSTEM,
                    temperature=0.2,
                    max_output_tokens=1500
                )
            )
        except Exception as e:
            logger.error(f"Gemini API error during structured summary generation: {e}")
            return self._generate_fallback_clinical_summary(record, str(e))

    def generate_patient_friendly_explanation(
        self,
        record: StructuredMedicalRecord,
        retrieved_knowledge_str: str
    ) -> str:
        """Generates patient-friendly plain language translation."""
        if not self.is_available():
            return self._generate_fallback_patient_explanation(record)

        summary_data = []
        if record.abnormal_tests:
            summary_data.append("Notable / Out of Range Tests:")
            for t in record.abnormal_tests:
                summary_data.append(f"- {t.test_name}: Your result is {t.value} {t.unit}. Normal target is {t.reference_range} ({t.status.value}).")
        if record.tests:
            summary_data.append("\nNormal Tests:")
            normal_tests = [t for t in record.tests if t.status == TestStatus.NORMAL]
            for t in normal_tests:
                summary_data.append(f"- {t.test_name}: {t.value} {t.unit} (Normal)")

        user_content = PATIENT_FRIENDLY_USER_TEMPLATE.format(
            patient_summary_data="\n".join(summary_data),
            retrieved_knowledge=retrieved_knowledge_str
        )

        try:
            return self._generate_with_fallback(
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=PATIENT_FRIENDLY_SYSTEM,
                    temperature=0.3,
                    max_output_tokens=1500
                )
            )
        except Exception as e:
            logger.error(f"Gemini API error during patient explanation: {e}")
            return self._generate_fallback_patient_explanation(record, str(e))

    def answer_patient_question(
        self,
        question: str,
        record: StructuredMedicalRecord,
        retrieved_knowledge_str: str
    ) -> str:
        """Answers follow-up patient questions grounded in report and RAG knowledge."""
        if not self.is_available():
            return (
                "⚠️ *Google Gemini API Key is not configured yet.*\n\n"
                f"**Based on the local report data:**\n"
                f"- Total Tests Analyzed: {len(record.tests)}\n"
                f"- Abnormal Results: {', '.join([f'{t.test_name} ({t.value} {t.unit})' for t in record.abnormal_tests]) or 'None'}\n\n"
                "Please add your `GEMINI_API_KEY` to the `.env` file to enable conversational AI Q&A."
            )

        report_context = f"Patient: {record.patient_info.patient_name or 'N/A'}, Age: {record.patient_info.age or 'N/A'}\n"
        report_context += "Tests in Report:\n"
        for t in record.tests:
            report_context += f"- {t.test_name}: {t.value} {t.unit} (Ref: {t.reference_range}, Status: {t.status.value})\n"

        user_content = QA_USER_TEMPLATE.format(
            patient_report_data=report_context,
            retrieved_knowledge=retrieved_knowledge_str,
            user_question=question
        )

        try:
            return self._generate_with_fallback(
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=QA_SYSTEM_PROMPT,
                    temperature=0.2,
                    max_output_tokens=1000
                )
            )
        except Exception as e:
            logger.error(f"Gemini API error in Q&A: {e}")
            return f"Error communicating with Gemini API: {str(e)}"

    def extract_structured_entities(self, raw_text: str) -> Optional[StructuredMedicalRecord]:
        """Uses Gemini to extract structured entities in strict JSON schema."""
        if not self.is_available():
            return None

        prompt = f"""You are a medical NLP extractor. Extract all lab tests, patient details, medications, and findings from the following medical report text into a strict JSON format matching this schema:
{{
  "patient_info": {{
    "patient_name": "string or null",
    "age": "string or null",
    "gender": "string or null",
    "report_date": "string or null",
    "lab_name": "string or null"
  }},
  "tests": [
    {{
      "test_name": "string",
      "value": "string",
      "numeric_value": 0.0,
      "unit": "string",
      "reference_range": "string",
      "status": "NORMAL or HIGH or LOW or ABNORMAL",
      "category": "Hematology or Lipid Profile or Diabetes Markers or Kidney Function or Liver Function or Thyroid Profile or Other"
    }}
  ],
  "medications": [
    {{ "name": "string", "dosage": "string", "frequency": "string", "purpose": "string" }}
  ],
  "findings": [
    {{ "observation": "string", "severity": "Info or Mild or Moderate or Severe", "category": "string" }}
  ]
}}

Only respond with the valid raw JSON object. Do not include markdown ticks or additional text.

REPORT TEXT:
{raw_text[:4000]}
"""
        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            data = json.loads(response.text)
            return StructuredMedicalRecord(**data)
        except Exception as e:
            logger.warning(f"Structured extraction via Gemini failed: {e}")
            return None

    # --- FALLBACK GENERATORS (Deterministic, High-Quality Viva Fallbacks) ---
    def _generate_fallback_clinical_summary(self, record: StructuredMedicalRecord, err_msg: str = "") -> str:
        """High-grade clinical summary fallback using extracted entities."""
        lines = [
            "## 📋 Clinical Overview",
            f"- **Patient**: {record.patient_info.patient_name or 'Unspecified'} | **Age**: {record.patient_info.age or 'N/A'} | **Gender**: {record.patient_info.gender or 'N/A'}",
            f"- **Date**: {record.patient_info.report_date or 'N/A'} | **Diagnostic Lab**: {record.patient_info.lab_name or 'Diagnostic Laboratory'}",
            f"- **Total Tests Evaluated**: {len(record.tests)} parameters across {len(set(t.category for t in record.tests))} diagnostic panels.",
            "",
            "## ⚠️ Key Abnormal Findings"
        ]

        if record.abnormal_tests:
            for t in record.abnormal_tests:
                lines.append(f"- **{t.test_name}**: `{t.value} {t.unit}` *(Normal Interval: {t.reference_range})* — **Flagged {t.status.value}**")
        else:
            lines.append("- All analyzed laboratory parameters reside within established baseline reference intervals.")

        lines.extend([
            "",
            "## ✅ Normal Parameters Summary",
            f"- Identified {len([t for t in record.tests if t.status == TestStatus.NORMAL])} parameters within normal physiological limits."
        ])

        if record.medications:
            lines.extend([
                "",
                "## 💊 Concurrent Medications Detected",
                *[f"- **{m.name}** ({m.dosage or 'Prescribed dose'}): {m.purpose or 'Chronic maintenance'}" for m in record.medications]
            ])

        lines.extend([
            "",
            "## 🩺 Clinical Considerations",
            "- Recommend clinical correlation with patient's symptomatology and past medical records.",
            "- Repeat evaluation of out-of-range parameters as clinically indicated.",
            "",
            "---",
            "*Disclaimer: This summary is generated for informational and organizational assistance and does not constitute a clinical diagnosis or treatment prescription.*"
        ])

        if err_msg:
            lines.insert(0, f"> ℹ️ *Generated via Rule-Based Clinical Engine (Gemini API Notice: {err_msg})*\n")
        elif not self.api_key:
            lines.insert(0, "> ℹ️ *Generated via Built-in Clinical Engine. Add your `GEMINI_API_KEY` to `.env` to enable Gemini 2.5 Flash generations.*\n")

        return "\n".join(lines)

    def _generate_fallback_patient_explanation(self, record: StructuredMedicalRecord, err_msg: str = "") -> str:
        """High-grade patient explanation fallback using extracted entities."""
        lines = [
            "## 👋 The Big Picture",
            f"Here is a simple, clear guide to your recent medical report. Your lab panel reviewed **{len(record.tests)} specific measurements**."
        ]

        if record.abnormal_tests:
            lines.append(f"Most parameters look stable, but there are **{len(record.abnormal_tests)} values** that were outside standard reference targets and are worth discussing with your doctor.\n")
            lines.append("## 🔍 Understanding Your Key Results")
            for t in record.abnormal_tests:
                direction = "higher" if "HIGH" in t.status.value else "lower"
                lines.append(f"### • {t.test_name}")
                lines.append(f"- **Your Result**: **{t.value} {t.unit}** (Standard target: {t.reference_range})")
                lines.append(f"- **What this means**: This value is {direction} than the typical range.")
                lines.append(f"- **Why it matters**: Your body balances this parameter closely. Temporary factors such as hydration, diet, exercise, or recent medications can influence this number.")
                lines.append("")
        else:
            lines.append("Great news! All of your lab results evaluated in this report fall squarely within standard healthy reference ranges.\n")

        lines.extend([
            "## 🥦 Healthy Everyday Habits",
            "- Stay well hydrated by drinking adequate water throughout the day.",
            "- Maintain consistent physical activity (such as 30 minutes of brisk walking).",
            "- Focus on balanced, fiber-rich meals with fresh vegetables, lean proteins, and whole grains.",
            "",
            "## 🗣️ Good Questions for Your Next Doctor's Visit",
            "- *'What might have caused these specific values to be slightly out of range?'*",
            "- *'Are there any simple dietary or lifestyle adjustments I should prioritize?'*",
            "- *'When would you recommend a routine follow-up check to re-test these levels?'*",
            "",
            "---",
            "*Important Reminder: This explanation is designed to help you understand your report, but your doctor knows your complete medical history best. Always discuss these results with your healthcare provider before making any changes.*"
        ])

        if err_msg:
            lines.insert(0, f"> ℹ️ *Generated via Built-in Plain Language Engine (Gemini Notice: {err_msg})*\n")
        elif not self.api_key:
            lines.insert(0, "> ℹ️ *Generated via Built-in Plain Language Engine. Add your `GEMINI_API_KEY` in `.env` for generative LLM explanations.*\n")

        return "\n".join(lines)


# Singleton instance
_gemini_client_instance = None


def get_gemini_client() -> GeminiMedicalClient:
    global _gemini_client_instance
    if _gemini_client_instance is None:
        _gemini_client_instance = GeminiMedicalClient()
    return _gemini_client_instance
