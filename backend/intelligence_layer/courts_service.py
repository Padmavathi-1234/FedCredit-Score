"""
Courts / Legal Risk Service — simulates a court-case lookup API.
Returns court case count and legal risk indicators.
"""

import random
import hashlib
from typing import Dict, Any


def get_court_cases(company_name: str = "", gstin: str = "") -> Dict[str, Any]:
    """Return simulated court case data."""
    seed = int(hashlib.md5((company_name + gstin).encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    case_count = rng.randint(0, 3)  # keep low for demo
    legal_risk = round(case_count * rng.uniform(1.0, 2.5), 1)

    cases = []
    case_types = ["Civil Suit", "Tax Dispute", "Consumer Complaint", "Contractual Dispute"]
    for i in range(case_count):
        cases.append({
            "case_type": rng.choice(case_types),
            "status": rng.choice(["Pending", "Resolved", "Under Review"]),
            "year": rng.randint(2020, 2025),
        })

    return {
        "court_cases": case_count,
        "legal_risk_score": min(legal_risk, 10),
        "cases": cases,
        "source": "simulated_courts_api",
    }
