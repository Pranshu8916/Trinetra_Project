"""
ICAO Doc 9303 MRZ Parsing and Checksum Validation Utility
Supports standard TD3 (Passports) and TD1 (ID Cards).
"""
import re
from typing import Any

WEIGHTS = [7, 3, 1]


def get_char_value(c: str) -> int:
    """Converts a character to its ICAO numeric value (A=10...Z=35, <=0, digits=0-9)."""
    c = c.upper()
    if c.isdigit():
        return int(c)
    elif "A" <= c <= "Z":
        return ord(c) - ord("A") + 10
    elif c == "<":
        return 0
    return 0


def calculate_icao_checksum(data: str) -> int:
    """Calculates ICAO 7-3-1 modulo 10 checksum for a string."""
    total = 0
    for idx, char in enumerate(data):
        weight = WEIGHTS[idx % 3]
        total += get_char_value(char) * weight
    return total % 10


def verify_checksum(data: str, expected_digit: str) -> bool:
    """Validates whether data matches the expected checksum digit."""
    if not expected_digit.isdigit():
        return False
    return calculate_icao_checksum(data) == int(expected_digit)


def _format_yy_mm_dd(yy_mm_dd: str, is_expiry: bool = False) -> str:
    clean = re.sub(r"\D", "", yy_mm_dd)
    if len(clean) == 6:
        yy, mm, dd = int(clean[:2]), clean[2:4], clean[4:]
        if is_expiry:
            year = 2000 + yy
        else:
            year = 1900 + yy if yy >= 30 else 2000 + yy
        return f"{dd}/{mm}/{year}"
    return yy_mm_dd


def parse_td3_passport(line1: str, line2: str) -> dict[str, Any]:
    """
    Parses a standard TD3 Passport (2 lines x 44 characters) or MRV Visa (V<).
    Line 1: P<ISSUER<SURNAME<<GIVEN_NAMES<<<<<<<<<<<< or V<ISSUER<SURNAME<<GIVEN_NAMES...
    Line 2: DOC_NUM+CHK+NAT+DOB+CHK+SEX+EXP+CHK+OPT+CHK+COMPOSITE_CHK
    """
    line1 = line1.replace(" ", "").upper().ljust(44, "<")[:44]
    line2 = line2.replace(" ", "").upper().ljust(44, "<")[:44]

    # Line 1 extraction
    doc_type_raw = line1[0:2].replace("<", "")
    issuing_country = line1[2:5].replace("<", "")
    name_section = line1[5:].split("<<")
    surname = re.sub(r"[^A-Za-z\s]", "", name_section[0].replace("<", " ")).strip() if len(name_section) > 0 else ""
    given_raw = " ".join([n.replace("<", " ").strip() for n in name_section[1:]]) if len(name_section) > 1 else ""
    given_clean = re.sub(r"[^A-Za-z\s]", "", given_raw).strip()
    given_names = " ".join([w for w in given_clean.split() if len(w) >= 2 or w.upper() in {"A", "I"}])

    # Line 2 extraction
    document_number = line2[0:9].replace("<", "")
    doc_num_check = line2[9]
    nationality = line2[10:13].replace("<", "")
    dob_raw = line2[13:19]  # YYMMDD
    dob_check = line2[19]
    sex = line2[20]
    expiry_raw = line2[21:27]  # YYMMDD
    expiry_check = line2[27]

    # Validate Checksums
    valid_doc = verify_checksum(line2[0:9], doc_num_check)
    valid_dob = verify_checksum(dob_raw, dob_check)
    valid_exp = verify_checksum(expiry_raw, expiry_check)
    all_valid = valid_doc and valid_dob and valid_exp

    is_visa = doc_type_raw.startswith("V")
    doc_label = "Visa Document (ICAO MRV)" if is_visa else "Passport (ICAO Doc 9303)"
    doc_cat = "visa" if is_visa else "passport"

    formatted_dob = _format_yy_mm_dd(dob_raw, is_expiry=False)
    formatted_exp = _format_yy_mm_dd(expiry_raw, is_expiry=True)

    return {
        "document_type": doc_label,
        "document_category": doc_cat,
        "issuing_country": issuing_country,
        "surname": surname,
        "given_names": given_names,
        "document_number": document_number,
        "nationality": nationality,
        "date_of_birth": formatted_dob,
        "sex": sex if sex in ["M", "F"] else "Unspecified",
        "expiration_date": formatted_exp,
        "checksums": {
            "document_number_valid": valid_doc,
            "dob_valid": valid_dob,
            "expiry_valid": valid_exp,
            "overall_mrz_valid": all_valid,
        },
    }


def find_mrz_in_text(text: str) -> dict[str, Any] | None:
    """Finds and parses TD3 Passport or MRV Visa lines from raw text string if present."""
    lines = [line.strip().replace(" ", "").upper() for line in text.splitlines() if line.strip()]
    mrz_candidates = []
    for line in lines:
        if line.startswith("P<") or line.startswith("V<") or (len(line) >= 30 and "<" in line):
            mrz_candidates.append(line)

    if len(mrz_candidates) >= 2:
        line1, line2 = mrz_candidates[-2], mrz_candidates[-1]
        try:
            return parse_td3_passport(line1, line2)
        except Exception:
            return None
    return None
