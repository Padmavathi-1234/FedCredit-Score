"""
Analysis Route — handles report generation and download.
"""

import logging

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
import json

logger = logging.getLogger(__name__)

from backend.database.database import get_db
from backend.database.models import AnalysisMessage, User
from backend.report_generation.report_builder import generate_report

router = APIRouter()


@router.get("/api/report/{analysis_id}")
async def download_report(
    analysis_id: str,
    db: Session = Depends(get_db)
):
    """Generate and return the PDF credit report for a completed analysis."""
    message = db.query(AnalysisMessage).filter(
        AnalysisMessage.session_id == analysis_id,
        AnalysisMessage.message_type == "analysis_result"
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Analysis result not found")

    try:
        result = json.loads(message.content)
        pdf_bytes = generate_report(result)
    except Exception as e:
        logger.error(f"Failed to generate report for {analysis_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF report: {str(e)}"
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="FedCredit_CAM_Report_{analysis_id[:8]}.pdf"'
        },
    )
