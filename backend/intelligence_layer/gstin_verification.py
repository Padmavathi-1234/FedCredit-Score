"""
GSTIN & Company Verification — validates GSTIN format, state code,
and cross-references with the claimed company location.
"""

import re
from typing import Dict, Any, List

# Same state code mapping as data_cleaning
from backend.document_processing.data_cleaning import (
    GSTIN_REGEX, STATE_CODES, validate_gstin_format, get_state_from_gstin,
)


# Mapping of common city/location names to their state
LOCATION_STATE_MAP: Dict[str, str] = {
    # Maharashtra
    "mumbai": "Maharashtra", "pune": "Maharashtra", "nagpur": "Maharashtra",
    "thane": "Maharashtra", "nashik": "Maharashtra", "aurangabad": "Maharashtra",
    "solapur": "Maharashtra", "kolhapur": "Maharashtra", "navi mumbai": "Maharashtra",
    # Karnataka
    "bangalore": "Karnataka", "bengaluru": "Karnataka", "mysore": "Karnataka",
    "mysuru": "Karnataka", "hubli": "Karnataka", "mangalore": "Karnataka",
    "mangaluru": "Karnataka", "belgaum": "Karnataka", "belagavi": "Karnataka",
    # Tamil Nadu
    "chennai": "Tamil Nadu", "coimbatore": "Tamil Nadu", "madurai": "Tamil Nadu",
    "salem": "Tamil Nadu", "trichy": "Tamil Nadu", "tiruchirappalli": "Tamil Nadu",
    # Delhi
    "delhi": "Delhi", "new delhi": "Delhi",
    # Uttar Pradesh
    "lucknow": "Uttar Pradesh", "noida": "Uttar Pradesh", "ghaziabad": "Uttar Pradesh",
    "kanpur": "Uttar Pradesh", "agra": "Uttar Pradesh", "varanasi": "Uttar Pradesh",
    "greater noida": "Uttar Pradesh",
    # Gujarat
    "ahmedabad": "Gujarat", "surat": "Gujarat", "vadodara": "Gujarat",
    "rajkot": "Gujarat", "gandhinagar": "Gujarat",
    # Telangana
    "hyderabad": "Telangana", "secunderabad": "Telangana", "warangal": "Telangana",
    # Kerala
    "kochi": "Kerala", "thiruvananthapuram": "Kerala", "trivandrum": "Kerala",
    "kozhikode": "Kerala", "calicut": "Kerala",
    # West Bengal
    "kolkata": "West Bengal", "howrah": "West Bengal", "durgapur": "West Bengal",
    # Rajasthan
    "jaipur": "Rajasthan", "jodhpur": "Rajasthan", "udaipur": "Rajasthan",
    # Punjab
    "chandigarh": "Chandigarh", "ludhiana": "Punjab", "amritsar": "Punjab",
    # Haryana
    "gurgaon": "Haryana", "gurugram": "Haryana", "faridabad": "Haryana",
    # Madhya Pradesh
    "bhopal": "Madhya Pradesh", "indore": "Madhya Pradesh",
    # Bihar
    "patna": "Bihar",
    # Odisha
    "bhubaneswar": "Odisha",
    # Andhra Pradesh
    "visakhapatnam": "Andhra Pradesh", "vijayawada": "Andhra Pradesh",
    "amaravati": "Andhra Pradesh", "vizag": "Andhra Pradesh",
    # Goa
    "goa": "Goa", "panaji": "Goa",
    # Jharkhand
    "ranchi": "Jharkhand", "jamshedpur": "Jharkhand",
    # Chhattisgarh
    "raipur": "Chhattisgarh",
    # Assam
    "guwahati": "Assam",
    # Uttarakhand
    "dehradun": "Uttarakhand",
    # Himachal Pradesh
    "shimla": "Himachal Pradesh",
}

# Reverse lookup: state name → set of valid GSTIN state codes
STATE_NAME_TO_CODES: Dict[str, List[str]] = {}
for code, state_name in STATE_CODES.items():
    base_name = state_name.replace(" (New)", "")
    STATE_NAME_TO_CODES.setdefault(base_name.lower(), []).append(code)
    STATE_NAME_TO_CODES.setdefault(state_name.lower(), []).append(code)


def _resolve_state_from_location(location: str) -> str | None:
    """Try to resolve a state name from a location string."""
    loc_lower = location.strip().lower()

    # Direct match against state names
    for state_name in STATE_CODES.values():
        if state_name.lower() in loc_lower:
            return state_name.replace(" (New)", "")

    # Match against city/location map
    for city, state in LOCATION_STATE_MAP.items():
        if city in loc_lower:
            return state

    return None


def verify_company(gstin: str, location: str) -> Dict[str, Any]:
    """
    Verify company authenticity:
    1. Validate GSTIN format
    2. Extract state from GSTIN
    3. Match against claimed location

    Returns:
        {
            "valid": bool,
            "errors": [...],
            "details": {
                "gstin_state_code": "29",
                "gstin_state_name": "Karnataka",
                "claimed_location": "Bangalore, Karnataka",
                "resolved_state": "Karnataka",
                "match": True/False
            }
        }
    """
    errors: List[str] = []
    details: Dict[str, Any] = {}

    # Step 1: Validate GSTIN format
    is_valid, error_msg = validate_gstin_format(gstin)
    if not is_valid:
        return {
            "valid": False,
            "errors": [error_msg],
            "details": {"gstin_provided": gstin},
        }

    gstin = gstin.strip().upper()
    state_code = gstin[:2]
    gstin_state = get_state_from_gstin(gstin)

    details["gstin_state_code"] = state_code
    details["gstin_state_name"] = gstin_state
    details["claimed_location"] = location

    # Step 2: Verify location
    if not location or not location.strip():
        return {
            "valid": False,
            "errors": ["Company location is required for verification."],
            "details": details,
        }

    resolved_state = _resolve_state_from_location(location)
    details["resolved_state"] = resolved_state

    if resolved_state is None:
        # Could not resolve state from location — warn but don't block
        details["match"] = None
        details["note"] = (
            f"Could not automatically determine the state from '{location}'. "
            f"GSTIN indicates the company is registered in {gstin_state} (code: {state_code})."
        )
        return {
            "valid": True,
            "errors": [],
            "details": details,
        }

    # Step 3: Cross-reference
    valid_codes = STATE_NAME_TO_CODES.get(resolved_state.lower(), [])
    if state_code in valid_codes:
        details["match"] = True
        return {
            "valid": True,
            "errors": [],
            "details": details,
        }
    else:
        details["match"] = False
        return {
            "valid": False,
            "errors": [
                f"GSTIN state mismatch: GSTIN '{gstin}' is registered in "
                f"{gstin_state} (code: {state_code}), but the claimed location "
                f"'{location}' resolves to {resolved_state}. "
                f"The company does not appear to be registered at the stated location."
            ],
            "details": details,
        }
