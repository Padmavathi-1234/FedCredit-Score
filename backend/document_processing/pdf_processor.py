"""
PDF Processor — extracts text and tables from digital PDFs.
Falls back to OCR for scanned documents.
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


def _extract_financial_values(text: str) -> Dict[str, Any]:
    """Use regex/keyword matching to pull financial metrics from raw text."""
    data: Dict[str, Any] = {}

    # Turnover / Revenue
    for pattern in [
        r"(?:turnover|total\s*revenue|gross\s*revenue|net\s*revenue|total\s*sales)[\s:₹$]*?([\d,]+(?:\.\d+)?)",
        r"([\d,]+(?:\.\d+)?)\s*(?:crore|lakh|million)?\s*(?:turnover|revenue)",
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            data["turnover"] = float(m.group(1).replace(",", ""))
            break

    # Debt ratio
    for pattern in [
        r"(?:debt[\s\-]*(?:to[\s\-]*)?(?:equity|asset)?\s*ratio)[\s:]*?([\d.]+)",
        r"(?:leverage\s*ratio)[\s:]*?([\d.]+)",
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            data["debt_ratio"] = float(m.group(1))
            break

    # Profit margin
    for pattern in [
        r"(?:net\s*profit\s*margin|profit\s*margin|npm)[\s:%]*?([\d.]+)",
        r"(?:margin)[\s:%]*?([\d.]+)",
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            data["profit_margin"] = val / 100 if val > 1 else val
            break

    # Capacity utilization
    m = re.search(
        r"(?:capacity\s*utilization|utilization)[\s:%]*?([\d.]+)", text, re.IGNORECASE
    )
    if m:
        data["capacity_utilization"] = f"{m.group(1)}%"

    # Audit notes (grab first sentence that mentions audit)
    m = re.search(r"([^.]*audit[^.]*\.)", text, re.IGNORECASE)
    if m:
        data["audit_notes"] = m.group(1).strip()

    return data


def process_pdf(file_path: str) -> Dict[str, Any]:
    """Process a digital PDF and return structured financial data."""
    text_parts: list[str] = []
    tables: list = []

    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    # ----- Try PyMuPDF first -----
    if fitz is not None:
        try:
            doc = fitz.open(file_path)
            for page in doc:
                page_text = page.get_text()
                text_parts.append(page_text)
            doc.close()
        except Exception as e:
            text_parts.append(f"[PyMuPDF error: {e}]")

    # ----- Supplement with pdfplumber for tables -----
    if pdfplumber is not None:
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    if not text_parts:
                        t = page.extract_text()
                        if t:
                            text_parts.append(t)
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
        except Exception:
            pass

    full_text = "\n".join(text_parts).strip()

    # If we got very little text the PDF is likely scanned → delegate to OCR
    if len(full_text) < 50:
        from backend.document_processing.ocr_processor import process_scanned_pdf

        return process_scanned_pdf(file_path)

    extracted = _extract_financial_values(full_text)
    extracted["raw_text"] = full_text[:3000]  # cap for payload size
    extracted["tables"] = tables[:5]
    extracted["source"] = "digital_pdf"
    return extracted
