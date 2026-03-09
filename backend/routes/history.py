import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import User, AnalysisSession, AnalysisMessage

router = APIRouter()

@router.get("/api/history")
def get_user_history(db: Session = Depends(get_db)):
    """Fetch all analysis sessions for the current user, ordered by most recent."""
    sessions = (
        db.query(AnalysisSession)
        .order_by(AnalysisSession.last_updated.desc())
        .all()
    )
    
    return [
        {
            "id": session.id,
            "company_name": session.company_name,
            "gstin": session.gstin,
            "location": session.location,
            "created_at": session.created_at,
            "last_updated": session.last_updated
        }
        for session in sessions
    ]

@router.get("/api/analysis/{session_id}")
def get_analysis_session(session_id: str, db: Session = Depends(get_db)):
    """Fetch a specific session and all its messages."""
    session = db.query(AnalysisSession).filter(
        AnalysisSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Analysis session not found")
        
    messages = db.query(AnalysisMessage).filter(AnalysisMessage.session_id == session.id).order_by(AnalysisMessage.timestamp.asc()).all()
    
    return {
        "session_info": {
            "id": session.id,
            "company_name": session.company_name,
            "gstin": session.gstin,
            "location": session.location,
            "created_at": session.created_at,
            "last_updated": session.last_updated
        },
        "messages": [
            {
                "id": msg.id,
                "message_type": msg.message_type,
                "content": json.loads(msg.content),
                "timestamp": msg.timestamp
            }
            for msg in messages
        ]
    }

@router.delete("/api/analysis/{session_id}")
def delete_analysis_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a complete analysis session."""
    session = db.query(AnalysisSession).filter(
        AnalysisSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Analysis session not found")
        
    db.delete(session)
    db.commit()
    
    return {"status": "success", "message": "Session deleted"}
