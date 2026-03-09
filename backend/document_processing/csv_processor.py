"""
CSV Processor — reads CSV files with pandas and extracts financial data.
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
                for v in reversed(row.values):
                    try:
                        num = float(str(v).replace(",", "").replace("₹", "").strip())
                        return num
                    except (ValueError, TypeError):
                        continue
    return None


def _extract_metadata_from_df(df) -> Dict[str, str]:
    """Scan the DataFrame for GSTIN, company name, and address patterns."""
    metadata: Dict[str, str] = {}
    if df is None:
        return metadata

    gstin_pattern = re.compile(r'\b(\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z])\b')
    company_keywords = ["company name", "firm name", "business name", "entity name", "name of company"]
    address_keywords = ["address", "registered office", "business location", "location"]

    for idx, row in df.iterrows():
        row_str = " ".join(str(v) for v in row.values)

        # GSTIN
        if "gstin_extracted" not in metadata:
            m = gstin_pattern.search(row_str)
            if m:
                metadata["gstin_extracted"] = m.group(1)

        # Company name
        if "company_name_extracted" not in metadata:
            row_lower = row_str.lower()
            for kw in company_keywords:
                if kw in row_lower:
                    for v in row.values:
                        v_str = str(v).strip()
                        if v_str and v_str.lower() != kw and len(v_str) > 2:
                            metadata["company_name_extracted"] = v_str
                            break
                    break

        # Address
        if "address_extracted" not in metadata:
            row_lower = row_str.lower()
            for kw in address_keywords:
                if kw in row_lower:
                    for v in row.values:
                        v_str = str(v).strip()
                        if v_str and v_str.lower() != kw and len(v_str) > 5:
                            metadata["address_extracted"] = v_str
                            break
                    break

    return metadata


def process_csv(file_path: str) -> Dict[str, Any]:
    """Parse a CSV file and extract key financial metrics."""
    if pd is None:
        return {"error": "pandas is required for CSV processing"}

    try:
        df = pd.read_csv(file_path, header=None, encoding="utf-8")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_path, header=None, encoding="latin-1")
        except Exception as e:
            return {"error": f"Cannot open CSV file: {e}"}
    except Exception as e:
        return {"error": f"Cannot open CSV file: {e}"}

    all_data: Dict[str, Any] = {}

    turnover = _find_value(df, ["turnover", "total revenue", "gross revenue", "net revenue", "total sales"])
    if turnover:
        all_data["turnover"] = turnover

    debt = _find_value(df, ["debt ratio", "debt to equity", "leverage ratio", "debt-to-equity"])
    if debt:
        all_data["debt_ratio"] = debt if debt < 10 else debt / 100

    profit = _find_value(df, ["profit margin", "net profit margin", "npm", "net margin"])
    if profit:
        all_data["profit_margin"] = profit / 100 if profit > 1 else profit

    cap = _find_value(df, ["capacity utilization", "utilization"])
    if cap:
        all_data["capacity_utilization"] = f"{cap}%"

    total_assets = _find_value(df, ["total assets"])
    if total_assets:
        all_data["total_assets"] = total_assets

    total_liabilities = _find_value(df, ["total liabilities"])
    if total_liabilities:
        all_data["total_liabilities"] = total_liabilities

    # Extract metadata (GSTIN, company name, address)
    metadata = _extract_metadata_from_df(df)
    all_data.update(metadata)

    raw_tables = [{"sheet": "csv", "preview": df.head(10).to_dict(orient="records")}]
    all_data["tables"] = raw_tables[:5]
    all_data["source"] = "csv"
    return all_data
