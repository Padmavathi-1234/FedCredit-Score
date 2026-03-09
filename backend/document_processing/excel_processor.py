"""
Excel Processor — reads XLSX files with pandas / openpyxl
and extracts financial data tables.
"""

import re
from typing import Dict, Any, List

try:
    import pandas as pd
except ImportError:
    pd = None


def _find_value(df, keywords: List[str]):
    """Search a DataFrame for a row label matching any keyword and return the value."""
    if df is None:
        return None
    for kw in keywords:
        for idx, row in df.iterrows():
            row_str = " ".join(str(v).lower() for v in row.values)
            if kw.lower() in row_str:
                # Return the last numeric-looking cell in the row
                for v in reversed(row.values):
                    try:
                        num = float(str(v).replace(",", "").replace("₹", "").strip())
                        return num
                    except (ValueError, TypeError):
                        continue
    return None


def process_excel(file_path: str) -> Dict[str, Any]:
    """Parse an Excel workbook and extract key financial metrics."""
    if pd is None:
        return {"error": "pandas is required for Excel processing"}

    try:
        xls = pd.ExcelFile(file_path)
    except Exception as e:
        return {"error": f"Cannot open Excel file: {e}"}

    all_data: Dict[str, Any] = {}
    raw_tables: list = []

    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            raw_tables.append(
                {"sheet": sheet_name, "preview": df.head(10).to_dict(orient="records")}
            )

            turnover = _find_value(df, ["turnover", "total revenue", "gross revenue", "net revenue", "total sales"])
            if turnover and "turnover" not in all_data:
                all_data["turnover"] = turnover

            debt = _find_value(df, ["debt ratio", "debt to equity", "leverage ratio", "debt-to-equity"])
            if debt and "debt_ratio" not in all_data:
                all_data["debt_ratio"] = debt if debt < 10 else debt / 100

            profit = _find_value(df, ["profit margin", "net profit margin", "npm", "net margin"])
            if profit and "profit_margin" not in all_data:
                all_data["profit_margin"] = profit / 100 if profit > 1 else profit

            cap = _find_value(df, ["capacity utilization", "utilization"])
            if cap and "capacity_utilization" not in all_data:
                all_data["capacity_utilization"] = f"{cap}%"

            total_assets = _find_value(df, ["total assets"])
            if total_assets:
                all_data["total_assets"] = total_assets

            total_liabilities = _find_value(df, ["total liabilities"])
            if total_liabilities:
                all_data["total_liabilities"] = total_liabilities

        except Exception:
            continue

    # Extract GSTIN, company name, address from all cell content
    gstin_pattern = re.compile(r'\b(\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z])\b')
    company_keywords = ["company name", "firm name", "business name", "entity name"]
    address_keywords = ["address", "registered office", "business location", "location"]

    for sheet_name in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            for idx, row in df.iterrows():
                row_str = " ".join(str(v) for v in row.values)

                if "gstin_extracted" not in all_data:
                    m = gstin_pattern.search(row_str)
                    if m:
                        all_data["gstin_extracted"] = m.group(1)

                if "company_name_extracted" not in all_data:
                    row_lower = row_str.lower()
                    for kw in company_keywords:
                        if kw in row_lower:
                            for v in row.values:
                                v_str = str(v).strip()
                                if v_str and v_str.lower() != kw and len(v_str) > 2:
                                    all_data["company_name_extracted"] = v_str
                                    break
                            break

                if "address_extracted" not in all_data:
                    row_lower = row_str.lower()
                    for kw in address_keywords:
                        if kw in row_lower:
                            for v in row.values:
                                v_str = str(v).strip()
                                if v_str and v_str.lower() != kw and len(v_str) > 5:
                                    all_data["address_extracted"] = v_str
                                    break
                            break
        except Exception:
            continue

    all_data["tables"] = raw_tables[:5]
    all_data["source"] = "excel"
    return all_data
