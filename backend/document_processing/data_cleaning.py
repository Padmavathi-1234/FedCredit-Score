"""
Data Cleaning Pipeline — deduplication, normalization,
format validation, and inconsistency detection for
extracted financial data before analysis.
"""

import re
from typing import Dict, Any, List, Tuple


# ── GSTIN format regex ──
GSTIN_REGEX = re.compile(r'^(\d{2})([A-Z]{5})(\d{4})([A-Z])([1-9A-Z])(Z)([0-9A-Z])$')

# Indian state code mapping (first 2 digits of GSTIN)
STATE_CODES: Dict[str, str] = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana",
    "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
    "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram",
    "16": "Tripura", "17": "Meghalaya", "18": "Assam",
    "19": "West Bengal", "20": "Jharkhand", "21": "Odisha",
    "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "25": "Daman & Diu", "26": "Dadra & Nagar Haveli",
    "27": "Maharashtra", "28": "Andhra Pradesh", "29": "Karnataka",
    "30": "Goa", "31": "Lakshadweep", "32": "Kerala",
    "33": "Tamil Nadu", "34": "Puducherry", "35": "Andaman & Nicobar",
    "36": "Telangana", "37": "Andhra Pradesh (New)", "38": "Ladakh",
}


def validate_gstin_format(gstin: str) -> Tuple[bool, str]:
    """Validate GSTIN format. Returns (is_valid, error_message)."""
    if not gstin:
        return False, "GSTIN is required but not provided."
    gstin = gstin.strip().upper()
    if len(gstin) != 15:
        return False, f"GSTIN must be 15 characters, got {len(gstin)}."
    if not GSTIN_REGEX.match(gstin):
        return False, (
            "Invalid GSTIN format. Expected: 2-digit state code + "
            "5 uppercase letters + 4 digits + 1 letter + 1 alphanumeric + Z + 1 checksum character."
        )
    state_code = gstin[:2]
    if state_code not in STATE_CODES:
        return False, f"Unknown state code '{state_code}' in GSTIN."
    return True, ""


def get_state_from_gstin(gstin: str) -> str:
    """Extract state name from GSTIN state code."""
    if len(gstin) >= 2:
        return STATE_CODES.get(gstin[:2], "Unknown")
    return "Unknown"


def _normalize_number(value) -> float | None:
    """Attempt to normalize a value to a float."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace(",", "").replace("₹", "").replace("$", "").replace("%", "").strip()
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    return None


def _normalize_percentage(value) -> float | None:
    """Normalize a percentage value to 0-1 range."""
    num = _normalize_number(value)
    if num is None:
        return None
    if num > 1:
        return num / 100
    return num


def clean_financial_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and validate extracted financial data.

    Returns:
        {
            "cleaned_data": {...},
            "cleaning_report": [...],   # list of actions taken
            "warnings": [...]           # inconsistencies or concerns
        }
    """
    cleaned: Dict[str, Any] = {}
    report: List[str] = []
    warnings: List[str] = []

    # ── 1. Normalize turnover ──
    turnover = _normalize_number(raw_data.get("turnover"))
    if turnover is not None:
        if turnover < 0:
            warnings.append(f"Negative turnover ({turnover}) detected — this is unusual.")
        cleaned["turnover"] = turnover
        report.append(f"Turnover normalized to {turnover:,.2f}")
    else:
        report.append("Turnover not found in extracted data.")

    # ── 2. Normalize debt ratio ──
    debt_ratio = _normalize_number(raw_data.get("debt_ratio"))
    if debt_ratio is not None:
        if debt_ratio > 10:
            debt_ratio = debt_ratio / 100
            report.append(f"Debt ratio converted from percentage to decimal: {debt_ratio:.4f}")
        if debt_ratio < 0:
            warnings.append(f"Negative debt ratio ({debt_ratio}) — invalid value.")
        elif debt_ratio > 5:
            warnings.append(f"Extremely high debt ratio ({debt_ratio:.2f}) — verify data accuracy.")
        cleaned["debt_ratio"] = debt_ratio
        report.append(f"Debt ratio normalized to {debt_ratio:.4f}")

    # ── 3. Normalize profit margin ──
    profit_margin = _normalize_number(raw_data.get("profit_margin"))
    if profit_margin is not None:
        if profit_margin > 1:
            profit_margin = profit_margin / 100
            report.append(f"Profit margin converted from percentage to decimal: {profit_margin:.4f}")
        if profit_margin < -1:
            warnings.append(f"Profit margin of {profit_margin*100:.1f}% is extremely negative.")
        cleaned["profit_margin"] = profit_margin
        report.append(f"Profit margin normalized to {profit_margin:.4f}")

    # ── 4. Normalize capacity utilization ──
    cap_raw = raw_data.get("capacity_utilization")
    if cap_raw:
        cap_str = str(cap_raw).replace("%", "").strip()
        try:
            cap_val = float(cap_str)
            if cap_val > 100:
                warnings.append(f"Capacity utilization of {cap_val}% exceeds 100% — verify data.")
            cleaned["capacity_utilization"] = f"{cap_val}%"
            report.append(f"Capacity utilization normalized to {cap_val}%")
        except (ValueError, TypeError):
            cleaned["capacity_utilization"] = cap_raw

    # ── 5. Normalize total assets & liabilities ──
    total_assets = _normalize_number(raw_data.get("total_assets"))
    if total_assets is not None:
        cleaned["total_assets"] = total_assets
        report.append(f"Total assets: {total_assets:,.2f}")

    total_liabilities = _normalize_number(raw_data.get("total_liabilities"))
    if total_liabilities is not None:
        cleaned["total_liabilities"] = total_liabilities
        report.append(f"Total liabilities: {total_liabilities:,.2f}")

    # ── 6. Consistency checks ──
    if total_assets is not None and total_liabilities is not None:
        if total_liabilities > total_assets:
            warnings.append(
                f"Total liabilities (₹{total_liabilities:,.0f}) exceed total assets "
                f"(₹{total_assets:,.0f}) — company may have negative net worth."
            )

    if turnover is not None and turnover > 0:
        if profit_margin is not None and profit_margin < -0.5:
            warnings.append(
                "Profit margin below -50% combined with positive turnover — "
                "indicates severe losses. Verify financial data accuracy."
            )

    # ── 7. Pass through other fields ──
    passthrough_keys = [
        "audit_notes", "tables", "raw_text", "source",
        "gstin_extracted", "company_name_extracted", "address_extracted",
    ]
    for key in passthrough_keys:
        if key in raw_data:
            cleaned[key] = raw_data[key]

    return {
        "cleaned_data": cleaned,
        "cleaning_report": report,
        "warnings": warnings,
    }
