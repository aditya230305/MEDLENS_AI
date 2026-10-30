"""
File Router Module
Determines file type (PDF vs Image) and routes to direct digital extraction or OCR.
"""
import os
import shutil
from pathlib import Path
from typing import Dict, Any, Tuple
from backend.ingestion.pdf_extractor import extract_text_from_pdf, check_pdf_has_text
from backend.ocr.tesseract_engine import extract_text_from_image, is_tesseract_available


SUPPORTED_EXTENSIONS = {
    "pdf": [".pdf"],
    "image": [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"]
}


def inspect_and_route_file(file_path: Path) -> Dict[str, Any]:
    """
    Inspects the file type and routes to direct PDF extraction or OCR.
    Returns:
        dict: {
            "file_name": str,
            "file_type": "digital_pdf" | "scanned_pdf" | "image" | "unsupported",
            "raw_text": str,
            "extraction_method": str,
            "page_count": int,
            "ocr_applied": bool,
            "notes": str
        }
    """
    ext = file_path.suffix.lower()

    if ext in SUPPORTED_EXTENSIONS["pdf"]:
        has_text, text_length, pages = check_pdf_has_text(file_path)
        if has_text and text_length > 100:
            # Digital PDF with selectable text layer
            raw_text, metadata = extract_text_from_pdf(file_path)
            return {
                "file_name": file_path.name,
                "file_type": "digital_pdf",
                "raw_text": raw_text,
                "extraction_method": "direct_digital_extraction (pdfplumber/pypdf)",
                "page_count": metadata.get("page_count", pages),
                "ocr_applied": False,
                "notes": f"Detected selectable text layer ({text_length} characters). Bypassed OCR."
            }
        else:
            # Scanned PDF without text layer
            if is_tesseract_available():
                # Extract text using OCR on rendered PDF pages
                from backend.ocr.tesseract_engine import extract_text_from_scanned_pdf
                raw_text, pages_processed = extract_text_from_scanned_pdf(file_path)
                return {
                    "file_name": file_path.name,
                    "file_type": "scanned_pdf",
                    "raw_text": raw_text,
                    "extraction_method": "tesseract_ocr (page rendering)",
                    "page_count": pages_processed,
                    "ocr_applied": True,
                    "notes": "Scanned PDF detected. Routed through Tesseract OCR."
                }
            else:
                # Fallback attempt direct extraction or warn
                raw_text, metadata = extract_text_from_pdf(file_path)
                return {
                    "file_name": file_path.name,
                    "file_type": "scanned_pdf",
                    "raw_text": raw_text,
                    "extraction_method": "direct_digital_fallback",
                    "page_count": metadata.get("page_count", 1),
                    "ocr_applied": False,
                    "notes": "Scanned PDF without text layer. Tesseract OCR is not installed; direct text fallback returned minimal text."
                }

    elif ext in SUPPORTED_EXTENSIONS["image"]:
        if is_tesseract_available():
            raw_text, confidence = extract_text_from_image(file_path)
            return {
                "file_name": file_path.name,
                "file_type": "image",
                "raw_text": raw_text,
                "extraction_method": "tesseract_ocr",
                "page_count": 1,
                "ocr_applied": True,
                "notes": f"Image report processed via Tesseract OCR (mean confidence: {confidence:.1f}%)."
            }
        else:
            return {
                "file_name": file_path.name,
                "file_type": "image",
                "raw_text": "",
                "extraction_method": "none",
                "page_count": 1,
                "ocr_applied": False,
                "notes": "Image report detected, but Tesseract binary is not installed on this system. Please run 'brew install tesseract'."
            }

    else:
        return {
            "file_name": file_path.name,
            "file_type": "unsupported",
            "raw_text": "",
            "extraction_method": "none",
            "page_count": 0,
            "ocr_applied": False,
            "notes": f"Unsupported file format '{ext}'. Supported formats: PDF, PNG, JPG, JPEG, TIFF."
        }
