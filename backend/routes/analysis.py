"""
Analysis Route — handles report generation and download.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.routes.upload import get_analysis_store
from backend.report_generation.report_builder import generate_report

router = APIRouter()


@router.get("/api/report/{analysis_id}")
async def download_report(analysis_id: str):
    """Generate and return the PDF credit report for a completed analysis."""
    store = get_analysis_store()
    result = store.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")

    pdf_bytes = generate_report(result)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="FedCredit_Report_{analysis_id[:8]}.pdf"'
        },
    )
