"""
Satellite / NDVI Activity Service — simulates a satellite-imagery API.
Returns an NDVI activity score between 0 and 1.
"""

import random
import hashlib
from typing import Dict, Any


def get_satellite_activity(location: str = "", company_name: str = "") -> Dict[str, Any]:
    """Return simulated satellite NDVI activity score."""
    seed = int(hashlib.md5((location + company_name).encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    ndvi = round(rng.uniform(0.4, 0.95), 2)
    activity_level = "High" if ndvi > 0.7 else ("Moderate" if ndvi > 0.4 else "Low")

    return {
        "ndvi_activity": ndvi,
        "activity_level": activity_level,
        "location_analyzed": location or "N/A",
        "imagery_date": "2025-12-15",
        "source": "simulated_satellite_api",
    }
