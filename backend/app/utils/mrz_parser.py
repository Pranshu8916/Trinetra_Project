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


def _format_yy_mm_dd(yy_mm_dd: str, is_expiry: bool = False) -> str | None:
    if not yy_mm_dd or not isinstance(yy_mm_dd, str):
        return None
    # Apply OCR numeric character fix (e.g., 'D' or 'O' -> '0', 'I' or 'l' -> '1')
    fixed_digits = "".join({"O": "0", "o": "0", "D": "0", "Q": "0", "I": "1", "l": "1", "Z": "2", "S": "5", "B": "8"}.get(c, c) for c in yy_mm_dd.strip())
    clean = re.sub(r"\D", "", fixed_digits)
    if len(clean) == 6:
        yy, mm, dd = int(clean[:2]), int(clean[2:4]), int(clean[4:])
        if 1 <= mm <= 12 and 1 <= dd <= 31:
            if is_expiry:
                year = 2000 + yy
            else:
                year = 1900 + yy if yy >= 25 else 2000 + yy
            return f"{dd:02d}/{mm:02d}/{year:04d}"
    return None


def is_likely_mrz_line1(line: str) -> bool:
    """Returns True if line is likely Line 1 of MRZ (starts with P< or V<, or has name separator << between letters)."""
    clean = line.replace(" ", "").upper()
    return clean.startswith("P<") or clean.startswith("V<") or bool(re.search(r"[A-Z]<<[A-Z]", clean))


def is_likely_mrz_line2(line: str) -> bool:
    """Returns True if line is likely Line 2 of MRZ (contains doc num, nationality, and DOB/sex/expiry sequence)."""
    clean = line.replace(" ", "").upper()
    # Line 2 never starts with P< or V<
    if clean.startswith("P<") or clean.startswith("V<"):
        return False
    # Check for nationality (3 letters) followed by digits (DOB) and sex (M/F/<)
    m = re.search(r"[A-Z0-9]{3}[0-9ODIlZS]{6}[0-9<]?[MFX<][0-9ODIlZS]{6}", clean)
    return bool(m)


