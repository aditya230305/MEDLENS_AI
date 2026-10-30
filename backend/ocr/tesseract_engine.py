"""
Tesseract OCR Engine Module
Provides image preprocessing, Tesseract binary discovery, and text extraction from images/scans.
"""
import shutil
import logging
from pathlib import Path
from typing import Tuple, List, Optional
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from backend.config import TESSERACT_CMD

logger = logging.getLogger(__name__)

# Search common paths for tesseract binary on macOS and Linux
COMMON_TESSERACT_PATHS = [
    TESSERACT_CMD,
    "/opt/homebrew/bin/tesseract",
    "/usr/local/bin/tesseract",
    "/usr/bin/tesseract"
]


def find_tesseract_binary() -> Optional[str]:
    """Finds the tesseract executable on the system."""
    for path in COMMON_TESSERACT_PATHS:
        if path and Path(path).is_file():
            return str(path)
    # Check PATH
    which_path = shutil.which("tesseract")
    if which_path:
        return which_path
    return None


def is_tesseract_available() -> bool:
    """Returns True if Tesseract executable is present on the host system."""
    binary = find_tesseract_binary()
    return binary is not None


# Configure pytesseract path if discovered
_detected_bin = find_tesseract_binary()
if _detected_bin:
    pytesseract.pytesseract.tesseract_cmd = _detected_bin


def preprocess_image_for_ocr(img: Image.Image) -> Image.Image:
    """
    Applies image enhancement pipeline to maximize OCR character recognition:
    1. Convert to Grayscale
    2. Increase contrast
    3. Moderate sharpening to clarify blurry scan fonts
    """
    # Convert to grayscale
    gray = img.convert("L")

    # Increase contrast
    enhancer = ImageEnhance.Contrast(gray)
    enhanced = enhancer.enhance(1.8)

    # Moderate sharpening
    sharpened = enhanced.filter(ImageFilter.SHARPEN)
    return sharpened


def extract_text_from_image(image_path: Path) -> Tuple[str, float]:
    """
    Loads an image, preprocesses it, and runs Tesseract OCR.
    Returns:
        (extracted_text: str, average_confidence: float)
    """
    if not is_tesseract_available():
        return (
            "OCR Error: Tesseract executable not detected on system.\n"
            "To enable OCR on scanned images, please run: brew install tesseract",
            0.0
        )

    try:
        with Image.open(str(image_path)) as img:
            processed_img = preprocess_image_for_ocr(img)

            # Extract detailed OCR data to calculate mean confidence
            data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)
            confidences = [int(c) for c in data.get("conf", []) if str(c).lstrip("-").isdigit() and int(c) >= 0]
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

            # Extract full text
            text = pytesseract.image_to_string(processed_img, config="--psm 6")
            return text.strip(), avg_conf
    except Exception as e:
        logger.error(f"Error during OCR execution: {e}")
        return f"OCR Processing Exception: {str(e)}", 0.0


def extract_text_from_scanned_pdf(pdf_path: Path) -> Tuple[str, int]:
    """
    Renders scanned PDF pages to raster images using pypdfium2 and executes OCR on each page.
    Returns:
        (combined_text: str, total_pages_processed: int)
    """
    if not is_tesseract_available():
        return ("OCR Error: Tesseract not available.", 0)

    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(str(pdf_path))
        page_texts: List[str] = []
        total_chars = 0

        for idx, page in enumerate(pdf):
            pil_image = page.render(scale=300/72).to_pil_image()
            processed_img = preprocess_image_for_ocr(pil_image)
            page_text = pytesseract.image_to_string(processed_img, config="--psm 6")
            cleaned_page_text = page_text.strip()
            if cleaned_page_text:
                page_texts.append(f"--- Scanned Page {idx + 1} ---\n" + cleaned_page_text)
            total_chars += len(cleaned_page_text)
            logger.info("Scanned PDF page OCR complete: page=%s characters=%s", idx + 1, len(cleaned_page_text))

        logger.info("Scanned PDF OCR complete: pages=%s total_characters=%s", len(pdf), total_chars)
        return "\n\n".join(page_texts), len(pdf)
    except Exception as e:
        logger.error(f"Error extracting scanned PDF: {e}")
        return f"Scanned PDF OCR Error: {str(e)}", 0
