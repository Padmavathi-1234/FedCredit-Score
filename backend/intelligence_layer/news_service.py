"""
News Sentiment Service — simulates a news-sentiment API.
Returns a sentiment score between -10 and +10.
"""

import random
import hashlib
from typing import Dict, Any


def get_news_sentiment(company_name: str = "", gstin: str = "") -> Dict[str, Any]:
    """Return simulated news sentiment for a company."""
    # Use a seed derived from the company identifier so results are
    # deterministic for the same input (good for demos).
    seed = int(hashlib.md5((company_name + gstin).encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    sentiment_score = round(rng.uniform(-3, 9), 1)  # skew positive for demo

    headlines = [
        {"title": f"{company_name or 'Company'} reports strong quarterly growth", "sentiment": "positive"},
        {"title": f"Industry outlook remains stable for FY2025", "sentiment": "neutral"},
        {"title": f"{company_name or 'Company'} expands operations to new markets", "sentiment": "positive"},
    ]

    if sentiment_score < 0:
        headlines.append(
            {"title": f"Concerns raised over {company_name or 'Company'} debt levels", "sentiment": "negative"}
        )

    return {
        "news_sentiment": sentiment_score,
        "headline_count": len(headlines),
        "headlines": headlines,
        "source": "simulated_news_api",
    }