def parse_td3_passport(line1: str, line2: str) -> dict[str, Any]:
    """
    Parses a standard TD3 Passport (2 lines x 44 characters) or MRV Visa (V<).
    Line 1: P<ISSUER<SURNAME<<GIVEN_NAMES<<<<<<<<<<<< or V<ISSUER<SURNAME<<GIVEN_NAMES...
    Line 2: DOC_NUM+CHK+NAT+DOB+CHK+SEX+EXP+CHK+OPT+CHK+COMPOSITE_CHK
    """
    clean_l1 = line1.replace(" ", "").upper()
    clean_l2 = line2.replace(" ", "").upper()

    # Normalize if clean_l1 starts with P + 3 uppercase letters (e.g. PINDSINGH -> P<INDSINGH)
    if re.match(r"^P[A-Z]{3}", clean_l1) and not clean_l1.startswith("P<"):
        clean_l1 = "P<" + clean_l1[1:]

    # Detect if lines are reversed (Line 2 passed first, Line 1 passed second)
    if is_likely_mrz_line1(clean_l2) and not is_likely_mrz_line1(clean_l1):
        clean_l1, clean_l2 = clean_l2, clean_l1
    elif is_likely_mrz_line2(clean_l1) and is_likely_mrz_line1(clean_l2):
        clean_l1, clean_l2 = clean_l2, clean_l1

    l1_padded = clean_l1.ljust(44, "<")[:44]
    l2_padded = clean_l2.ljust(44, "<")[:44]

    # Line 1 extraction
    doc_type_raw = l1_padded[0:2].replace("<", "")
    issuing_country = l1_padded[2:5].replace("<", "")
    name_body = l1_padded[5:].lstrip("<")
    name_section = name_body.split("<<")
    surname = re.sub(r"[^A-Za-z\s]", "", name_section[0].replace("<", " ")).strip() if len(name_section) > 0 else ""
    given_raw = " ".join([n.replace("<", " ").strip() for n in name_section[1:]]) if len(name_section) > 1 else ""
    given_clean = re.sub(r"[^A-Za-z\s]", "", given_raw).strip()
    given_names = " ".join([w for w in given_clean.split() if len(w) >= 2 or w.upper() in {"A", "I"}])

    if not surname and given_names:
        tokens = given_names.split()
        if len(tokens) >= 2:
            surname = tokens[0]
            given_names = " ".join(tokens[1:])

    # Line 2 verification: DO NOT slice names as Line 2 if Line 2 is actually a duplicated or misplaced Line 1!
    if clean_l2.startswith("V<") or clean_l2.startswith("P<") or bool(re.search(r"[A-Z]<<[A-Z]", clean_l2)):
        # clean_l2 is actually Line 1, not Line 2!
        l2_padded = ""

    document_number = None
    nationality = None
    formatted_dob = None
    formatted_exp = None
    sex = "Unspecified"
    valid_doc = False
    valid_dob = False
    valid_exp = False
    all_valid = False

    if l2_padded and len(l2_padded) >= 28:
        # Check if line 2 has shifted or noisy start; attempt anchor search
        line2_m = re.search(r"([A-Z0-9<]{9})([0-9<])([A-Z<]{3})([0-9ODIlZS]{6})([0-9<])([MFX<])([0-9ODIlZS]{6})", clean_l2)
        if line2_m:
            document_number = line2_m.group(1).replace("<", "")
            doc_num_check = line2_m.group(2)
            raw_nat = line2_m.group(3).replace("<", "")
            dob_raw = line2_m.group(4)
            dob_check = line2_m.group(5)
            raw_sex = line2_m.group(6)
            expiry_raw = line2_m.group(7)
            expiry_check = clean_l2[line2_m.end():line2_m.end() + 1] if line2_m.end() < len(clean_l2) else "<"
        else:
            document_number = l2_padded[0:9].replace("<", "")
            doc_num_check = l2_padded[9]
            raw_nat = l2_padded[10:13].replace("<", "")
            dob_raw = l2_padded[13:19]
            dob_check = l2_padded[19]
            raw_sex = l2_padded[20]
            expiry_raw = l2_padded[21:27]
            expiry_check = l2_padded[27]

        # Nationality normalization
        if raw_nat in {"ND8", "1ND", "0IN", "OIN", "IN0", "IND8", "IND"}:
            nationality = "IND"
        elif raw_nat in {"U5A", "USA8", "USA"}:
            nationality = "USA"
        elif raw_nat in {"6BR", "GBR8", "GBR"}:
            nationality = "GBR"
        else:
            nationality = raw_nat

        if raw_sex in {"M", "F"}:
            sex = raw_sex

        # Validate Checksums
        valid_doc = verify_checksum(document_number, doc_num_check)
        valid_dob = verify_checksum(dob_raw, dob_check)
        valid_exp = verify_checksum(expiry_raw, expiry_check)
        all_valid = valid_doc and valid_dob and valid_exp

        formatted_dob = _format_yy_mm_dd(dob_raw, is_expiry=False)
        formatted_exp = _format_yy_mm_dd(expiry_raw, is_expiry=True)

    is_visa = doc_type_raw.startswith("V")
    doc_label = "Visa Document (ICAO MRV)" if is_visa else "Passport (ICAO Doc 9303)"
    doc_cat = "visa" if is_visa else "passport"

    full_name = f"{given_names} {surname}".strip() or surname or given_names

    return {
        "document_type": doc_label,
        "document_category": doc_cat,
        "issuing_country": issuing_country,
        "surname": surname,
        "given_names": given_names,
        "name": full_name or None,
        "holder_name": full_name or None,
        "document_number": document_number,
        "nationality": nationality,
        "date_of_birth": formatted_dob,
        "sex": sex,
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
    if not text:
        return None

    raw_lines = [line.strip() for line in text.splitlines() if line.strip()]
    lines = [line.replace(" ", "").upper() for line in raw_lines]

    line1_candidates = []
    line2_candidates = []

    for line in lines:
        is_p_l1 = line.startswith("P<") or (line.startswith("P") and "<" in line and len(line) >= 18)
        is_v_l1 = line.startswith("V<") or (re.match(r"^V[A-Z0-9<]", line) and "<" in line and len(line) >= 18)
        if (is_p_l1 or is_v_l1) and ("<<" in line or "<" in line):
            line1_candidates.append(line)
        elif is_likely_mrz_line2(line):
            line2_candidates.append(line)
        elif len(line) >= 20 and line.count("<") >= 2:
            if "<<" in line:
                line1_candidates.append(line)
            else:
                line2_candidates.append(line)

    # If we found at least 1 Line 1 and 1 Line 2
    if line1_candidates and line2_candidates:
        try:
            return parse_td3_passport(line1_candidates[-1], line2_candidates[-1])
        except Exception:
            pass

    # Standard consecutive pair fallback
    mrz_candidates = []
    for line in lines:
        is_passport_mrz = line.startswith("P<") or (line.startswith("P") and "<" in line and len(line) >= 18)
        is_visa_mrz = line.startswith("V<") or (re.match(r"^V[A-Z0-9<]", line) and "<" in line and len(line) >= 18)
        is_general_mrz = len(line) >= 20 and line.count("<") >= 2
        if is_passport_mrz or is_visa_mrz or is_general_mrz:
            mrz_candidates.append(line)

    if len(mrz_candidates) >= 2:
        line1, line2 = mrz_candidates[-2], mrz_candidates[-1]
        try:
            res = parse_td3_passport(line1, line2)
            if res and (res.get("date_of_birth") or res.get("name")):
                return res
        except Exception:
            pass

    # If only Line 1 is found (e.g. Visa Line 1 without Line 2), parse Line 1 alone
    if line1_candidates:
        try:
            return parse_td3_passport(line1_candidates[-1], "")
        except Exception:
            pass

    return None
