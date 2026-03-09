"""
Upload Route — handles file upload and orchestrates
the full analysis pipeline with extraction, cleaning,
validation, verification, and scoring.
"""

import os
import uuid
import json
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import User, AnalysisSession, AnalysisMessage
from fastapi.responses import JSONResponse

from backend.document_processing.pdf_processor import process_pdf
from backend.document_processing.excel_processor import process_excel
from backend.document_processing.doc_processor import process_docx
from backend.document_processing.csv_processor import process_csv
from backend.document_processing.ocr_processor import process_image
from backend.document_processing.data_cleaning import clean_financial_data, validate_gstin_format

from backend.intelligence_layer.news_service import get_news_sentiment
from backend.intelligence_layer.compliance_service import get_compliance_score
from backend.intelligence_layer.satellite_service import get_satellite_activity
from backend.intelligence_layer.courts_service import get_court_cases
from backend.intelligence_layer.gstin_verification import verify_company

from backend.scoring_engine.federated_scoring import compute_federated_score

router = APIRouter()

# Removed file-based get_analysis_store


def _process_file(file_path: str, filename: str) -> dict:
    """Route a file to the appropriate processor based on extension."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return process_pdf(file_path)
    elif ext in (".doc", ".docx"):
        return process_docx(file_path)
    elif ext in (".xls", ".xlsx"):
        return process_excel(file_path)
    elif ext == ".csv":
        return process_csv(file_path)
    elif ext in (".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"):
        return process_image(file_path)
    else:
        return {"error": f"Unsupported file type: {ext}"}


def _merge_financial_data(results: list) -> dict:
    """Merge extracted data from multiple documents into a single dict."""
    merged: dict = {}
    for r in results:
        for key in ["turnover", "debt_ratio", "profit_margin",
                     "capacity_utilization", "total_assets",
                     "total_liabilities", "audit_notes",
                     "gstin_extracted", "company_name_extracted",
                     "address_extracted"]:
            if key in r and key not in merged:
                merged[key] = r[key]
    return merged


@router.post("/api/extract-fields")
async def extract_fields(files: List[UploadFile] = File(...)):
    """
    Lightweight endpoint: process uploaded files and return only
    auto-detected fields (GSTIN, company name, address).
    Called immediately after files are selected/dropped—before analysis.
    """
    if not files:
        return JSONResponse(content={"extracted_fields": {}})

    doc_results = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        for f in files:
            tmp_path = os.path.join(tmp_dir, f.filename)
            content = await f.read()
            with open(tmp_path, "wb") as fp:
                fp.write(content)
            result = _process_file(tmp_path, f.filename)
            doc_results.append(result)

    merged = _merge_financial_data(doc_results)

    extracted: dict = {}
    if merged.get("gstin_extracted"):
        extracted["gstin"] = merged["gstin_extracted"]
    if merged.get("company_name_extracted"):
        extracted["company_name"] = merged["company_name_extracted"]
    if merged.get("address_extracted"):
        extracted["location"] = merged["address_extracted"]

    return JSONResponse(content={"extracted_fields": extracted})


@router.post("/api/upload")
async def upload_and_analyze(
    files: List[UploadFile] = File(...),
    gstin: str = Form(""),
    location: str = Form(""),
    insights: str = Form(""),
    db: Session = Depends(get_db)
):
    """
    Accept uploaded financial documents + company info,
    run the full pipeline, and return analysis results.

    Pipeline: Extract → Clean → Validate → Verify → Score
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    analysis_id = str(uuid.uuid4())
    doc_results = []
    
    # ══════════════════════════════════════════════════
    # DB: Initialize Session
    # ══════════════════════════════════════════════════
    session_record = AnalysisSession(
        id=analysis_id,
        company_name=gstin,
        gstin=gstin,
        location=location
    )
    db.add(session_record)
    db.commit()

    msg1 = AnalysisMessage(
        session_id=analysis_id,
        message_type="user_upload",
        content=json.dumps({"message": f"User uploaded {len(files)} files.", "files": [f.filename for f in files]})
    )
    db.add(msg1)
    db.commit()

    # ══════════════════════════════════════════════════
    # STAGE 1: Document Processing & Data Extraction
    # ══════════════════════════════════════════════════
    with tempfile.TemporaryDirectory() as tmp_dir:
        for f in files:
            tmp_path = os.path.join(tmp_dir, f.filename)
            content = await f.read()
            with open(tmp_path, "wb") as fp:
                fp.write(content)
            result = _process_file(tmp_path, f.filename)
            result["filename"] = f.filename
            doc_results.append(result)

    # Check for processing errors
    processing_errors = [
        r for r in doc_results if "error" in r and r["error"]
    ]
    if processing_errors and len(processing_errors) == len(doc_results):
        return JSONResponse(
            status_code=400,
            content={
                "error_type": "processing_error",
                "errors": [
                    f"Failed to process '{r.get('filename', 'unknown')}': {r['error']}"
                    for r in processing_errors
                ],
                "extracted_fields": {},
            },
        )

    # ══════════════════════════════════════════════════
    # STAGE 2: Merge & Auto-populate extracted fields
    # ══════════════════════════════════════════════════
    financial_data = _merge_financial_data(doc_results)

    # Auto-populate GSTIN and location from documents if user left them empty
    extracted_fields = {}
    if not gstin and financial_data.get("gstin_extracted"):
        gstin = financial_data["gstin_extracted"]
        extracted_fields["gstin"] = gstin
    if not location and financial_data.get("address_extracted"):
        location = financial_data["address_extracted"]
        extracted_fields["location"] = location
    if financial_data.get("company_name_extracted"):
        extracted_fields["company_name"] = financial_data["company_name_extracted"]

    # ══════════════════════════════════════════════════
    # STAGE 2.5: AI Financial Data Extraction
    # ══════════════════════════════════════════════════
    combined_text = "\n".join(r.get("raw_text", "") for r in doc_results if "raw_text" in r)
    if combined_text:
        try:
            from backend.intelligence_layer.llm_service import is_ollama_available, extract_financial_data
            if is_ollama_available():
                llm_finance = extract_financial_data(combined_text)
                if llm_finance:
                    for k in ["turnover", "debt_ratio", "profit_margin", "capacity_utilization", "total_assets", "total_liabilities"]:
                        if k in llm_finance and llm_finance[k] is not None:
                            financial_data[k] = llm_finance[k]
        except Exception as e:
            pass

    # Parse capacity from user insights if provided
    if insights:
        import re
        m = re.search(r"(\d+)\s*%\s*capacity", insights, re.IGNORECASE)
        if m:
            financial_data["capacity_utilization"] = f"{m.group(1)}%"

    # ══════════════════════════════════════════════════
    # STAGE 3: Data Cleaning & Pre-processing
    # ══════════════════════════════════════════════════
    cleaning_result = clean_financial_data(financial_data)
    cleaned_data = cleaning_result["cleaned_data"]
    cleaning_report = cleaning_result["cleaning_report"]
    cleaning_warnings = cleaning_result["warnings"]

    # Use cleaned data going forward, but preserve defaults
    for key in ["turnover", "debt_ratio", "profit_margin", "capacity_utilization",
                "total_assets", "total_liabilities", "audit_notes"]:
        if key in cleaned_data:
            financial_data[key] = cleaned_data[key]

    # ══════════════════════════════════════════════════
    # STAGE 4: Mandatory Fields Validation
    # ══════════════════════════════════════════════════
    validation_errors = []

    if not gstin:
        validation_errors.append(
            "GSTIN / CIN is required. Please enter the company's GSTIN or it will be auto-detected from documents."
        )

    if not location:
        validation_errors.append(
            "Company location is required. Please enter the city and state of the company."
        )

    if not insights or len(insights.strip()) < 10:
        validation_errors.append(
            "Officer insights are required. Please provide a detailed assessment of the company (at least 10 characters)."
        )

    # Validation of user inputs is completed.

    if validation_errors:
        return JSONResponse(
            status_code=400,
            content={
                "error_type": "validation_error",
                "errors": validation_errors,
                "extracted_fields": extracted_fields,
                "cleaning_warnings": cleaning_warnings,
            },
        )

    # ══════════════════════════════════════════════════
    # STAGE 5: GSTIN Format Validation
    # ══════════════════════════════════════════════════
    is_valid_gstin, gstin_error = validate_gstin_format(gstin)
    if not is_valid_gstin:
        return JSONResponse(
            status_code=400,
            content={
                "error_type": "gstin_format_error",
                "errors": [gstin_error],
                "extracted_fields": extracted_fields,
            },
        )

    # ══════════════════════════════════════════════════
    # STAGE 6: Company Verification
    # ══════════════════════════════════════════════════
    verification = verify_company(gstin, location)
    if not verification["valid"]:
        return JSONResponse(
            status_code=422,
            content={
                "error_type": "verification_error",
                "errors": verification["errors"],
                "details": verification["details"],
                "extracted_fields": extracted_fields,
            },
        )

    # ══════════════════════════════════════════════════
    # STAGE 7: External Intelligence & Scoring
    # ══════════════════════════════════════════════════
    company_name = extracted_fields.get("company_name", gstin)
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

    # Compute federated score (with officer insight adjustment)
    scoring = compute_federated_score(financial_data, intelligence, officer_insights=insights, gstin=gstin)

    # ══════════════════════════════════════════════════
    # STAGE 8: LLM Executive Summary (if Ollama available)
    # ══════════════════════════════════════════════════
    llm_executive_summary = None
    try:
        from backend.intelligence_layer.llm_service import (
            generate_executive_summary,
            is_ollama_available,
        )
        if is_ollama_available():
            llm_executive_summary = generate_executive_summary(
                company_name=extracted_fields.get("company_name", gstin),
                gstin=gstin,
                financial_data=financial_data,
                scoring=scoring,
                intelligence=intelligence,
            )
    except Exception:
        pass  # Graceful fallback - no LLM summary

    # ══════════════════════════════════════════════════
    # STAGE 9: Assemble final result
    # ══════════════════════════════════════════════════
    result = {
        "analysis_id": analysis_id,
        "company_info": {
            "gstin": gstin,
            "location": location,
            "insights": insights,
            "company_name": extracted_fields.get("company_name", ""),
        },
        "documents_processed": [
            {"filename": r.get("filename", ""), "source": r.get("source", "unknown")}
            for r in doc_results
        ],
        "financial_data": financial_data,
        "intelligence": intelligence,
        "scoring": scoring,
        "verification": verification["details"],
        "data_quality": {
            "cleaning_report": cleaning_report,
            "warnings": cleaning_warnings,
        },
        "extracted_fields": extracted_fields,
        "llm_executive_summary": llm_executive_summary,
    }

    # Update Session Information
    session_record.company_name = extracted_fields.get("company_name", gstin)
    session_record.gstin = extracted_fields.get("gstin", gstin)
    session_record.location = extracted_fields.get("location", location)

    msg2 = AnalysisMessage(
        session_id=analysis_id,
        message_type="extracted_data",
        content=json.dumps(extracted_fields)
    )
    db.add(msg2)

    msg3 = AnalysisMessage(
        session_id=analysis_id,
        message_type="analysis_result",
        content=json.dumps(result)
    )
    db.add(msg3)
    db.commit()

    return JSONResponse(content=result)
