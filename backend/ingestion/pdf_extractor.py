"""
Digital PDF Text & Table Extractor
Extracts structured text and tabular data from selectable/digital PDF medical reports.
"""
import logging
from pathlib import Path
from typing import Tuple, Dict, Any, List

import pypdf
import pdfplumber

logger = logging.getLogger(__name__)


def check_pdf_has_text(pdf_path: Path) -> Tuple[bool, int, int]:
    """
    Quickly checks whether the PDF contains a selectable text layer.
    Returns:
        (has_text: bool, character_count: int, page_count: int)
    """
    total_chars = 0
    page_count = 0
    try:
        reader = pypdf.PdfReader(str(pdf_path))
        page_count = len(reader.pages)
        for page in reader.pages:
            text = page.extract_text() or ""
            total_chars += len(text.strip())
        return (total_chars > 80), total_chars, page_count
    except Exception:
        return False, 0, 0


def extract_text_from_pdf(pdf_path: Path) -> Tuple[str, Dict[str, Any]]:
    """
    Extracts text and table structures from a digital PDF file using pdfplumber.
    Preserves lines and table layouts across all pages.
    """
    extracted_text_blocks: List[str] = []
    metadata: Dict[str, Any] = {
        "page_count": 0,
        "tables_found": 0,
        "source": "pdfplumber",
        "pages_processed": 0,
        "total_characters": 0,
        "per_page_characters": []
    }

    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            metadata["page_count"] = len(pdf.pages)
            for idx, page in enumerate(pdf.pages):
                page_header = f"--- Page {idx + 1} ---"
                extracted_text_blocks.append(page_header)

                tables = page.extract_tables()
                if tables:
                    metadata["tables_found"] += len(tables)
                    for table in tables:
                        table_lines = []
                        for row in table:
                            cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]
                            if any(cleaned_row):
                                table_lines.append(" | ".join(cleaned_row))
                        if table_lines:
                            extracted_text_blocks.append("\n".join(table_lines))

                raw_page_text = page.extract_text(layout=True) or ""
                if raw_page_text.strip():
                    extracted_text_blocks.append(raw_page_text.strip())

                page_char_count = len((raw_page_text or "").strip())
                metadata["per_page_characters"].append({"page": idx + 1, "characters": page_char_count})
                metadata["total_characters"] += page_char_count
                metadata["pages_processed"] += 1

                logger.info("PDF page processed: page=%s characters=%s", idx + 1, page_char_count)

    except Exception as e:
        try:
            reader = pypdf.PdfReader(str(pdf_path))
            metadata["page_count"] = len(reader.pages)
            metadata["source"] = "pypdf_fallback"
            for idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    extracted_text_blocks.append(f"--- Page {idx + 1} ---\n" + text.strip())
                page_char_count = len(text.strip())
                metadata["per_page_characters"].append({"page": idx + 1, "characters": page_char_count})
                metadata["total_characters"] += page_char_count
                metadata["pages_processed"] += 1
                logger.info("PDF page processed via fallback: page=%s characters=%s", idx + 1, page_char_count)
        except Exception as fallback_err:
            extracted_text_blocks.append(f"Error extracting PDF: {str(e)} / {str(fallback_err)}")
            logger.warning("PDF extraction failed: %s / %s", e, fallback_err)

    full_text = "\n\n".join(extracted_text_blocks).strip()
    metadata["total_characters"] = len(full_text)
    logger.info("PDF extraction complete: pages=%s total_characters=%s", metadata.get("pages_processed", 0), metadata["total_characters"])
    return full_text, metadata
