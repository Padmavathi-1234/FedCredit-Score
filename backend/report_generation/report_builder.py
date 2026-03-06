"""
Report Builder — generates a branded PDF credit report using ReportLab.
Now includes 5Cs of Credit Analysis section with full explanations.
"""

import io
from typing import Dict, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie


def _build_pie_chart(breakdown: Dict[str, float]) -> Drawing:
    """Create a ReportLab pie chart from risk breakdown data."""
    d = Drawing(300, 200)
    pie = Pie()
    pie.x = 50
    pie.y = 20
    pie.width = 150
    pie.height = 150
    pie.data = list(breakdown.values())
    pie.labels = list(breakdown.keys())
    pie.slices.strokeWidth = 0.5

    chart_colors = [
        colors.HexColor("#6366f1"),
        colors.HexColor("#22d3ee"),
        colors.HexColor("#f59e0b"),
        colors.HexColor("#10b981"),
    ]
    for i, c in enumerate(chart_colors[: len(breakdown)]):
        pie.slices[i].fillColor = c

    d.add(pie)
    return d


def generate_report(analysis_result: Dict[str, Any]) -> bytes:
    """Generate a PDF credit report and return the bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=30 * mm,
        bottomMargin=20 * mm,
        leftMargin=25 * mm,
        rightMargin=25 * mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=24,
        textColor=colors.HexColor("#1e1b4b"),
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#6366f1"),
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        "SectionHead",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#312e81"),
        spaceBefore=18,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "BodyText2",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
        leading=14,
    )
    explanation_style = ParagraphStyle(
        "Explanation",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#475569"),
        spaceAfter=4,
        leading=13,
        leftIndent=12,
    )
    body = styles["Normal"]

    elements = []

    # ── Header ──
    elements.append(Paragraph("FedCredit Score", title_style))
    elements.append(Paragraph("AI Financial Intelligence — Credit Report", subtitle_style))
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#6366f1"), thickness=1))
    elements.append(Spacer(1, 12))

    # ── Company Details ──
    company = analysis_result.get("company_info", {})
    elements.append(Paragraph("Company Details", heading_style))
    company_data = [
        ["GSTIN / CIN", company.get("gstin", "N/A")],
        ["Location", company.get("location", "N/A")],
        ["Operational Insights", company.get("insights", "N/A")],
    ]
    t = Table(company_data, colWidths=[150, 300])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef2ff")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1e1b4b")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c7d2fe")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 12))

    # ── Credit Score ──
    scoring = analysis_result.get("scoring", {})
    score = scoring.get("federated_score", 0)
    risk = scoring.get("risk_category", "N/A")

    elements.append(Paragraph("Credit Score", heading_style))

    risk_color = "#10b981" if risk == "Low Risk" else ("#f59e0b" if risk == "Medium Risk" else "#ef4444")
    score_html = f"""
    <para alignment="center">
    <font size="36" color="{risk_color}"><b>{score}</b></font>
    <font size="14" color="#64748b"> / 1000</font><br/>
    <font size="16" color="{risk_color}"><b>{risk}</b></font>
    </para>
    """
    elements.append(Paragraph(score_html, styles["Normal"]))
    elements.append(Spacer(1, 8))

    # Score explanation
    if score >= 700:
        score_exp = f"A score of {score}/1000 indicates strong creditworthiness with low risk. Lenders can extend credit with high confidence."
    elif score >= 400:
        score_exp = f"A score of {score}/1000 reflects moderate creditworthiness. Standard risk provisioning and monitoring is recommended."
    else:
        score_exp = f"A score of {score}/1000 signals significant credit risk. Detailed due diligence is strongly recommended."
    elements.append(Paragraph(score_exp, explanation_style))
    elements.append(Spacer(1, 12))

    # ── 5Cs of Credit Analysis ──
    five_cs = scoring.get("five_cs", [])
    if five_cs:
        elements.append(Paragraph("5Cs of Credit Analysis", heading_style))
        elements.append(Paragraph(
            "The 5Cs framework provides a comprehensive assessment of creditworthiness across "
            "five critical dimensions: Character, Capacity, Capital, Collateral, and Conditions.",
            body_style,
        ))
        elements.append(Spacer(1, 8))

        for c in five_cs:
            name = c.get("name", "")
            c_score = c.get("score", 0)
            c_color = c.get("color", "#6366f1")

            # Section header
            c_heading = ParagraphStyle(
                f"C_{name}",
                parent=styles["Heading3"],
                fontSize=12,
                textColor=colors.HexColor(c_color),
                spaceBefore=10,
                spaceAfter=4,
            )
            elements.append(Paragraph(f"{c.get('icon', '')} {name} — Score: {c_score}/100", c_heading))
            elements.append(Paragraph(c.get("description", ""), explanation_style))
            elements.append(Spacer(1, 4))

            # Explanation
            elements.append(Paragraph(c.get("explanation", ""), body_style))

            # Factors
            factors = c.get("factors", [])
            for f in factors:
                elements.append(Paragraph(f"• {f}", explanation_style))

            elements.append(Spacer(1, 6))

    # ── Risk Narrative ──
    risk_narrative = scoring.get("risk_narrative", "")
    if risk_narrative:
        elements.append(Paragraph("Risk Assessment Summary", heading_style))
        # Replace markdown bold markers
        risk_narrative = risk_narrative.replace("**", "<b>").replace("**", "</b>")
        elements.append(Paragraph(risk_narrative, body_style))
        elements.append(Spacer(1, 12))

    # ── Bank Scores ──
    bank_scores = scoring.get("bank_scores", [])
    if bank_scores:
        elements.append(Paragraph("Individual Bank Assessments", heading_style))
        bank_data = [["Bank", "Focus Area", "Score"]]
        for b in bank_scores:
            bank_data.append([b["bank_name"], b["focus"], str(b["score"])])

        bt = Table(bank_data, colWidths=[160, 160, 80])
        bt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c7d2fe")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f3ff")]),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(bt)
        elements.append(Spacer(1, 12))

    # ── Risk Breakdown Chart ──
    breakdown = scoring.get("risk_breakdown", {})
    if breakdown:
        elements.append(Paragraph("Risk Factor Breakdown", heading_style))
        elements.append(_build_pie_chart(breakdown))
        elements.append(Spacer(1, 8))

        bd_data = [["Factor", "Contribution %"]]
        for k, v in breakdown.items():
            bd_data.append([k, f"{v}%"])
        bdt = Table(bd_data, colWidths=[200, 120])
        bdt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c7d2fe")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(bdt)
        elements.append(Spacer(1, 12))

    # ── Financial Metrics ──
    fin = analysis_result.get("financial_data", {})
    if fin:
        elements.append(Paragraph("Extracted Financial Metrics", heading_style))
        fin_rows = [["Metric", "Value"]]
        for key in ["turnover", "debt_ratio", "profit_margin", "capacity_utilization", "total_assets", "total_liabilities"]:
            if key in fin:
                label = key.replace("_", " ").title()
                val = fin[key]
                if key == "turnover":
                    val = f"₹{val:,.0f}" if isinstance(val, (int, float)) else str(val)
                elif key in ("debt_ratio", "profit_margin"):
                    val = f"{val:.2f}" if isinstance(val, (int, float)) else str(val)
                else:
                    val = str(val)
                fin_rows.append([label, val])

        if len(fin_rows) > 1:
            ft = Table(fin_rows, colWidths=[200, 200])
            ft.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c7d2fe")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f3ff")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            elements.append(ft)
            elements.append(Spacer(1, 12))

    # ── Intelligence Signals ──
    intel = analysis_result.get("intelligence", {})
    if intel:
        elements.append(Paragraph("External Intelligence Signals", heading_style))
        intel_rows = [["Signal", "Value", "Interpretation"]]
        
        ns = intel.get("news_sentiment", "N/A")
        ns_interp = "Positive" if isinstance(ns, (int, float)) and ns >= 5 else ("Neutral" if isinstance(ns, (int, float)) and ns >= 0 else "Negative")
        intel_rows.append(["News Sentiment", f"{ns} / 10", ns_interp])
        
        mca = intel.get("mca_compliance", "N/A")
        mca_interp = "Strong" if isinstance(mca, (int, float)) and mca >= 7 else ("Moderate" if isinstance(mca, (int, float)) and mca >= 4 else "Weak")
        intel_rows.append(["MCA Compliance", f"{mca} / 10", mca_interp])
        
        cc = intel.get("court_cases", "N/A")
        cc_interp = "Clean record" if cc == 0 else f"{cc} case(s) — risk"
        intel_rows.append(["Court Cases", str(cc), cc_interp])
        
        ndvi = intel.get("ndvi_activity", "N/A")
        ndvi_interp = "High activity" if isinstance(ndvi, (int, float)) and ndvi >= 0.7 else ("Moderate" if isinstance(ndvi, (int, float)) and ndvi >= 0.4 else "Low activity")
        intel_rows.append(["NDVI Activity", str(ndvi), ndvi_interp])

        it = Table(intel_rows, colWidths=[130, 100, 170])
        it.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c7d2fe")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(it)
        elements.append(Spacer(1, 12))

    # ── Loan Recommendation ──
    loan = scoring.get("loan_recommendation", {})
    if loan:
        elements.append(Paragraph("Loan Recommendation", heading_style))
        loan_rows = [["Parameter", "Value"]]
        loan_rows.append(["Recommended Loan Amount", loan.get("recommended_loan", "N/A")])
        loan_rows.append(["Interest Rate", loan.get("interest_rate", "N/A")])
        loan_rows.append(["Tenure", loan.get("tenure", "N/A")])
        loan_rows.append(["Approval Likelihood", loan.get("approval_likelihood", "N/A")])

        lt = Table(loan_rows, colWidths=[200, 200])
        lt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#10b981")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#a7f3d0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(lt)
        elements.append(Spacer(1, 6))

        loan_exp = loan.get("explanation", "")
        if loan_exp:
            elements.append(Paragraph(loan_exp, explanation_style))
        elements.append(Spacer(1, 20))

    # ── Footer ──
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#6366f1"), thickness=0.5))
    elements.append(Spacer(1, 6))
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"], fontSize=8,
        textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER,
    )
    elements.append(Paragraph(
        "Generated by FedCredit Score — AI Financial Intelligence Engine  |  "
        "This report is for informational purposes only.",
        footer_style,
    ))

    doc.build(elements)
    return buf.getvalue()
