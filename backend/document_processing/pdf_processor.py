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

    # Total assets
    m = re.search(
        r"(?:total\s*assets)[\s:₹$]*?([\d,]+(?:\.\d+)?)", text, re.IGNORECASE
    )
    if m:
        data["total_assets"] = float(m.group(1).replace(",", ""))

    # Total liabilities
    m = re.search(
        r"(?:total\s*liabilities)[\s:₹$]*?([\d,]+(?:\.\d+)?)", text, re.IGNORECASE
    )
    if m:
        data["total_liabilities"] = float(m.group(1).replace(",", ""))

    # Audit notes (grab first sentence that mentions audit)
    m = re.search(r"([^.]*audit[^.]*\.)", text, re.IGNORECASE)
    if m:
        data["audit_notes"] = m.group(1).strip()

    # ── Auto-extract GSTIN ──
    gstin_match = re.search(
        r'\b(\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z])\b', text
    )
    if gstin_match:
        data["gstin_extracted"] = gstin_match.group(1)

    # ── Auto-extract Company Name ──
    for pattern in [
        r"(?:company\s*name|firm\s*name|business\s*name|name\s*of\s*(?:the\s*)?company|entity\s*name)[\s:]+([A-Z][A-Za-z\s&.,\-()]+?)(?:\n|$|(?:\s{2,}))",
        r"M/s\.?\s+([A-Z][A-Za-z\s&.,\-()]+?)(?:\n|$)",
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            name = m.group(1).strip().rstrip(".,")
            if len(name) > 2:
                data["company_name_extracted"] = name
                break

    # ── Auto-extract Address ──
    for pattern in [
        r"(?:registered\s*(?:office|address)|business\s*address|address|location)[\s:]+(.+?)(?:\n\n|\n(?=[A-Z]))",
        r"(?:registered\s*(?:office|address)|business\s*address|address)[\s:]+(.+?)(?:\n|$)",
    ]:
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if m:
            addr = m.group(1).strip().replace("\n", ", ").rstrip(".,")
            if len(addr) > 5:
                data["address_extracted"] = addr
                break

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
