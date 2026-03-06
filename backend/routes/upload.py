"""
Upload Route — handles file upload and orchestrates
the full analysis pipeline.
"""

import os
import uuid
import json
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from backend.document_processing.pdf_processor import process_pdf
from backend.document_processing.excel_processor import process_excel
from backend.document_processing.doc_processor import process_docx

from backend.intelligence_layer.news_service import get_news_sentiment
from backend.intelligence_layer.compliance_service import get_compliance_score
from backend.intelligence_layer.satellite_service import get_satellite_activity
from backend.intelligence_layer.courts_service import get_court_cases

from backend.scoring_engine.federated_scoring import compute_federated_score

router = APIRouter()

# In-memory store for demo (maps analysis_id → result)
_analysis_store: dict = {}


def get_analysis_store():
    return _analysis_store


def _process_file(file_path: str, filename: str) -> dict:
    """Route a file to the appropriate processor based on extension."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return process_pdf(file_path)
    elif ext in (".doc", ".docx"):
        return process_docx(file_path)
    elif ext in (".xls", ".xlsx"):
        return process_excel(file_path)
    else:
        return {"error": f"Unsupported file type: {ext}"}


def _merge_financial_data(results: list) -> dict:
    """Merge extracted data from multiple documents into a single dict."""
    merged: dict = {}
    for r in results:
        for key in ["turnover", "debt_ratio", "profit_margin",
                     "capacity_utilization", "total_assets",
                     "total_liabilities", "audit_notes"]:
            if key in r and key not in merged:
                merged[key] = r[key]
    return merged


@router.post("/api/upload")
async def upload_and_analyze(
    files: List[UploadFile] = File(...),
    gstin: str = Form(""),
    location: str = Form(""),
    insights: str = Form(""),
):
    """
    Accept uploaded financial documents + company info,
    run the full pipeline, and return analysis results.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    analysis_id = str(uuid.uuid4())
    doc_results = []

    # 1. Process each uploaded document
    with tempfile.TemporaryDirectory() as tmp_dir:
        for f in files:
            tmp_path = os.path.join(tmp_dir, f.filename)
            content = await f.read()
            with open(tmp_path, "wb") as fp:
                fp.write(content)
            result = _process_file(tmp_path, f.filename)
            result["filename"] = f.filename
            doc_results.append(result)

    # 2. Merge financial data from all documents
    financial_data = _merge_financial_data(doc_results)

    # Apply defaults if not extracted
    financial_data.setdefault("turnover", 52_000_000)
    financial_data.setdefault("debt_ratio", 0.42)
    financial_data.setdefault("profit_margin", 0.18)
    financial_data.setdefault("capacity_utilization", "80%")

    # Parse capacity from user insights if provided
    if insights:
        import re
        m = re.search(r"(\d+)\s*%\s*capacity", insights, re.IGNORECASE)
        if m:
            financial_data["capacity_utilization"] = f"{m.group(1)}%"

    # 3. Gather external intelligence signals
    company_name = gstin or "DemoCompany"
    news = get_news_sentiment(company_name, gstin)
    compliance = get_compliance_score(gstin, company_name)
    satellite = get_satellite_activity(location, company_name)
    courts = get_court_cases(company_name, gstin)

    intelligence = {
        "news_sentiment": news["news_sentiment"],
        "headlines": news["headlines"],
        "mca_compliance": compliance["mca_compliance"],
        "gst_return_status": compliance["gst_return_status"],
        "filings_on_time": compliance["filings_on_time"],
        "filings_total": compliance["filings_total"],
        "court_cases": courts["court_cases"],
        "legal_risk_score": courts["legal_risk_score"],
        "cases": courts["cases"],
        "ndvi_activity": satellite["ndvi_activity"],
        "activity_level": satellite["activity_level"],
    }

    # 4. Compute federated score
    scoring = compute_federated_score(financial_data, intelligence)

    # 5. Assemble final result
    result = {
        "analysis_id": analysis_id,
        "company_info": {
            "gstin": gstin,
            "location": location,
            "insights": insights,
        },
        "documents_processed": [
            {"filename": r.get("filename", ""), "source": r.get("source", "unknown")}
            for r in doc_results
        ],
        "financial_data": financial_data,
        "intelligence": intelligence,
        "scoring": scoring,
    }

    # Store for later PDF generation
    _analysis_store[analysis_id] = result

    return JSONResponse(content=result)
