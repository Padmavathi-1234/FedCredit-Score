"""
Federated Scoring Engine — aggregates individual bank scores
into a single federated credit score with risk categorisation,
5Cs of Credit analysis, loan recommendation, and full explainability.
"""

from typing import Dict, Any, List

from backend.scoring_engine.bank_models import (
    bank1_financial_ratios,
    bank2_compliance_legal,
    bank3_market_sentiment,
)


def _risk_category(score: int) -> str:
    if score >= 700:
        return "Low Risk"
    elif score >= 400:
        return "Medium Risk"
    else:
        return "High Risk"


def _loan_recommendation(score: int) -> Dict[str, Any]:
    if score >= 700:
        return {
            "recommended_loan": "₹25 Crore",
            "interest_rate": "9.5%",
            "tenure": "5 Years",
            "approval_likelihood": "High",
            "explanation": "Strong financial health, low risk profile, and solid compliance record support a higher loan amount at competitive rates.",
        }
    elif score >= 500:
        return {
            "recommended_loan": "₹10 Crore",
            "interest_rate": "12.0%",
            "tenure": "3 Years",
            "approval_likelihood": "Moderate",
            "explanation": "Moderate financial standing with some areas for improvement. A shorter tenure with a moderate interest rate balances risk and opportunity.",
        }
    elif score >= 400:
        return {
            "recommended_loan": "₹5 Crore",
            "interest_rate": "14.5%",
            "tenure": "2 Years",
            "approval_likelihood": "Moderate-Low",
            "explanation": "The company shows mixed signals across financial and compliance dimensions. A smaller loan with higher rate and shorter tenure mitigates lender risk.",
        }
    else:
        return {
            "recommended_loan": "Not Recommended",
            "interest_rate": "N/A",
            "tenure": "N/A",
            "approval_likelihood": "Low",
            "explanation": "High risk indicators across multiple dimensions. The company should address financial health, compliance, and operational concerns before seeking credit.",
        }


