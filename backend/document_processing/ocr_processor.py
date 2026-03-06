"""
OCR Processor — handles scanned PDFs by converting pages to images
and running Tesseract OCR with OpenCV preprocessing.
"""

import re
import tempfile
from pathlib import Path
from typing import Dict, Any

try:
    import fitz  # PyMuPDF – used to rasterise PDF pages
except ImportError:
    fitz = None

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None


def _preprocess_image(img_path: str):
    """Apply OpenCV preprocessing to improve OCR accuracy."""
    if cv2 is None or np is None:
        return img_path

    img = cv2.imread(img_path)
    if img is None:
        return img_path

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Adaptive threshold for better text contrast
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    processed_path = img_path.replace(".png", "_processed.png")
    cv2.imwrite(processed_path, thresh)
    return processed_path


def process_scanned_pdf(file_path: str) -> Dict[str, Any]:
    """Convert each page of a scanned PDF to an image and OCR it."""
    if fitz is None:
        return {
            "error": "PyMuPDF is required for scanned-PDF processing",
            "source": "ocr",
        }
    if pytesseract is None or Image is None:
        return {
            "error": "pytesseract / Pillow are required for OCR",
            "source": "ocr",
        }

    text_parts: list[str] = []

    try:
        doc = fitz.open(file_path)
        with tempfile.TemporaryDirectory() as tmp_dir:
            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=300)
                img_path = str(Path(tmp_dir) / f"page_{i}.png")
                pix.save(img_path)

                processed = _preprocess_image(img_path)
                page_text = pytesseract.image_to_string(Image.open(processed))
                text_parts.append(page_text)
        doc.close()
    except Exception as e:
        return {"error": str(e), "source": "ocr"}

    full_text = "\n".join(text_parts).strip()

    # Reuse the financial-value extractor from pdf_processor
    from backend.document_processing.pdf_processor import _extract_financial_values

    extracted = _extract_financial_values(full_text)
    extracted["raw_text"] = full_text[:3000]
    extracted["source"] = "ocr"
    return extracted
