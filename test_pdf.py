import os
import sys
import json

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from backend.database.database import SessionLocal
from backend.database.models import AnalysisMessage
from backend.report_generation.report_builder import generate_report

def main():
    db = SessionLocal()
    # Get the latest analysis
    msg = db.query(AnalysisMessage).filter(
        AnalysisMessage.message_type == "analysis_result"
    ).order_by(AnalysisMessage.id.desc()).first()
    
    if not msg:
        print("No analysis found")
        return
        
    print(f"Generating PDF for {msg.session_id}...")
    result = json.loads(msg.content)
    try:
        pdf_bytes = generate_report(result)
        with open("test_report.pdf", "wb") as f:
            f.write(pdf_bytes)
        print(f"PDF generated successfully, size: {len(pdf_bytes)} bytes")
    except Exception as e:
        print(f"Failed to generate report: {e}")

if __name__ == "__main__":
    main()
