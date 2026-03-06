"""
MCA Compliance Service — simulates an MCA / ROC compliance API.
Returns a compliance score between 0 and 10.
"""

import random
import hashlib
from typing import Dict, Any


def get_compliance_score(gstin: str = "", company_name: str = "") -> Dict[str, Any]:
    """Return simulated MCA compliance score."""
    seed = int(hashlib.md5((gstin + company_name).encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    score = round(rng.uniform(5, 10), 1)  # skew high for demo
    filings_on_time = rng.randint(8, 12)
    filings_total = 12

    return {
        "mca_compliance": score,
        "filings_on_time": filings_on_time,
        "filings_total": filings_total,
        "gst_return_status": "Filed" if score > 6 else "Pending",
        "director_disqualification": False,
        "source": "simulated_mca_api",
    }
