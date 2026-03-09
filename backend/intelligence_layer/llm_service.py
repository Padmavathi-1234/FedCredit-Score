"""
LLM Service — Ollama-powered credit analysis narrative generation.

Uses llama3.1:8b with deterministic parameters for stable financial reasoning.
Falls back to template-based generation if Ollama is unavailable.
"""

import json
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# ── Ollama Configuration ──
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.1:8b"
OLLAMA_OPTIONS = {
    "temperature": 0.1,
    "top_p": 0.9,
    "repeat_penalty": 1.1,
    "num_predict": 4096,
}

# System prompt for deterministic credit analysis
CREDIT_ANALYST_SYSTEM_PROMPT = """You are TEAM LAKSHYA CREDIT INTELLIGENCE ENGINE.

You operate as a bank-grade AI credit analyst trained on RBI lending frameworks,
corporate financial analysis, and SME credit underwriting.

STRICT RULES:
- NEVER fabricate financial values. Use ONLY the data provided.
- If information is missing, explicitly state "DATA NOT FOUND".
- All calculations must be mathematically correct.
- Use professional banking terminology.
- Be concise and decision-focused.
- Every financial claim must include evidence from the provided data."""


def _call_ollama(prompt: str, system_prompt: str = CREDIT_ANALYST_SYSTEM_PROMPT) -> Optional[str]:
    """Call Ollama API with deterministic parameters. Returns None if unavailable."""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": OLLAMA_OPTIONS,
            },
            timeout=120,
        )
        if response.status_code == 200:
            return response.json().get("response", "").strip()
        else:
            logger.warning(f"Ollama returned status {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        logger.info("Ollama not available — using template-based generation")
        return None
    except Exception as e:
        logger.warning(f"Ollama call failed: {e}")
        return None


def is_ollama_available() -> bool:
    """Check if Ollama is running and the model is available."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(OLLAMA_MODEL in m.get("name", "") for m in models)
        return False
    except Exception:
        return False


def generate_executive_summary(
    company_name: str,
    gstin: str,
    financial_data: Dict[str, Any],
    scoring: Dict[str, Any],
    intelligence: Dict[str, Any],
) -> Optional[str]:
    """
    Generate a concise executive summary using LLM.
    A credit officer should be able to read this in under 30 seconds.
    """
    score = scoring.get("federated_score", 0)
    risk = scoring.get("risk_category", "N/A")
    loan = scoring.get("loan_recommendation", {})
    five_cs = scoring.get("five_cs", [])
    avg_5c = sum(c.get("score", 0) for c in five_cs) / max(len(five_cs), 1)

    # Financial ratios
    fr = scoring.get("financial_ratios", {})
    turnover_fmt = fr.get("turnover", {}).get("formatted", "N/A")
    dscr_val = fr.get("dscr", {}).get("value", "N/A")
    debt_ebitda_val = fr.get("debt_ebitda", {}).get("value", "N/A")

    prompt = f"""Generate a concise executive summary (3-4 sentences maximum) for a credit appraisal.
Use ONLY these facts — do NOT invent any numbers:

Company: {company_name}
GSTIN: {gstin}
Turnover: {turnover_fmt}
DSCR: {dscr_val}
Debt/EBITDA: {debt_ebitda_val}
Profit Margin: {financial_data.get('profit_margin', 'N/A')}
Federated Credit Score: {score}/1000
Risk Category: {risk}
5Cs Average: {avg_5c:.0f}/100
Court Cases: {intelligence.get('court_cases', 0)}
MCA Compliance: {intelligence.get('mca_compliance', 'N/A')}/10
Loan Recommendation: {loan.get('recommended_loan', 'N/A')} at {loan.get('interest_rate', 'N/A')} for {loan.get('tenure', 'N/A')}

Write a professional, decision-focused summary suitable for a bank credit committee."""

    return _call_ollama(prompt)


def generate_risk_narrative_llm(
    scoring: Dict[str, Any],
    financial_data: Dict[str, Any],
    intelligence: Dict[str, Any],
    officer_insights: str = "",
) -> Optional[str]:
    """
    Generate a detailed risk narrative using LLM.
    Covers overall assessment, 5Cs analysis, officer impact, and recommendations.
    """
    score = scoring.get("federated_score", 0)
    risk = scoring.get("risk_category", "N/A")
    original = scoring.get("original_score", score)
    adj = scoring.get("insight_adjustment", 0)
    five_cs = scoring.get("five_cs", [])

    five_cs_text = "\n".join(
        f"- {c['name']}: {c['score']}/100 — {c.get('explanation', '')[:100]}"
        for c in five_cs
    )

    risk_assessment = scoring.get("detailed_risk_assessment", [])
    risks_text = "\n".join(
        f"- {r['category']}: {r['severity']} — {r['description'][:80]}"
        for r in risk_assessment
    )

    prompt = f"""Generate a comprehensive credit risk narrative (4-5 paragraphs) for a bank credit analyst.
Use ONLY these facts:

Federated Score: {score}/1000 ({risk})
Original AI Score: {original}, Officer Adjustment: {adj:+d}
Officer Insights: "{officer_insights[:200]}"

5Cs Analysis:
{five_cs_text}

Risk Assessment:
{risks_text}

News Sentiment: {intelligence.get('news_sentiment', 0)}/10
MCA Compliance: {intelligence.get('mca_compliance', 5)}/10
Court Cases: {intelligence.get('court_cases', 0)}
NDVI Activity: {intelligence.get('ndvi_activity', 0.5)}

Structure as:
1. OVERALL ASSESSMENT (score interpretation)
2. 5Cs STRENGTHS AND WEAKNESSES
3. OFFICER ASSESSMENT IMPACT (if applicable)
4. EXTERNAL INTELLIGENCE SUMMARY
5. RECOMMENDATIONS

Use professional banking terminology. Be specific with numbers."""

    return _call_ollama(prompt)


def generate_cam_narrative(
    analysis_result: Dict[str, Any],
) -> Optional[Dict[str, str]]:
    """
    Generate a comprehensive, multi-section Credit Appraisal Memorandum (CAM)
    using LLM. Returns a dict with keys for each CAM section, or None on failure.
    """
    if not is_ollama_available():
        return None

    company = analysis_result.get("company_info", {})
    scoring = analysis_result.get("scoring", {})
    intelligence = analysis_result.get("intelligence", {})
    financial = analysis_result.get("financial_data", {})

    fr = scoring.get("financial_ratios", {})
    credit_model = scoring.get("credit_score_model", {})
    dsr = scoring.get("dsr_loan_eligibility", {})
    five_cs = scoring.get("five_cs", [])
    risk_assessment = scoring.get("detailed_risk_assessment", [])
    loan_rec = scoring.get("loan_recommendation", {})

    # ── Build context blocks ──
    company_profile = (
        f"Company Name: {company.get('company_name', 'N/A')}\n"
        f"GSTIN/CIN: {company.get('gstin', 'N/A')}\n"
        f"Location: {company.get('location', 'N/A')}\n"
        f"Officer Insights: {company.get('insights', 'N/A')}"
    )

    five_cs_text = "\n".join(
        f"- {c['name']}: {c['score']}/100 — {c.get('explanation', '')}"
        for c in five_cs
    )

    turnover_raw = financial.get("turnover", 0)
    financial_analysis = (
        f"Turnover: {fr.get('turnover', {}).get('formatted', turnover_raw)}\n"
        f"EBITDA: {fr.get('ebitda', {}).get('formatted', 'N/A')}\n"
        f"Net Profit: {fr.get('net_profit', {}).get('formatted', 'N/A')}\n"
        f"Net Profit Margin: {fr.get('net_profit_margin', {}).get('value', financial.get('profit_margin', 'N/A'))}\n"
        f"Debt/EBITDA: {fr.get('debt_ebitda', {}).get('value', 'N/A')}x\n"
        f"DSCR: {fr.get('dscr', {}).get('value', 'N/A')}x\n"
        f"Debt/Equity: {fr.get('debt_equity', {}).get('value', 'N/A')}\n"
        f"Total Assets: {financial.get('total_assets', 'N/A')}\n"
        f"Total Liabilities: {financial.get('total_liabilities', 'N/A')}\n"
        f"Debt Ratio: {financial.get('debt_ratio', 'N/A')}\n"
        f"Capacity Utilization: {financial.get('capacity_utilization', 'N/A')}\n"
        f"Credit Score Model (base 650): {credit_model.get('final_score', 'N/A')}/850\n"
        f"Federated Credit Score: {scoring.get('federated_score', 0)}/1000\n"
        f"Risk Category: {scoring.get('risk_category', 'N/A')}"
    )

    risk_text = "\n".join(
        f"- {r.get('category', '')}: {r.get('severity', '')} — {r.get('description', '')}"
        for r in risk_assessment
    )

    news_data = (
        f"News Sentiment: {intelligence.get('news_sentiment', 'N/A')}/10\n"
        f"Headlines: {', '.join(h.get('headline', '') for h in intelligence.get('headlines', [])[:3])}"
    )
    mca_status = (
        f"MCA Compliance: {intelligence.get('mca_compliance', 'N/A')}/10\n"
        f"GST Return Status: {intelligence.get('gst_return_status', 'N/A')}\n"
        f"Filings On Time: {intelligence.get('filings_on_time', 'N/A')}/{intelligence.get('filings_total', 'N/A')}"
    )
    legal_cases = (
        f"Court Cases: {intelligence.get('court_cases', 0)}\n"
        f"Legal Risk Score: {intelligence.get('legal_risk_score', 'N/A')}"
    )

    credit_evaluation = (
        f"5Cs Analysis:\n{five_cs_text}\n\n"
        f"DSR Eligible: {dsr.get('eligible', 'N/A')}\n"
        f"Recommended Loan (DSR): {dsr.get('recommended_loan', 'N/A')}"
    )

    loan_parameters = (
        f"Recommended Loan: {loan_rec.get('recommended_loan', 'N/A')}\n"
        f"Interest Rate: {loan_rec.get('interest_rate', 'N/A')}\n"
        f"Tenure: {loan_rec.get('tenure', 'N/A')}\n"
        f"Approval Likelihood: {loan_rec.get('approval_likelihood', 'N/A')}"
    )

    prompt = f"""You are an experienced bank credit analyst responsible for preparing Credit Appraisal Memorandums (CAM) for loan approval committees.

Analyze the provided company information and generate a professional CAM report suitable for review by a credit committee.

STRICT RULES:
- NEVER fabricate financial values. Use ONLY the data provided below.
- If information is missing, state "Data not available".
- Write in structured paragraphs and sections, not bullet-only responses.
- Use professional banking language.

INPUT DATA:

Company Information:
{company_profile}

Financial Analysis:
{financial_analysis}

Risk Assessment:
{risk_text}

External Intelligence:
News: {news_data}
MCA/Compliance: {mca_status}
Legal: {legal_cases}

Credit Evaluation:
{credit_evaluation}

Loan Parameters:
{loan_parameters}

REPORT STRUCTURE — generate each section as a CONCISE narrative (max 4-5 sentences each):

1. EXECUTIVE SUMMARY — High-level summary: borrower name, nature of business, purpose of borrowing, key financial highlights, overall creditworthiness. Allow a credit officer to quickly understand the borrower profile.

2. BORROWER PROFILE — Company background, incorporation details, business operations, management assessment, production capacity, key customers/suppliers context.

3. INDUSTRY AND MARKET ANALYSIS — Industry characteristics, market trends, demand drivers, competitive landscape, macroeconomic influences and how they affect the borrower.

4. FINANCIAL ANALYSIS — Revenue trends, profitability, operating margins, asset base, liabilities and leverage, liquidity indicators. Interpret what the numbers indicate about financial strength.

5. RISK ASSESSMENT — Analyze Financial Risk, Liquidity Risk, Leverage Risk, Operational Risk, Compliance Risk, Legal Risk, Industry Risk. For each: nature, evidence, possible impact on repayment.

6. CREDIT EVALUATION FRAMEWORK — Evaluate the borrower across Character, Capacity, Capital, Collateral, Conditions. Explain performance in each area.

7. LOAN RECOMMENDATION — Assess repayment capacity. If appropriate, recommend loan amount range, repayment tenure, interest rate range, repayment feasibility. Explain why the loan appears viable or risky.

8. FINAL CREDIT PERSPECTIVE — Overall credit profile view. State whether the borrower represents low, moderate, or elevated credit risk with justification.

OUTPUT FORMAT — Return ONLY a valid JSON object with NO markdown formatting:
{{
  "executive_summary": "<section 1 text>",
  "borrower_profile": "<section 2 text>",
  "industry_analysis": "<section 3 text>",
  "financial_analysis": "<section 4 text>",
  "risk_assessment": "<section 5 text>",
  "credit_evaluation": "<section 6 text>",
  "loan_recommendation": "<section 7 text>",
  "final_credit_perspective": "<section 8 text>"
}}"""

    try:
        # Use higher token limit for multi-page report
        cam_options = {**OLLAMA_OPTIONS, "num_predict": 2048}
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "system": CREDIT_ANALYST_SYSTEM_PROMPT,
                "stream": False,
                "options": cam_options,
            },
            timeout=120,  # 2 minute timeout
        )
        if response.status_code != 200:
            logger.warning(f"Ollama returned status {response.status_code} for CAM narrative")
            return None

        raw = response.json().get("response", "").strip()
        if not raw:
            return None

        # Clean up JSON
        import re
        if raw.startswith("```json"):
            raw = raw.strip("```json").strip("```").strip()
        elif raw.startswith("```"):
            raw = raw.strip("```").strip()

        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            raw = json_match.group(0)

        # Remove trailing commas
        raw = re.sub(r',\s*\}', '}', raw)

        parsed = json.loads(raw)
        logger.info("Successfully generated comprehensive CAM narrative via LLM")
        return parsed

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse CAM narrative JSON: {e}")
        return None
    except requests.exceptions.ConnectionError:
        logger.info("Ollama not available for CAM narrative — skipping")
        return None
    except Exception as e:
        logger.warning(f"CAM narrative generation failed: {e}")
        return None


def generate_cam_charts(
    analysis_result: Dict[str, Any],
) -> Optional[list]:
    """
    Use the LLM to generate chart data for the CAM report.
    Returns a list of chart dicts with title, type, labels, values, and insight.
    """
    if not is_ollama_available():
        return None

    scoring = analysis_result.get("scoring", {})
    financial = analysis_result.get("financial_data", {})
    fr = scoring.get("financial_ratios", {})

    data_summary = (
        f"Turnover: {fr.get('turnover', {}).get('formatted', financial.get('turnover', 'N/A'))}\n"
        f"EBITDA: {fr.get('ebitda', {}).get('formatted', 'N/A')}\n"
        f"Net Profit Margin: {fr.get('net_profit_margin', {}).get('value', 'N/A')}\n"
        f"Debt/EBITDA: {fr.get('debt_ebitda', {}).get('value', 'N/A')}\n"
        f"DSCR: {fr.get('dscr', {}).get('value', 'N/A')}\n"
        f"Federated Score: {scoring.get('federated_score', 0)}/1000\n"
        f"Risk Category: {scoring.get('risk_category', 'N/A')}\n"
        f"Total Assets: {financial.get('total_assets', 'N/A')}\n"
        f"Total Liabilities: {financial.get('total_liabilities', 'N/A')}\n"
        f"Debt Ratio: {financial.get('debt_ratio', 'N/A')}"
    )

    prompt = f"""Based on the following financial data, generate chart specifications for a credit report.
Return ONLY a valid JSON array. No markdown or conversational text.

Financial Data:
{data_summary}

Generate 2-3 charts. Each chart object must have:
- "chart_title": string
- "chart_type": "bar" | "line" | "pie"
- "data_labels": list of strings
- "data_values": list of numbers
- "insight": one-sentence explanation

Example:
[{{"chart_title":"Risk Distribution","chart_type":"pie","data_labels":["Financial","Operational","Compliance"],"data_values":[40,35,25],"insight":"Financial risk is the dominant component."}}]
"""

    try:
        response = _call_ollama(prompt)
        if not response:
            return None

        import re
        if response.startswith("```json"):
            response = response.strip("```json").strip("```").strip()
        elif response.startswith("```"):
            response = response.strip("```").strip()

        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)

        return json.loads(response)
    except Exception as e:
        logger.warning(f"CAM chart generation failed: {e}")
        return None


def extract_financial_data(raw_text: str) -> Dict[str, Any]:
    """
    Use the LLM to extract financial metrics from raw document text.
    Returns a dictionary of metrics natively extracted from the text.
    """
    if not is_ollama_available() or not raw_text.strip():
        return {}

    # Truncate text if it's too large to maintain context window performance
    # 15000 chars is roughly 3000-4000 tokens.
    if len(raw_text) > 15000:
        raw_text = raw_text[:15000] + "... [TRUNCATED]"

    prompt = f"""Extract core financial metrics from the following document text.
Return ONLY a valid JSON object. Do not include any markdown styling, code blocks, or conversational text.
If a metric is not found in the text, DO NOT include its key in the JSON object at all. Never use values like "N/A" or "DATA NOT FOUND".

Expected keys (use these exact names, only if the data is present):
- "turnover" (as a pure number, e.g., if it says 4.19 Crore, write 41900000; if 52 Cr, write 52000000)
- "debt_ratio" (as a decimal number between 0 and 10, e.g., 0.42)
- "profit_margin" (as a decimal number between -1 and 1, e.g., 0.168 for 16.8%)
- "capacity_utilization" (as a string with percentage, e.g., "70%")
- "total_assets" (as a pure number)
- "total_liabilities" (as a pure number)

Document Text:
{raw_text}
"""
    try:
        response = _call_ollama(prompt)
        if not response:
            return {}
        
        # Clean up in case the model returns markdown like ```json ... ```
        if response.startswith("```json"):
            response = response.strip("```json").strip("```").strip()
        elif response.startswith("```"):
            response = response.strip("```").strip()
            
        # Sometimes Ollama hallucinate plain text before or after JSON. Use regex to extract the JSON block.
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)

        # Remove trailing commas that break strict JSON
        response = re.sub(r',\s*\}', '}', response)
        
        # If the LLM still hallucinates "DATA NOT FOUND" without quotes, fix it
        response = re.sub(r':\s*DATA NOT FOUND\b', ': null', response, flags=re.IGNORECASE)
        response = re.sub(r':\s*N/A\b', ': null', response, flags=re.IGNORECASE)

        parsed = json.loads(response)
        
        # Strip out any keys that became null due to the fix above
        return {k: v for k, v in parsed.items() if v is not None}

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM extraction JSON: {e} | Raw Response: {response[:100]}")
        return {}
    except Exception as e:
        logger.error(f"Error during LLM extraction: {e}")
        return {}


def generate_dynamic_scoring(
    federated_score: int,
    financial_data: Dict[str, Any],
    intelligence: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Use the LLM to dynamically determine risk category, loan recommendation,
    and the 5Cs of credit based on facts rather than static rules.
    """
    if not is_ollama_available():
        return None

    # Format the input data cleanly for the prompt
    fin_summary = ", ".join(f"{k}: {v}" for k, v in financial_data.items() if v is not None)
    intel_summary = ", ".join(f"{k}: {v}" for k, v in intelligence.items() if v is not None and k != "headlines")

    # Calculate a rough mathematical maximum loan amount to prevent LLM hallucinations logically
    turnover = float(financial_data.get("turnover", 0))
    max_loan = turnover * 0.25  # Safe assumption: max loan is 25% of turnover
    
    if max_loan >= 10000000:
        max_loan_str = f"₹{max_loan / 10000000:.2f} Crore"
    elif max_loan > 0:
        max_loan_str = f"₹{max_loan / 100000:.2f} Lakhs"
    else:
        max_loan_str = "Not Recommended"

    prompt = f"""You are a senior credit analyst. Based on the following company data, generate a complete credit scoring assessment.
Return ONLY a valid JSON object. Do not include any formatting or conversational text.

CRITICAL RULES FOR SPEED AND ACCURACY:
1. LOAN AMOUNT: Do NOT blindly recommend loans in 'Crores'. The absolute maximum eligible loan for this company is {max_loan_str}. Your recommendation must be equal to or lower than this amount. Use 'Lakhs' if turnover is low.
2. CONCISENESS: Keep ALL explanations strictly under 15 words to reduce generation time.
3. FACTORS: Only provide exactly ONE factor string in the factors list per 5C category.

INPUT DATA:
- Federated Credit Score: {federated_score}/1000
- Financials: {fin_summary}
- Intelligence: {intel_summary}

REQUIRED JSON STRUCTURE:
{{
  "risk_category": "Low Risk" | "Medium Risk" | "High Risk",
  "loan_recommendation": {{
    "recommended_loan": "₹[Amount] Lakhs/Crore" | "Not Recommended",
    "interest_rate": "[Rate]%",
    "tenure": "[Years] Years",
    "approval_likelihood": "High" | "Moderate" | "Moderate-Low" | "Low",
    "explanation": "[Short explanation < 15 words]"
  }},
  "five_cs": [
    {{
      "name": "Character",
      "icon": "🤝",
      "score": [0-100],
      "color": "#6366f1",
      "explanation": "[< 15 words]",
      "factors": ["[exactly one key factor]"],
      "description": "Measures the borrower's reputation, track record, and willingness to repay obligations."
    }},
    {{
      "name": "Capacity",
      "icon": "📊",
      "score": [0-100],
      "color": "#22d3ee",
      "explanation": "[< 15 words]",
      "factors": ["[exactly one key factor]"],
      "description": "Evaluates the borrower's ability to repay based on financial performance and cash flow."
    }},
    {{
      "name": "Capital",
      "icon": "🏦",
      "score": [0-100],
      "color": "#10b981",
      "explanation": "[< 15 words]",
      "factors": ["[exactly one key factor]"],
      "description": "Assesses the owner's investment in the business and overall equity strength."
    }},
    {{
      "name": "Collateral",
      "icon": "🏗️",
      "score": [0-100],
      "color": "#f59e0b",
      "explanation": "[< 15 words]",
      "factors": ["[exactly one key factor]"],
      "description": "Reviews physical assets, operational activity, and tangible backing for the loan."
    }},
    {{
      "name": "Conditions",
      "icon": "🌍",
      "score": [0-100],
      "color": "#8b5cf6",
      "explanation": "[< 15 words]",
      "factors": ["[exactly one key factor]"],
      "description": "Examines external factors like market conditions, industry trends, and economic outlook."
    }}
  ]
}}
"""
    try:
        response = _call_ollama(prompt)
        if not response:
            return None
            
        # Clean up JSON formatting
        if response.startswith("```json"):
            response = response.strip("```json").strip("```").strip()
        elif response.startswith("```"):
            response = response.strip("```").strip()
            
        return json.loads(response)
    except Exception as e:
        logger.error(f"Failed to generate dynamic scoring from LLM: {e}")
        return None
