"""
Federated Scoring Engine — aggregates individual bank scores
into a single federated credit score with risk categorisation,
5Cs of Credit analysis, loan recommendation, and full explainability.
"""

from typing import Dict, Any, List
import re
import logging

logger = logging.getLogger(__name__)

from backend.scoring_engine.bank_models import (
    bank1_financial_ratios,
    bank2_compliance_legal,
    bank3_market_sentiment,
)


def _fallback_dynamic_scoring(score: int) -> Dict[str, Any]:
    """A minimal fallback if Ollama fails to generate dynamic scoring."""
    risk = "Low Risk" if score >= 700 else "Medium Risk" if score >= 400 else "High Risk"
    return {
        "risk_category": risk,
        "loan_recommendation": {
            "recommended_loan": "Fallback: ₹10 Crore",
            "interest_rate": "12.0%",
            "tenure": "3 Years",
            "approval_likelihood": "Moderate",
            "explanation": "This is a fallback recommendation because the AI engine is currently unavailable."
        },
        "five_cs": [
            {"name": "Character", "icon": "🤝", "score": score//10, "color": "#6366f1", "explanation": "Fallback analysis.", "factors": []},
            {"name": "Capacity", "icon": "📊", "score": score//10, "color": "#22d3ee", "explanation": "Fallback analysis.", "factors": []},
            {"name": "Capital", "icon": "🏦", "score": score//10, "color": "#10b981", "explanation": "Fallback analysis.", "factors": []},
            {"name": "Collateral", "icon": "🏗️", "score": score//10, "color": "#f59e0b", "explanation": "Fallback analysis.", "factors": []},
            {"name": "Conditions", "icon": "🌍", "score": score//10, "color": "#8b5cf6", "explanation": "Fallback analysis.", "factors": []},
        ]
    }


def _generate_risk_narrative(
    score: int, risk: str, five_cs: list, intelligence: dict,
    original_score: int = 0, insight_adjustment: int = 0, officer_insights: str = ""
) -> str:
    """Generate a comprehensive, multi-paragraph risk narrative explaining the overall assessment."""
    avg_5c = sum(c["score"] for c in five_cs) / len(five_cs)

    strengths = [c for c in five_cs if c["score"] >= 70]
    weaknesses = [c for c in five_cs if c["score"] < 40]
    moderate = [c for c in five_cs if 40 <= c["score"] < 70]

    # Paragraph 1: Overall Assessment
    narrative = f"OVERALL ASSESSMENT: The federated credit score of {score}/1000 places this company in the **{risk}** category. "
    if score >= 700:
        narrative += "This indicates a strong credit profile with high confidence for lending. The company demonstrates solid fundamentals across most assessment dimensions. "
    elif score >= 400:
        narrative += "This indicates a moderate credit profile with room for improvement. While the company meets basic lending criteria, certain areas require attention. "
    else:
        narrative += "This indicates significant credit risk. Multiple assessment dimensions raise concerns that must be addressed before credit approval. "

    # Paragraph 2: 5Cs Strengths and Weaknesses
    narrative += "\n\nDETAILED 5Cs ANALYSIS: "
    if strengths:
        strength_details = []
        for c in strengths:
            strength_details.append(f"{c['name']} ({c['score']}/100)")
        narrative += f"Key strengths were identified in {', '.join(strength_details)}, which bolster the overall creditworthiness. "
        for c in strengths:
            narrative += f"{c['name']}: {c['explanation']} "

    if moderate:
        mod_details = []
        for c in moderate:
            mod_details.append(f"{c['name']} ({c['score']}/100)")
        narrative += f"Moderate performance was observed in {', '.join(mod_details)}, suggesting room for improvement. "

    if weaknesses:
        weak_details = []
        for c in weaknesses:
            weak_details.append(f"{c['name']} ({c['score']}/100)")
        narrative += f"Areas of concern include {', '.join(weak_details)}, which weigh down the overall score and may require remediation before credit approval. "
        for c in weaknesses:
            narrative += f"{c['name']}: {c['explanation']} "

    # Paragraph 3: Officer Insight Impact
    if officer_insights and insight_adjustment != 0:
        narrative += f"\n\nOFFICER ASSESSMENT IMPACT: The credit officer provided the following assessment: \"{officer_insights.strip()}\". "
        if insight_adjustment > 0:
            narrative += f"Based on this assessment, the federated score was adjusted upward by {insight_adjustment} points (from {original_score} to {score}), reflecting the officer's positive evaluation of the company's prospects, operational strength, and management quality. "
        else:
            narrative += f"Based on this assessment, the federated score was adjusted downward by {abs(insight_adjustment)} points (from {original_score} to {score}), reflecting concerns raised by the officer regarding operational, financial, or management risks. "

    # Paragraph 4: External Intelligence Summary
    news = intelligence.get("news_sentiment", 0)
    mca = intelligence.get("mca_compliance", 5)
    court_cases = intelligence.get("court_cases", 0)
    ndvi = intelligence.get("ndvi_activity", 0.5)

    narrative += f"\n\nEXTERNAL INTELLIGENCE SUMMARY: "
    narrative += f"News sentiment scored {news}/10 ({'positive — favorable market perception' if news >= 5 else 'neutral' if news >= 0 else 'negative — adverse market signals'}). "
    narrative += f"MCA compliance is at {mca}/10 ({'strong regulatory standing' if mca >= 7 else 'moderate compliance' if mca >= 4 else 'weak compliance record'}). "
    if court_cases == 0:
        narrative += "No pending court cases were found, indicating a clean legal record. "
    else:
        narrative += f"{court_cases} court case(s) detected, adding legal risk to the profile. "
    narrative += f"Satellite NDVI activity is at {ndvi} ({'high operational activity confirmed' if ndvi >= 0.7 else 'moderate activity levels' if ndvi >= 0.4 else 'low operational activity — potential concern'}). "

    # Paragraph 5: Recommendations
    narrative += f"\n\nRECOMMENDATIONS: "
    if score >= 700:
        narrative += "The company qualifies for credit with competitive terms. Standard monitoring is recommended. It is advisable to conduct periodic reviews to ensure continued financial health."
    elif score >= 500:
        narrative += "Credit may be extended with moderate risk provisioning. Close monitoring of weak dimensions is recommended, along with structured repayment milestones. A follow-up review in 6 months is advised."
    elif score >= 400:
        narrative += "Credit should be extended cautiously with higher risk provisioning, shorter tenure, and strict collateral requirements. Quarterly performance monitoring is essential."
    else:
        narrative += "Credit extension is not recommended at this time. The company should address identified weaknesses — particularly in financial health, compliance, and operational concerns — before reapplying. A reassessment after 6-12 months of demonstrated improvement is suggested."

    return narrative


def _compute_insight_adjustment(insights: str) -> int:
    """Parse officer insights text for sentiment keywords and return a score adjustment (-50 to +50)."""
    if not insights or not insights.strip():
        return 0

    text = insights.lower()
    adjustment = 0

    # Positive keywords → increase score
    positive_keywords = {
        "expanding": 8, "growth": 8, "profitable": 10, "strong": 7,
        "excellent": 10, "stable": 5, "improving": 7, "competent": 6,
        "reliable": 6, "efficient": 6, "innovative": 5, "diversified": 5,
        "well-managed": 8, "consistent": 5, "healthy": 7, "robust": 8,
        "positive": 6, "optimistic": 5, "surplus": 7, "growing": 7,
        "reputable": 6, "trusted": 6, "compliant": 5, "timely": 4,
        "transparent": 5, "high capacity": 7, "good management": 8,
        "market leader": 9, "low risk": 8, "good track record": 8,
    }

    # Negative keywords → decrease score
    negative_keywords = {
        "declining": -8, "losses": -10, "loss": -8, "downsizing": -8,
        "struggling": -10, "weak": -7, "poor": -8, "default": -10,
        "inconsistent": -6, "risky": -7, "unstable": -8, "debt-heavy": -9,
        "non-compliant": -8, "delayed": -5, "lagging": -6, "concern": -5,
        "negative": -6, "closure": -10, "fraud": -10, "dispute": -7,
        "delinquent": -9, "overdue": -7, "shrinking": -7, "insolvent": -10,
        "high risk": -8, "poor management": -8, "cash crunch": -9,
        "court cases": -7, "irregular": -6, "red flag": -9,
    }

    for keyword, value in positive_keywords.items():
        if keyword in text:
            adjustment += value

    for keyword, value in negative_keywords.items():
        if keyword in text:
            adjustment += value  # value is already negative

    # Clamp to -50 to +50
    return max(-50, min(50, adjustment))


def _generate_bank_summary(
    bank_scores: List[Dict[str, Any]], federated_score: int
) -> str:
    """Generate a cohesive narrative summarizing all bank assessments."""
    summaries = []
    for b in bank_scores:
        name = b["bank_name"]
        score = b["score"]
        focus = b["focus"]
        if score >= 700:
            assessment = "gave a strong positive assessment"
        elif score >= 500:
            assessment = "provided a moderately favorable evaluation"
        elif score >= 400:
            assessment = "indicated moderate risk with some concerns"
        else:
            assessment = "flagged significant risk factors"
        summaries.append(f"{name} (specializing in {focus}) scored the company at {score}/1000 and {assessment}.")

    combined = " ".join(summaries)

    # Overall interpretation
    avg_score = sum(b["score"] for b in bank_scores) / len(bank_scores)
    if avg_score >= 700:
        verdict = f"All three banks converge on a positive outlook, resulting in a federated consensus score of {federated_score}/1000. The company is well-positioned for credit approval across multiple lending perspectives."
    elif avg_score >= 500:
        high_bank = max(bank_scores, key=lambda x: x["score"])
        low_bank = min(bank_scores, key=lambda x: x["score"])
        verdict = f"The banks show mixed assessments — the strongest rating came from {high_bank['bank_name']} ({high_bank['score']}/1000) while {low_bank['bank_name']} gave the most conservative score ({low_bank['score']}/1000). The weighted federated consensus settles at {federated_score}/1000, reflecting a balanced view across all assessment angles."
    elif avg_score >= 400:
        low_bank = min(bank_scores, key=lambda x: x["score"])
        verdict = f"The consensus across banks trends toward caution. {low_bank['bank_name']}'s assessment of {low_bank['score']}/1000 is particularly conservative. The federated score of {federated_score}/1000 reflects the need for careful risk management."
    else:
        verdict = f"All three banks indicate significant risk in their respective focus areas. The low federated consensus of {federated_score}/1000 suggests the company does not currently meet lending criteria from multiple perspectives."

    return f"{combined} {verdict}"


# ═══════════════════════════════════════════════════════════════
# Credit Intelligence Engine — Enhanced Analysis Functions
# ═══════════════════════════════════════════════════════════════

def _compute_financial_ratios(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute enhanced financial ratios with formulas and industry benchmarks.
    Returns EBITDA, Net Worth, DSCR, Debt/EBITDA, Net Profit Margin, Debt/Equity.
    """
    turnover = financial_data.get("turnover", 0)
    profit_margin = financial_data.get("profit_margin", 0.10)
    debt_ratio = financial_data.get("debt_ratio", 0.5)
    total_assets = financial_data.get("total_assets", 0)
    total_liabilities = financial_data.get("total_liabilities", 0)

    # Estimate EBITDA from available data (Net Profit + ~30% for interest/depreciation/tax)
    net_profit = turnover * profit_margin
    ebitda = financial_data.get("ebitda", net_profit * 1.7)  # rough estimate if not extracted
    interest_expense = financial_data.get("interest_expense", ebitda * 0.095)

    # Net Worth
    net_worth = (total_assets - total_liabilities) if total_assets else turnover * 0.3

    # Total Debt
    total_debt = total_liabilities if total_liabilities else turnover * debt_ratio

    # Equity
    equity = net_worth if net_worth > 0 else turnover * 0.2

    # Ratios
    debt_ebitda = round(total_debt / ebitda, 2) if ebitda > 0 else None
    dscr = round(ebitda / (interest_expense + (total_debt * 0.1))) if (interest_expense + total_debt * 0.1) > 0 else None
    net_profit_margin = round(profit_margin * 100, 1)
    debt_equity = round(total_debt / equity, 2) if equity > 0 else None

    # Industry benchmarks
    benchmarks = {
        "debt_ebitda": {"industry_avg": 3.5, "good_below": 3.0},
        "dscr": {"industry_avg": 1.2, "good_above": 1.5},
        "net_profit_margin": {"industry_avg": 12.0, "good_above": 15.0},
        "debt_equity": {"industry_avg": 1.5, "good_below": 1.0},
    }

    ratios = {
        "turnover": {"value": turnover, "formatted": f"₹{turnover / 10000000:.1f}Cr" if turnover >= 10000000 else f"₹{turnover:,.0f}"},
        "ebitda": {"value": ebitda, "formatted": f"₹{ebitda / 10000000:.1f}Cr" if ebitda >= 10000000 else f"₹{ebitda:,.0f}"},
        "net_profit": {"value": net_profit, "formatted": f"₹{net_profit / 10000000:.1f}Cr" if net_profit >= 10000000 else f"₹{net_profit:,.0f}"},
        "total_debt": {"value": total_debt, "formatted": f"₹{total_debt / 10000000:.1f}Cr" if total_debt >= 10000000 else f"₹{total_debt:,.0f}"},
        "net_worth": {"value": net_worth, "formatted": f"₹{net_worth / 10000000:.1f}Cr" if net_worth >= 10000000 else f"₹{net_worth:,.0f}"},
        "interest_expense": {"value": interest_expense, "formatted": f"₹{interest_expense / 10000000:.1f}Cr" if interest_expense >= 10000000 else f"₹{interest_expense:,.0f}"},
        "debt_ebitda": {
            "value": debt_ebitda,
            "formula": f"Total Debt / EBITDA = ₹{total_debt/10000000:.1f}Cr / ₹{ebitda/10000000:.1f}Cr = {debt_ebitda}x" if debt_ebitda else "N/A",
            "industry_avg": "3.5x",
            "assessment": "Better than industry" if debt_ebitda and debt_ebitda < 3.5 else "Above industry average" if debt_ebitda else "N/A",
        },
        "dscr": {
            "value": dscr,
            "formula": f"EBITDA / (Interest + Debt Service) = {dscr:.2f}x" if dscr else "N/A",
            "industry_avg": "1.2x",
            "assessment": "Strong debt service capacity" if dscr and dscr > 1.5 else "Adequate" if dscr and dscr > 1.0 else "Weak" if dscr else "N/A",
        },
        "net_profit_margin": {
            "value": net_profit_margin,
            "formula": f"Net Profit / Turnover = {net_profit_margin}%",
            "industry_avg": "12%",
            "assessment": "Above industry average" if net_profit_margin > 12 else "Below industry average",
        },
        "debt_equity": {
            "value": debt_equity,
            "formula": f"Total Debt / Equity = {debt_equity}x" if debt_equity else "N/A",
            "industry_avg": "1.5x",
            "assessment": "Conservative leverage" if debt_equity and debt_equity < 1.0 else "Moderate" if debt_equity and debt_equity < 1.5 else "High leverage" if debt_equity else "N/A",
        },
    }

    return ratios


def _compute_credit_score_model(
    financial_ratios: Dict[str, Any],
    five_cs: List[Dict[str, Any]],
    intelligence: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Credit score model: Base 650 + transparent risk adjustments, capped at 850.
    """
    base_score = 650
    adjustments = []

    # 1. GST / Turnover growth adjustment
    turnover = financial_ratios.get("turnover", {}).get("value", 0)
    if turnover > 40_000_000:
        adj = min(85, int((turnover / 50_000_000) * 40))
        adjustments.append({"factor": "Strong Turnover", "adjustment": f"+{adj}", "value": adj})
    elif turnover > 10_000_000:
        adj = 30
        adjustments.append({"factor": "Moderate Turnover", "adjustment": f"+{adj}", "value": adj})
    else:
        adj = -20
        adjustments.append({"factor": "Low Turnover", "adjustment": str(adj), "value": adj})

    # 2. Debt/EBITDA vs industry
    debt_ebitda = financial_ratios.get("debt_ebitda", {}).get("value")
    if debt_ebitda is not None:
        if debt_ebitda < 3.5:
            adj = 25
            adjustments.append({"factor": "Debt/EBITDA < Industry 3.5x", "adjustment": f"+{adj}", "value": adj})
        else:
            adj = -15
            adjustments.append({"factor": "Debt/EBITDA > Industry 3.5x", "adjustment": str(adj), "value": adj})

    # 3. DSCR threshold
    dscr = financial_ratios.get("dscr", {}).get("value")
    if dscr is not None:
        if dscr > 1.5:
            adj = 20
            adjustments.append({"factor": "DSCR > 1.5x", "adjustment": f"+{adj}", "value": adj})
        elif dscr > 1.0:
            adj = 10
            adjustments.append({"factor": "DSCR > 1.0x", "adjustment": f"+{adj}", "value": adj})
        else:
            adj = -25
            adjustments.append({"factor": "DSCR < 1.0x", "adjustment": str(adj), "value": adj})

    # 4. 5Cs average
    avg_5c = sum(c["score"] for c in five_cs) / len(five_cs) if five_cs else 50
    if avg_5c >= 80:
        adj = 45
        adjustments.append({"factor": "5Cs Average ≥ 80", "adjustment": f"+{adj}", "value": adj})
    elif avg_5c >= 60:
        adj = 25
        adjustments.append({"factor": "5Cs Average ≥ 60", "adjustment": f"+{adj}", "value": adj})
    else:
        adj = -15
        adjustments.append({"factor": "5Cs Average < 60", "adjustment": str(adj), "value": adj})

    # 5. Litigation
    court_cases = intelligence.get("court_cases", 0)
    if court_cases == 0:
        adj = 35
        adjustments.append({"factor": "No Litigation", "adjustment": f"+{adj}", "value": adj})
    else:
        adj = -20 * min(court_cases, 3)
        adjustments.append({"factor": f"{court_cases} Court Case(s)", "adjustment": str(adj), "value": adj})

    # 6. Sector / Market conditions
    news_sentiment = intelligence.get("news_sentiment", 0)
    if news_sentiment >= 5:
        adj = 32
        adjustments.append({"factor": "Positive Sector Outlook", "adjustment": f"+{adj}", "value": adj})
    elif news_sentiment >= 0:
        adj = 15
        adjustments.append({"factor": "Neutral Sector Outlook", "adjustment": f"+{adj}", "value": adj})
    else:
        adj = -20
        adjustments.append({"factor": "Negative Sector Outlook", "adjustment": str(adj), "value": adj})

    # 7. MCA Compliance
    mca = intelligence.get("mca_compliance", 5)
    if mca >= 8:
        adj = 20
        adjustments.append({"factor": "Strong MCA Compliance", "adjustment": f"+{adj}", "value": adj})
    elif mca >= 5:
        adj = 10
        adjustments.append({"factor": "Moderate MCA Compliance", "adjustment": f"+{adj}", "value": adj})
    else:
        adj = -15
        adjustments.append({"factor": "Weak MCA Compliance", "adjustment": str(adj), "value": adj})

    total_adj = sum(a["value"] for a in adjustments)
    raw_score = base_score + total_adj
    final_score = max(300, min(850, raw_score))

    formula_parts = [f"Base: {base_score}"]
    for a in adjustments:
        formula_parts.append(f"{a['factor']}: {a['adjustment']}")
    formula_parts.append(f"Raw Total: {raw_score}")
    if raw_score != final_score:
        formula_parts.append(f"Capped to: {final_score}")

    return {
        "base_score": base_score,
        "adjustments": adjustments,
        "total_adjustment": total_adj,
        "raw_score": raw_score,
        "final_score": final_score,
        "formula_breakdown": formula_parts,
    }


def _compute_detailed_risk_assessment(
    financial_data: Dict[str, Any],
    financial_ratios: Dict[str, Any],
    intelligence: Dict[str, Any],
    five_cs: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Evaluate 7 risk categories with severity and mitigation.
    """
    risks = []
    profit_margin = financial_data.get("profit_margin", 0.10)
    debt_ratio = financial_data.get("debt_ratio", 0.5)
    turnover = financial_data.get("turnover", 0)

    # 1. Financial Risk
    if profit_margin < 0.08:
        severity = "High"
        desc = f"Net profit margin of {profit_margin*100:.1f}% is below the 8% minimum threshold, indicating weak earnings."
        mitigation = "Recommend cost reduction strategies and revenue diversification."
    elif profit_margin < 0.15:
        severity = "Medium"
        desc = f"Net profit margin of {profit_margin*100:.1f}% is adequate but below the 15% benchmark."
        mitigation = "Monitor margins quarterly, encourage operational efficiency improvements."
    else:
        severity = "Low"
        desc = f"Net profit margin of {profit_margin*100:.1f}% is healthy and above industry benchmarks."
        mitigation = "Continue current strategies. Standard monitoring."
    risks.append({"category": "Financial Risk", "description": desc, "severity": severity, "mitigation": mitigation, "evidence": "Financial statements analysis"})

    # 2. Liquidity Risk
    dscr = financial_ratios.get("dscr", {}).get("value")
    if dscr and dscr < 1.0:
        severity = "High"
        desc = f"DSCR of {dscr:.2f}x is below 1.0, indicating insufficient cash flow to service debt."
        mitigation = "Require cash flow improvement plan. Consider restructuring existing debt."
    elif dscr and dscr < 1.5:
        severity = "Medium"
        desc = f"DSCR of {dscr:.2f}x is adequate but leaves limited headroom."
        mitigation = "Maintain DSCR covenant >1.5x with quarterly monitoring."
    else:
        dscr_val = dscr if dscr else 0
        severity = "Low"
        desc = f"DSCR of {dscr_val:.2f}x indicates comfortable debt service coverage."
        mitigation = "Standard annual review."
    risks.append({"category": "Liquidity Risk", "description": desc, "severity": severity, "mitigation": mitigation, "evidence": "Cash flow analysis"})

    # 3. Leverage Risk
    debt_ebitda = financial_ratios.get("debt_ebitda", {}).get("value")
    if debt_ebitda and debt_ebitda > 4.0:
        severity = "High"
        desc = f"Debt/EBITDA of {debt_ebitda}x significantly exceeds industry average of 3.5x."
        mitigation = "Require deleveraging plan. Cap additional borrowing."
    elif debt_ebitda and debt_ebitda > 2.5:
        severity = "Medium"
        desc = f"Debt/EBITDA of {debt_ebitda}x is below industry average of 3.5x but leverage remains material."
        mitigation = "Maintain DSCR covenant >1.5x and quarterly monitoring."
    else:
        d_val = debt_ebitda if debt_ebitda else 0
        severity = "Low"
        desc = f"Debt/EBITDA of {d_val}x indicates conservative leverage well below the 3.5x benchmark."
        mitigation = "Standard monitoring. Company has headroom for additional borrowing."
    risks.append({"category": "Leverage Risk", "description": desc, "severity": severity, "mitigation": mitigation, "evidence": "Balance Sheet analysis"})

    # 4. Legal Risk
    court_cases = intelligence.get("court_cases", 0)
    legal_risk = intelligence.get("legal_risk_score", 0)
    if court_cases > 2 or legal_risk > 5:
        severity = "High"
        desc = f"{court_cases} court case(s) with legal risk score {legal_risk}. Significant litigation exposure."
        mitigation = "Require legal opinion and contingent liability assessment before credit approval."
    elif court_cases > 0:
        severity = "Medium"
        desc = f"{court_cases} court case(s) found with moderate legal risk."
        mitigation = "Monitor case outcomes. Include legal risk covenant in loan agreement."
    else:
        severity = "Low"
        desc = "No pending court cases. Clean legal record."
        mitigation = "Standard periodic legal check."
    risks.append({"category": "Legal Risk", "description": desc, "severity": severity, "mitigation": mitigation, "evidence": "Court records and legal database search"})

    # 5. Compliance Risk
    mca = intelligence.get("mca_compliance", 5)
    gst_status = intelligence.get("gst_return_status", "Unknown")
    if mca < 4 or gst_status != "Filed":
        severity = "High"
        desc = f"MCA compliance score {mca}/10 with GST status '{gst_status}'. Regulatory non-compliance flagged."
        mitigation = "Require regularization of filings before disbursement."
    elif mca < 7:
        severity = "Medium"
        desc = f"MCA compliance score {mca}/10. Some filing delays noted."
        mitigation = "Include compliance covenant. Quarterly compliance certificate requirement."
    else:
        severity = "Low"
        desc = f"MCA compliance score {mca}/10. GST returns filed. Regulatory standing is strong."
        mitigation = "Annual compliance review."
    risks.append({"category": "Compliance Risk", "description": desc, "severity": severity, "mitigation": mitigation, "evidence": "MCA records, GST portal verification"})

    # 6. Industry Risk
    news_sentiment = intelligence.get("news_sentiment", 0)
    ndvi = intelligence.get("ndvi_activity", 0.5)
    if news_sentiment < -3:
        severity = "High"
        desc = f"Negative news sentiment ({news_sentiment}/10) indicates adverse market conditions."
        mitigation = "Reduce exposure. Consider shorter loan tenure to limit cyclical risk."
    elif news_sentiment < 3:
        severity = "Medium"
        desc = f"Neutral/mixed news sentiment ({news_sentiment}/10). Industry outlook is stable."
        mitigation = "Exposure limited to standard loan tenure. Monitor quarterly."
    else:
        severity = "Low"
        desc = f"Positive news sentiment ({news_sentiment}/10). Favorable industry outlook."
        mitigation = "Standard monitoring."
    risks.append({"category": "Industry Risk", "description": desc, "severity": severity, "mitigation": mitigation, "evidence": "News sentiment analysis and industry reports"})

    # 7. Operational Risk
    cap_str = str(financial_data.get("capacity_utilization", "50%"))
    cap_val = float(cap_str.replace("%", "")) if "%" in cap_str else 50
    activity = intelligence.get("activity_level", "Moderate")
    if cap_val < 50 or activity == "Low":
        severity = "High"
        desc = f"Capacity utilization at {cap_val}% with {activity} activity level. Underutilized operations."
        mitigation = "Assess operational restructuring. Require utilization improvement plan."
    elif cap_val < 70:
        severity = "Medium"
        desc = f"Capacity utilization at {cap_val}% with {activity} activity. Room for improvement."
        mitigation = "Monitor operational KPIs monthly."
    else:
        severity = "Low"
        desc = f"Capacity utilization at {cap_val}% with {activity} activity. Strong operational output."
        mitigation = "Standard operational review."
    risks.append({"category": "Operational Risk", "description": desc, "severity": severity, "mitigation": mitigation, "evidence": "Operational data and satellite imagery analysis"})

    return risks


def _compute_gst_confidence(
    gstin: str, financial_data: Dict[str, Any], intelligence: Dict[str, Any]
) -> Dict[str, Any]:
    """
    GST verification confidence scoring.
    100% = GST verified in documents + format valid
    90-98% = Format valid + partial document evidence
    <80% = Unverified
    """
    confidence = 0
    checks = []

    # 1. Format validation (15 characters)
    if gstin and len(gstin.strip()) == 15:
        confidence += 40
        checks.append({"check": "GSTIN format validation (15 characters)", "passed": True})
    else:
        checks.append({"check": "GSTIN format validation (15 characters)", "passed": False})

    # 2. PAN embedded match (characters 3-12)
    if gstin and len(gstin) >= 12:
        pan = gstin[2:12]
        if re.match(r'^[A-Z]{5}\d{4}[A-Z]$', pan):
            confidence += 20
            checks.append({"check": f"PAN embedded match ({pan})", "passed": True})
        else:
            checks.append({"check": "PAN embedded match", "passed": False})
    else:
        checks.append({"check": "PAN embedded match", "passed": False})

    # 3. GSTIN mentioned in documents
    gstin_extracted = financial_data.get("gstin_extracted", "")
    if gstin_extracted and gstin_extracted.upper() == (gstin or "").upper():
        confidence += 25
        checks.append({"check": "GSTIN found in uploaded documents", "passed": True})
    elif gstin_extracted:
        confidence += 15
        checks.append({"check": "GSTIN partially matched in documents", "passed": True, "note": "Extracted GSTIN differs from provided"})
    else:
        checks.append({"check": "GSTIN not found in documents", "passed": False})

    # 4. Business name consistency
    company_name = financial_data.get("company_name_extracted", "")
    if company_name:
        confidence += 15
        checks.append({"check": f"Business name found: {company_name}", "passed": True})
    else:
        checks.append({"check": "Business name not extracted", "passed": False})

    confidence = min(100, confidence)

    if confidence >= 100:
        status = "Fully Verified"
        explanation = "GST verified in documents with valid format. High confidence."
    elif confidence >= 80:
        status = "Verified"
        explanation = "Format valid with partial document evidence. Good confidence."
    elif confidence >= 50:
        status = "Partially Verified"
        explanation = "Format valid but limited document corroboration."
    else:
        status = "Unverified"
        explanation = "Insufficient evidence for GST verification."

    return {
        "confidence_percent": confidence,
        "status": status,
        "explanation": explanation,
        "checks": checks,
    }


def _compute_dsr_loan_eligibility(
    financial_ratios: Dict[str, Any], credit_score: int
) -> Dict[str, Any]:
    """
    DSR-based loan eligibility: DSR must be < 40%.
    DSR = Total Debt Obligations / EBITDA
    """
    ebitda = financial_ratios.get("ebitda", {}).get("value", 0)
    total_debt = financial_ratios.get("total_debt", {}).get("value", 0)

    if ebitda <= 0:
        return {
            "eligible": False,
            "reason": "EBITDA is zero or negative. Cannot compute DSR.",
            "dsr": None,
        }

    current_dsr = round((total_debt / ebitda) * 100, 1) if ebitda > 0 else 100
    allowed_dsr = 40  # percent

    max_annual_service = ebitda * (allowed_dsr / 100)
    quarterly_emi = round(max_annual_service / 4)

    # Determine loan parameters based on credit score
    if credit_score >= 750:
        interest_rate = 9.5
        tenure_years = 5
    elif credit_score >= 650:
        interest_rate = 11.2
        tenure_years = 4
    elif credit_score >= 550:
        interest_rate = 13.0
        tenure_years = 3
    else:
        interest_rate = 15.5
        tenure_years = 2

    # Simple loan amount estimate: annual EMI capacity × tenure / (1 + total interest factor)
    total_interest_factor = 1 + (interest_rate / 100 * tenure_years / 2)
    loan_amount = round(max_annual_service * tenure_years / total_interest_factor)

    return {
        "eligible": current_dsr < allowed_dsr,
        "current_dsr": f"{current_dsr}%",
        "allowed_dsr": f"{allowed_dsr}%",
        "ebitda": financial_ratios.get("ebitda", {}).get("formatted", "N/A"),
        "max_annual_debt_service": f"₹{max_annual_service / 10000000:.1f}Cr" if max_annual_service >= 10000000 else f"₹{max_annual_service:,.0f}",
        "quarterly_emi": f"₹{quarterly_emi / 10000000:.1f}Cr" if quarterly_emi >= 10000000 else f"₹{quarterly_emi:,.0f}",
        "recommended_loan": f"₹{loan_amount / 10000000:.1f}Cr" if loan_amount >= 10000000 else f"₹{loan_amount:,.0f}",
        "interest_rate": f"{interest_rate}%",
        "tenure": f"{tenure_years} Years",
        "formula": f"DSR = Total Debt / EBITDA = {current_dsr}% (threshold: {allowed_dsr}%)",
    }


def compute_federated_score(
    financial_data: Dict[str, Any],
    intelligence: Dict[str, Any],
    officer_insights: str = "",
    gstin: str = "",
) -> Dict[str, Any]:
    """
    Run all three bank models, compute 5Cs, apply officer insight adjustment,
    and aggregate into a federated score with before/after tracking.
    Now also computes enhanced financial ratios, credit score model,
    detailed risk assessment, GST confidence, and DSR loan eligibility.
    """
    b1 = bank1_financial_ratios(financial_data)
    b2 = bank2_compliance_legal(intelligence)
    b3 = bank3_market_sentiment(intelligence)

    bank_scores: List[Dict[str, Any]] = [b1, b2, b3]

    # Weighted average (original score)
    weights = [0.40, 0.30, 0.30]
    original_score = round(sum(b["score"] * w for b, w in zip(bank_scores, weights)))
    original_score = max(0, min(1000, original_score))

    # Compute officer insight adjustment
    insight_adjustment = _compute_insight_adjustment(officer_insights)
    federated = max(0, min(1000, original_score + insight_adjustment))

    # ══════════════════════════════════════════════════
    # AI-Driven Dynamic Scoring (Risk, Loan, 5Cs)
    # ══════════════════════════════════════════════════
    dynamic_scoring = None
    try:
        from backend.intelligence_layer.llm_service import generate_dynamic_scoring
        logger.info("Attempting dynamic LLM scoring for Risk, Loan, and 5Cs...")
        dynamic_scoring = generate_dynamic_scoring(federated, financial_data, intelligence)
    except Exception as e:
        logger.warning(f"Dynamic scoring failed: {e}")

    if not dynamic_scoring:
        logger.info("Falling back to minimal static scoring.")
        dynamic_scoring = _fallback_dynamic_scoring(federated)
        
    risk = dynamic_scoring.get("risk_category", "Unknown")
    loan = dynamic_scoring.get("loan_recommendation", {})
    five_cs = dynamic_scoring.get("five_cs", [])

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

    # Bank assessment summary
    bank_summary = _generate_bank_summary(bank_scores, federated)

    # Risk narrative — try LLM first, fall back to template
    risk_narrative = _generate_risk_narrative(
        federated, risk, five_cs, intelligence,
        original_score=original_score,
        insight_adjustment=insight_adjustment,
        officer_insights=officer_insights,
    )
    llm_risk_narrative = None
    llm_executive_summary = None
    try:
        from backend.intelligence_layer.llm_service import (
            generate_risk_narrative_llm,
            generate_executive_summary,
            is_ollama_available,
        )
        if is_ollama_available():
            logger.info("Ollama available — generating LLM-powered narratives")
            # Build a temp scoring dict for the LLM functions
            _temp_scoring = {
                "federated_score": federated,
                "original_score": original_score,
                "insight_adjustment": insight_adjustment,
                "risk_category": risk,
                "five_cs": five_cs,
                "detailed_risk_assessment": [],  # will be filled after
                "financial_ratios": {},  # will be filled after
            }
            llm_risk_narrative = generate_risk_narrative_llm(
                _temp_scoring, financial_data, intelligence, officer_insights
            )
            if llm_risk_narrative:
                risk_narrative = llm_risk_narrative
                logger.info("LLM risk narrative generated successfully")
    except Exception as e:
        logger.info(f"LLM generation skipped: {e}")

    # ═══════════════════════════════════════════════════════
    # Credit Intelligence Engine — Enhanced Analysis
    # ═══════════════════════════════════════════════════════
    financial_ratios = _compute_financial_ratios(financial_data)

    credit_score_model = _compute_credit_score_model(
        financial_ratios, five_cs, intelligence
    )

    detailed_risk_assessment = _compute_detailed_risk_assessment(
        financial_data, financial_ratios, intelligence, five_cs
    )

    gst_verification = _compute_gst_confidence(gstin, financial_data, intelligence)

    dsr_loan_eligibility = _compute_dsr_loan_eligibility(
        financial_ratios, credit_score_model["final_score"]
    )

    return {
        "federated_score": federated,
        "original_score": original_score,
        "insight_adjustment": insight_adjustment,
        "officer_insights": officer_insights,
        "risk_category": risk,
        "loan_recommendation": loan,
        "bank_scores": bank_scores,
        "bank_summary": bank_summary,
        "risk_breakdown": risk_breakdown,
        "five_cs": five_cs,
        "risk_narrative": risk_narrative,
        "weights": {b["bank_id"]: w for b, w in zip(bank_scores, weights)},
        # Credit Intelligence Engine additions
        "financial_ratios": financial_ratios,
        "credit_score_model": credit_score_model,
        "detailed_risk_assessment": detailed_risk_assessment,
        "gst_verification": gst_verification,
        "dsr_loan_eligibility": dsr_loan_eligibility,
        "llm_generated": llm_risk_narrative is not None,
    }