def _compute_five_cs(
    financial_data: Dict[str, Any],
    intelligence: Dict[str, Any],
    bank_scores: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Compute the 5Cs of Credit Analysis:
    Character, Capacity, Capital, Collateral, Conditions
    Each scored 0-100 with detailed explanation.
    """
    # ── 1. CHARACTER (repayment history, compliance, legal standing) ──
    mca = intelligence.get("mca_compliance", 5)
    court_cases = intelligence.get("court_cases", 0)
    legal_risk = intelligence.get("legal_risk_score", 0)
    filings_on_time = intelligence.get("filings_on_time", 8)
    filings_total = intelligence.get("filings_total", 12)

    char_score = min(100, max(0,
        (mca / 10) * 40 +          # compliance weight
        max(0, (1 - court_cases / 5)) * 30 +  # legal weight
        (filings_on_time / max(filings_total, 1)) * 30  # filing diligence
    ))

    char_factors = []
    if mca >= 7:
        char_factors.append(f"MCA compliance score is strong at {mca}/10")
    elif mca >= 4:
        char_factors.append(f"MCA compliance score is moderate at {mca}/10")
    else:
        char_factors.append(f"MCA compliance score is weak at {mca}/10 — needs attention")

    if court_cases == 0:
        char_factors.append("No pending court cases — clean legal record")
    else:
        char_factors.append(f"{court_cases} court case(s) found — adds risk to credit profile")

    gst_status = intelligence.get("gst_return_status", "Unknown")
    char_factors.append(f"GST return status: {gst_status}")
    char_factors.append(f"Statutory filings: {filings_on_time}/{filings_total} on time")

    if char_score >= 70:
        char_explanation = "The company demonstrates strong character traits — consistent regulatory compliance, clean legal record, and timely statutory filings. This indicates a reliable borrower with a history of fulfilling obligations."
    elif char_score >= 40:
        char_explanation = "The company shows moderate character indicators. While compliance exists, there may be gaps in filings or minor legal issues. Improving compliance timeliness would strengthen this dimension."
    else:
        char_explanation = "Significant concerns exist in the character assessment. Legal issues, poor compliance scores, or late filings suggest risk of default. Remediation is recommended before credit approval."

    # ── 2. CAPACITY (ability to repay — profit margin, turnover, debt ratio) ──
    turnover = financial_data.get("turnover", 0)
    debt_ratio = financial_data.get("debt_ratio", 0.5)
    profit_margin = financial_data.get("profit_margin", 0.10)
    cap_str = str(financial_data.get("capacity_utilization", "50%"))
    capacity_util = float(cap_str.replace("%", "")) / 100 if "%" in cap_str else 0.5

    cap_score = min(100, max(0,
        min(30, profit_margin * 150) +        # profit margin
        max(0, (1 - debt_ratio) * 35) +       # low debt is good
        min(20, capacity_util * 25) +          # capacity usage
        min(15, (turnover / 100_000_000) * 15) # turnover scale
    ))

    cap_factors = []
    if profit_margin >= 0.15:
        cap_factors.append(f"Healthy profit margin of {profit_margin*100:.1f}% — strong earnings capacity")
    elif profit_margin >= 0.08:
        cap_factors.append(f"Moderate profit margin of {profit_margin*100:.1f}% — adequate cash generation")
    else:
        cap_factors.append(f"Low profit margin of {profit_margin*100:.1f}% — repayment ability may be constrained")

    if debt_ratio <= 0.4:
        cap_factors.append(f"Debt ratio of {debt_ratio:.2f} is conservative — low leverage risk")
    elif debt_ratio <= 0.6:
        cap_factors.append(f"Debt ratio of {debt_ratio:.2f} is moderate — manageable leverage")
    else:
        cap_factors.append(f"High debt ratio of {debt_ratio:.2f} — significant leverage reduces repayment headroom")

    cap_factors.append(f"Capacity utilization at {cap_str} — {'strong' if capacity_util >= 0.75 else 'moderate'} operational output")

    if cap_score >= 70:
        cap_explanation = "Strong repayment capacity driven by healthy margins, manageable debt levels, and efficient operations. The company generates sufficient cash flow to service debt obligations comfortably."
    elif cap_score >= 40:
        cap_explanation = "Moderate repayment capacity. While operational, the margins or debt levels suggest the company may face strain under additional debt. Careful structuring of loan terms is advised."
    else:
        cap_explanation = "Limited repayment capacity. High leverage, low margins, or underutilized capacity indicate the company may struggle to meet additional debt obligations."

    # ── 3. CAPITAL (net worth, reserves, equity strength) ──
    total_assets = financial_data.get("total_assets", 0)
    total_liabilities = financial_data.get("total_liabilities", 0)
    net_worth = total_assets - total_liabilities if total_assets else turnover * 0.3

    capital_score = min(100, max(0,
        min(40, (1 - debt_ratio) * 50) +
        min(30, profit_margin * 200) +
        min(30, (net_worth / max(turnover, 1)) * 100)
    ))

    capital_factors = []
    if net_worth > 0:
        capital_factors.append(f"Estimated net worth: ₹{net_worth:,.0f}")
    capital_factors.append(f"Equity cushion reflected in debt ratio of {debt_ratio:.2f}")
    if profit_margin > 0.12:
        capital_factors.append("Retained earnings likely growing — positive capital trajectory")
    else:
        capital_factors.append("Limited retained earnings capacity — capital growth may be slow")

    if capital_score >= 70:
        capital_explanation = "The company has a strong capital base with adequate equity reserves. This provides a safety buffer for lenders and indicates the company has significant skin-in-the-game."
    elif capital_score >= 40:
        capital_explanation = "Moderate capital position. The company has invested equity but may benefit from additional capital infusion to strengthen its balance sheet before taking on more debt."
    else:
        capital_explanation = "Weak capital base. The company has limited equity reserves, meaning lenders bear disproportionate risk. Additional equity investment is recommended."

    # ── 4. COLLATERAL (assets, satellite activity, tangible backing) ──
    ndvi = intelligence.get("ndvi_activity", 0.5)
    activity_level = intelligence.get("activity_level", "Moderate")

    collateral_score = min(100, max(0,
        min(40, ndvi * 50) +
        min(30, (total_assets / max(turnover, 1)) * 60) +
        min(30, capacity_util * 35)
    ))

    collateral_factors = []
    collateral_factors.append(f"Satellite NDVI activity: {ndvi} ({activity_level})")
    if total_assets > 0:
        collateral_factors.append(f"Total reported assets: ₹{total_assets:,.0f}")
    collateral_factors.append(f"Physical operational activity level: {activity_level}")
    if collateral_score >= 60:
        collateral_factors.append("Adequate tangible assets to serve as collateral")
    else:
        collateral_factors.append("Limited tangible asset base may require additional security")

    if collateral_score >= 70:
        collateral_explanation = "Strong collateral position supported by active operations confirmed via satellite imagery, tangible physical assets, and high capacity utilization."
    elif collateral_score >= 40:
        collateral_explanation = "Moderate collateral availability. Operations are active but asset coverage could be stronger. Partial collateral requirements may apply."
    else:
        collateral_explanation = "Limited collateral. Low asset base and reduced operational activity suggest insufficient tangible backing for the requested credit."

    # ── 5. CONDITIONS (market sentiment, industry, external environment) ──
    news_sentiment = intelligence.get("news_sentiment", 0)

    conditions_score = min(100, max(0,
        ((news_sentiment + 10) / 20) * 50 +  # sentiment normalized
        ndvi * 25 +
        min(25, mca * 2.5)
    ))

    conditions_factors = []
    if news_sentiment >= 5:
        conditions_factors.append(f"Positive news sentiment ({news_sentiment}/10) — favorable market perception")
    elif news_sentiment >= 0:
        conditions_factors.append(f"Neutral news sentiment ({news_sentiment}/10) — stable market conditions")
    else:
        conditions_factors.append(f"Negative news sentiment ({news_sentiment}/10) — adverse market environment")

    conditions_factors.append(f"Industry activity level: {activity_level}")
    conditions_factors.append(f"Regulatory environment score: {mca}/10")

    headlines = intelligence.get("headlines", [])
    if headlines:
        conditions_factors.append(f"Latest: \"{headlines[0].get('title', '')}\"")

    if conditions_score >= 70:
        conditions_explanation = "Favorable external conditions: positive market sentiment, strong industry activity, and supportive regulatory environment suggest low macro risk for lending."
    elif conditions_score >= 40:
        conditions_explanation = "Mixed external conditions. While there are positive signals, some market or regulatory factors warrant monitoring. Standard risk provisioning is recommended."
    else:
        conditions_explanation = "Challenging external conditions. Negative sentiment, weak industry signals, or regulatory concerns increase the risk of lending at this time."

    return [
        {
            "name": "Character",
            "icon": "🤝",
            "score": round(char_score),
            "color": "#6366f1",
            "explanation": char_explanation,
            "factors": char_factors,
            "description": "Measures the borrower's reputation, track record, and willingness to repay obligations.",
        },
        {
            "name": "Capacity",
            "icon": "📊",
            "score": round(cap_score),
            "color": "#22d3ee",
            "explanation": cap_explanation,
            "factors": cap_factors,
            "description": "Evaluates the borrower's ability to repay based on financial performance and cash flow.",
        },
        {
            "name": "Capital",
            "icon": "🏦",
            "score": round(capital_score),
            "color": "#10b981",
            "explanation": capital_explanation,
            "factors": capital_factors,
            "description": "Assesses the owner's investment in the business and overall equity strength.",
        },
        {
            "name": "Collateral",
            "icon": "🏗️",
            "score": round(collateral_score),
            "color": "#f59e0b",
            "explanation": collateral_explanation,
            "factors": collateral_factors,
            "description": "Reviews physical assets, operational activity, and tangible backing for the loan.",
        },
        {
            "name": "Conditions",
            "icon": "🌍",
            "score": round(conditions_score),
            "color": "#8b5cf6",
            "explanation": conditions_explanation,
            "factors": conditions_factors,
            "description": "Examines external factors like market conditions, industry trends, and economic outlook.",
        },
    ]


def _generate_risk_narrative(
    score: int, risk: str, five_cs: list, intelligence: dict
) -> str:
    """Generate a human-readable risk narrative explaining the overall assessment."""
    avg_5c = sum(c["score"] for c in five_cs) / len(five_cs)

    strengths = [c["name"] for c in five_cs if c["score"] >= 70]
    weaknesses = [c["name"] for c in five_cs if c["score"] < 40]
    moderate = [c["name"] for c in five_cs if 40 <= c["score"] < 70]

    narrative = f"The federated credit score of {score}/1000 places this company in the **{risk}** category. "

    if strengths:
        narrative += f"Key strengths were identified in {', '.join(strengths)}, which bolster the overall creditworthiness. "

    if moderate:
        narrative += f"Moderate performance was observed in {', '.join(moderate)}, suggesting room for improvement. "

    if weaknesses:
        narrative += f"Areas of concern include {', '.join(weaknesses)}, which weigh down the overall score and may require remediation. "

    narrative += f"The assessment is based on analysis across all 5Cs of credit — Character, Capacity, Capital, Collateral, and Conditions — combining financial document analysis with external intelligence signals from news, compliance records, court data, and satellite imagery."

    return narrative


def compute_federated_score(
    financial_data: Dict[str, Any],
    intelligence: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run all three bank models, compute 5Cs, and aggregate into a federated score.
    """
    b1 = bank1_financial_ratios(financial_data)
    b2 = bank2_compliance_legal(intelligence)
    b3 = bank3_market_sentiment(intelligence)

    bank_scores: List[Dict[str, Any]] = [b1, b2, b3]

    # Weighted average
    weights = [0.40, 0.30, 0.30]
    federated = round(sum(b["score"] * w for b, w in zip(bank_scores, weights)))
    federated = max(0, min(1000, federated))

    risk = _risk_category(federated)
    loan = _loan_recommendation(federated)

    # 5Cs of Credit
    five_cs = _compute_five_cs(financial_data, intelligence, bank_scores)

    # Risk breakdown percentages for chart
    total_contrib = (
        abs(intelligence.get("mca_compliance", 5))
        + abs(intelligence.get("ndvi_activity", 0.5)) * 10
        + abs(intelligence.get("news_sentiment", 0)) + 10
        + max(0, 10 - intelligence.get("court_cases", 0) * 2)
    )
    if total_contrib == 0:
        total_contrib = 1

    risk_breakdown = {
        "GST Compliance": round(abs(intelligence.get("mca_compliance", 5)) / total_contrib * 100, 1),
        "Satellite Activity": round(abs(intelligence.get("ndvi_activity", 0.5)) * 10 / total_contrib * 100, 1),
        "News Sentiment": round((abs(intelligence.get("news_sentiment", 0)) + 10) / total_contrib * 100, 1),
        "Financial Ratios": round(max(0, 10 - intelligence.get("court_cases", 0) * 2) / total_contrib * 100, 1),
    }

    # Risk narrative
    risk_narrative = _generate_risk_narrative(federated, risk, five_cs, intelligence)

    return {
        "federated_score": federated,
        "risk_category": risk,
        "loan_recommendation": loan,
        "bank_scores": bank_scores,
        "risk_breakdown": risk_breakdown,
        "five_cs": five_cs,
        "risk_narrative": risk_narrative,
        "weights": {b["bank_id"]: w for b, w in zip(bank_scores, weights)},
    }
