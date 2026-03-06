"""
Bank Scoring Models — three simulated bank models that each
produce a credit score from 0 to 1000 based on different factors.
"""

import numpy as np
from typing import Dict, Any


def _clamp(value: float, lo: float = 0, hi: float = 1000) -> float:
    return max(lo, min(hi, value))


def bank1_financial_ratios(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Bank 1 — scores primarily on financial ratios.
    Weights: turnover (30%), debt ratio (30%), profit margin (25%), capacity (15%)
    """
    base = 500  # neutral starting point

    turnover = financial_data.get("turnover", 0)
    debt_ratio = financial_data.get("debt_ratio", 0.5)
    profit_margin = financial_data.get("profit_margin", 0.10)
    cap_str = str(financial_data.get("capacity_utilization", "50%"))
    capacity = float(cap_str.replace("%", "")) / 100 if "%" in cap_str else 0.5

    # Turnover component: higher is better, log scale
    turnover_score = min(300, np.log1p(turnover / 1_000_000) * 60)

    # Debt component: lower is better
    debt_score = max(0, 300 * (1 - debt_ratio))

    # Profit margin component: higher is better
    profit_score = min(250, profit_margin * 1000)

    # Capacity component
    capacity_score = capacity * 150

    total = _clamp(base * 0.2 + turnover_score + debt_score + profit_score + capacity_score)

    return {
        "bank_name": "National Financial Bank",
        "bank_id": "bank_1",
        "score": round(total),
        "focus": "Financial Ratios",
        "components": {
            "turnover_score": round(turnover_score, 1),
            "debt_score": round(debt_score, 1),
            "profit_score": round(profit_score, 1),
            "capacity_score": round(capacity_score, 1),
        },
    }


def bank2_compliance_legal(intelligence: Dict[str, Any]) -> Dict[str, Any]:
    """
    Bank 2 — scores primarily on compliance and legal signals.
    Weights: MCA compliance (50%), court risk (30%), GST status (20%)
    """
    mca = intelligence.get("mca_compliance", 5)
    court_cases = intelligence.get("court_cases", 0)
    legal_risk = intelligence.get("legal_risk_score", 0)

    compliance_score = mca * 50  # 0-500
    legal_penalty = min(300, legal_risk * 30 + court_cases * 40)
    gst_bonus = 100 if intelligence.get("gst_return_status") == "Filed" else 0

    total = _clamp(compliance_score - legal_penalty + gst_bonus + 100)

    return {
        "bank_name": "Regulatory Trust Bank",
        "bank_id": "bank_2",
        "score": round(total),
        "focus": "Compliance & Legal",
        "components": {
            "compliance_score": round(compliance_score, 1),
            "legal_penalty": round(legal_penalty, 1),
            "gst_bonus": round(gst_bonus, 1),
        },
    }


def bank3_market_sentiment(intelligence: Dict[str, Any]) -> Dict[str, Any]:
    """
    Bank 3 — scores primarily on market sentiment and satellite activity.
    Weights: news sentiment (40%), satellite NDVI (35%), overall market (25%)
    """
    sentiment = intelligence.get("news_sentiment", 0)  # -10 to +10
    ndvi = intelligence.get("ndvi_activity", 0.5)  # 0 to 1

    # Normalize sentiment to 0-400
    sentiment_score = ((sentiment + 10) / 20) * 400

    # NDVI score
    ndvi_score = ndvi * 350

    # Market baseline
    market_base = 200

    total = _clamp(sentiment_score + ndvi_score + market_base)

    return {
        "bank_name": "Market Intelligence Bank",
        "bank_id": "bank_3",
        "score": round(total),
        "focus": "Market & Satellite Intelligence",
        "components": {
            "sentiment_score": round(sentiment_score, 1),
            "ndvi_score": round(ndvi_score, 1),
            "market_base": round(market_base, 1),
        },
    }
