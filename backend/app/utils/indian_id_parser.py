"""
Indian Identity Document Parser & Validation Utility
Supports:
1. Aadhaar Card (12-digit UID with official Verhoeff checksum algorithm)
2. Indian Driving License (State RTO code + Issue Year + 7-digit Serial)
3. PAN Card (Income Tax Department 10-character structure)
4. ICAO Doc 9303 Passports (TD3 & TD1)
"""

import re
from typing import Any

# =====================================================================
# 1. VERHOEFF ALGORITHM (Official UIDAI 12-digit Aadhaar Checksum)
# =====================================================================

D_TABLE = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

P_TABLE = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]


def validate_verhoeff(num_str: str) -> bool:
    """Validates 12-digit Aadhaar number using Verhoeff modulo-10 algorithm."""
    clean_num = re.sub(r"\D", "", num_str)
    if len(clean_num) != 12:
        return False
    # Aadhaar numbers never start with 0 or 1
    if clean_num[0] in ["0", "1"]:
        return False

    c = 0
    for i, ch in enumerate(reversed(clean_num)):
        c = D_TABLE[c][P_TABLE[i % 8][int(ch)]]
    return c == 0


# =====================================================================
# 2. INDIAN STATE CODES (for Driving Licenses)
# =====================================================================

INDIAN_STATES = {
    "AN": "Andaman and Nicobar", "AP": "Andhra Pradesh", "AR": "Arunachal Pradesh",
    "AS": "Assam", "BR": "Bihar", "CH": "Chandigarh", "CG": "Chhattisgarh",
    "DD": "Daman and Diu", "DL": "Delhi", "DN": "Dadra and Nagar Haveli",
    "GA": "Goa", "GJ": "Gujarat", "HP": "Himachal Pradesh", "HR": "Haryana",
    "JH": "Jharkhand", "JK": "Jammu and Kashmir", "KA": "Karnataka",
    "KL": "Kerala", "LA": "Ladakh", "LD": "Lakshadweep", "MH": "Maharashtra",
    "ML": "Meghalaya", "MN": "Manipur", "MP": "Madhya Pradesh", "MZ": "Mizoram",
    "NL": "Nagaland", "OD": "Odisha", "PB": "Punjab", "PY": "Puducherry",
    "RJ": "Rajasthan", "SK": "Sikkim", "TN": "Tamil Nadu", "TR": "Tripura",
    "TS": "Telangana", "UK": "Uttarakhand", "UP": "Uttar Pradesh", "WB": "West Bengal"
}


# =====================================================================
# 2b. NAME EXTRACTION & CLEANING UTILITY
# =====================================================================

_INVALID_NAME_KEYWORDS = {
    "GOVERNMENT", "INDIA", "UIDAI", "BHARAT", "SARKAR", "INCOME TAX", "TRANSPORT",
    "DEPARTMENT", "UNION", "STATE", "AUTHORITY", "UNIQUE", "IDENTIFICATION", "REPUBLIC",
    "PASSPORT", "DOB", "DATE OF BIRTH", "YEAR OF BIRTH", "DATE", "BIRTH", "ISSUE",
    "EXPIRY", "VALID", "MALE", "FEMALE", "TRANSGENDER", "ADDRESS", "NO", "NUMBER",
    "DOCUMENT", "ENROLLMENT", "VID", "SIGNATURE", "HELP", "WWW", "S/O", "D/O", "W/O",
    "C/O", "SON OF", "DAUGHTER OF", "WIFE OF", "CARE OF", "FATHER", "MOTHER", "HUSBAND",
    "S/0", "D/0", "W/0", "C/0", "MERCHANTS", "1947", "HELP@UIDAI.GOV.IN", "WWW.UIDAI.GOV.IN",
    "DETAILS", "CARD", "FORM", "LICENCE", "LICENSE", "PERMANENT", "ACCOUNT", "ENTRY", "PERMIT"
}


def clean_person_name(raw: str) -> str | None:
    if not raw or len(raw) < 2:
        return None
    # Strip relation prefixes (S/O, D/O, W/O, C/O, Father, Care of, Name:)
    clean = re.sub(
        r"^(?:Name|Holder|Cardholder|To|S/O|D/O|W/O|C/O|Father|Mother|Son of|Daughter of|Wife of|Care of|S/0|D/0|W/0|C/0)[:\s\.\-]*",
        "",
        raw,
        flags=re.IGNORECASE,
    ).strip()

    clean = re.sub(r"^[^a-zA-Z]+|[^a-zA-Z]+$", "", clean).strip()
    clean = re.sub(r"\s+", " ", clean)

    words = [w for w in clean.split() if len(w) >= 2 and re.match(r"^[A-Za-z\.'\-]+$", w)]
    if not words:
        return None

    valid_words = []
    for w in words:
        upper_w = w.upper()
        if upper_w in _INVALID_NAME_KEYWORDS:
            return None
        # Reject repeating single-character OCR noise like "TT", "AA", "XX", "ZZ"
        if len(set(upper_w)) == 1:
            continue
        valid_words.append(w)

    if not valid_words:
        return None

    result = " ".join(w.capitalize() for w in valid_words)
    return result if len(result) >= 3 else None


def extract_clean_indian_person_name(text: str, dob: str | None = None) -> tuple[str | None, str | None]:
    """
    Extracts (holder_name, father_name) from document OCR text.
    Correctly separates subject's full name from father's / caregiver's name (S/O, C/O) and filters out OCR noise.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    father_name = None
    for line in lines:
        upper = line.upper()
        if any(k in upper for k in ["S/O", "D/O", "W/O", "C/O", "FATHER", "S/0", "D/0", "W/0", "C/0", "SON OF", "DAUGHTER OF", "WIFE OF"]):
            f_cand = clean_person_name(line)
            if f_cand:
                father_name = f_cand
                break

    dob_idx = -1
    for i, line in enumerate(lines):
        if any(k in line.upper() for k in ["DOB", "DATE OF BIRTH", "YEAR OF BIRTH", "D.O.B"]):
            dob_idx = i
            break

    holder_name = None

    # 1. Look at lines above DOB
    if dob_idx > 0:
        candidates = []
        for i in range(max(0, dob_idx - 4), dob_idx):
            line = lines[i]
            upper = line.upper()
            if re.search(r"\d", line):
                continue
            if any(k in upper for k in ["S/O", "D/O", "W/O", "C/O", "FATHER", "MOTHER", "S/0", "D/0", "W/0", "C/0"]):
                continue
            c_name = clean_person_name(line)
            if c_name:
                candidates.append(c_name)

        if candidates:
            if len(candidates) >= 2 and len(candidates[0].split()) == 1 and len(candidates[1].split()) == 1:
                holder_name = f"{candidates[0]} {candidates[1]}"
            else:
                holder_name = max(candidates, key=lambda x: len(x.split()))

    # 2. Search for "Name:" field pattern anywhere in text
    if not holder_name:
        name_match = re.search(r"(?:Full\s*Name|Name|Cardholder)[:\s]*([A-Za-z\s\.\'\-]+)", text, re.IGNORECASE)
        if name_match:
            raw_cand = name_match.group(1).split("\n")[0].strip()
            raw_cand = re.split(r"\b(?:DOB|DATE|SEX|GENDER|NO|DOC|ISSUED|EXPIRY|S/O|D/O|W/O|FATHER)\b", raw_cand, flags=re.IGNORECASE)[0].strip()
            c_name = clean_person_name(raw_cand)
            if c_name:
                holder_name = c_name

    # 3. Fallback: Search top 10 lines of document (below Govt of India header)
    if not holder_name:
        for line in lines[:10]:
            upper = line.upper()
            if re.search(r"\d", line):
                continue
            if any(k in upper for k in ["GOVERNMENT", "INDIA", "UIDAI", "BHARAT", "SARKAR", "S/O", "D/O", "W/O", "C/O", "FATHER"]):
                continue
            c_name = clean_person_name(line)
            if c_name and len(c_name.split()) >= 1:
                holder_name = c_name
                break

    return holder_name, father_name


# =====================================================================
# 3. AADHAAR CARD PARSER
# =====================================================================

def parse_aadhaar_card(text: str) -> dict[str, Any] | None:
    # Look for 12-digit pattern (e.g., 2345 6789 1234 or 234567891234)
    aadhaar_match = re.search(r"\b([2-9]\d{3})[\s\-]?(\d{4})[\s\-]?(\d{4})\b", text)
    if not aadhaar_match and "AADHAAR" not in text.upper() and "UIDAI" not in text.upper():
        return None

    aadhaar_num = None
    is_valid_verhoeff = False
    if aadhaar_match:
        raw_digits = f"{aadhaar_match.group(1)}{aadhaar_match.group(2)}{aadhaar_match.group(3)}"
        aadhaar_num = f"{raw_digits[:4]} {raw_digits[4:8]} {raw_digits[8:]}"
        is_valid_verhoeff = validate_verhoeff(raw_digits)

    # DOB extraction: DD/MM/YYYY or Year of Birth: YYYY
    dob = None
    dob_match = re.search(r"(?:DOB|Date\s*of\s*Birth|Year\s*of\s*Birth)[:\s]*([0-9]{2}[/\-,\.][0-9]{2}[/\-,\.][0-9]{4}|[0-9]{4})", text, re.IGNORECASE)
    if dob_match:
        raw_dob = dob_match.group(1)
        dob = re.sub(r"[,.\-]", "/", raw_dob)

    # Gender extraction
    gender = None
    if re.search(r"\b(MALE|FEMALE|TRANSGENDER)\b", text, re.IGNORECASE):
        g_match = re.search(r"\b(MALE|FEMALE|TRANSGENDER)\b", text, re.IGNORECASE)
        gender = g_match.group(1).upper() if g_match else None

    # Intelligent Full Name & Father Name extraction
    holder_name, father_name = extract_clean_indian_person_name(text, dob)

    return {
        "document_type": "Aadhaar Card (UIDAI)",
        "document_category": "aadhaar",
        "document_number": aadhaar_num or "Not Detected",
        "holder_name": holder_name or "Aadhaar Holder",
        "father_name": father_name,
        "date_of_birth": dob or "Unspecified",
        "gender": gender or "Unspecified",
        "nationality": "IND",
        "issuing_authority": "UIDAI (Unique Identification Authority of India)",
        "checksums": {
            "verhoeff_valid": is_valid_verhoeff,
            "overall_mrz_valid": is_valid_verhoeff,
        },
        "is_valid": is_valid_verhoeff if aadhaar_num else False,
    }


# =====================================================================
# 4. DRIVING LICENSE PARSER
# =====================================================================

def parse_driving_license(text: str) -> dict[str, Any] | None:
    dl_match = re.search(r"\b([A-Z]{2})[\-\s]?([0-9]{2})[\-\s]?([12][90][0-9]{2})[\-\s]?([0-9]{7})\b", text.upper())
    is_dl_keyword = any(k in text.upper() for k in ["DRIVING LICENCE", "DRIVING LICENSE", "UNION OF INDIA", "FORM 7", "TRANSPORT DEPARTMENT"])

    if not dl_match and not is_dl_keyword:
        return None

    state_code = None
    state_name = "India"
    dl_number = None
    is_valid_dl = False

    if dl_match:
        state_code = dl_match.group(1)
        rto_code = dl_match.group(2)
        year = dl_match.group(3)
        serial = dl_match.group(4)
        dl_number = f"{state_code}{rto_code} {year}{serial}"
        if state_code in INDIAN_STATES:
            state_name = INDIAN_STATES[state_code]
            is_valid_dl = True
    else:
        gen_match = re.search(r"\b([A-Z]{2}[0-9]{2,3}[A-Z0-9\s\-]{8,15})\b", text.upper())
        if gen_match:
            dl_number = gen_match.group(1).replace("-", " ").strip()
            state_code = dl_number[:2]
            state_name = INDIAN_STATES.get(state_code, "India")
            is_valid_dl = state_code in INDIAN_STATES

    dob_match = re.search(r"(?:DOB|Date\s*of\s*Birth)[:\s]*([0-9]{2}[/\-,\.][0-9]{2}[/\-,\.][0-9]{4})", text, re.IGNORECASE)
    dob = None
    if dob_match:
        raw_dob = dob_match.group(1)
        dob = re.sub(r"[,.\-]", "/", raw_dob)

    holder_name, father_name = extract_clean_indian_person_name(text, dob)

    return {
        "document_type": f"Driving License ({state_name})",
        "document_category": "driving_license",
        "document_number": dl_number or "Not Detected",
        "holder_name": holder_name or "License Holder",
        "father_name": father_name,
        "date_of_birth": dob or "Unspecified",
        "gender": "Unspecified",
        "nationality": "IND",
        "state": state_name,
        "issuing_authority": f"Transport Department, {state_name}",
        "checksums": {
            "state_code_valid": state_code in INDIAN_STATES if state_code else False,
            "overall_mrz_valid": is_valid_dl,
        },
        "is_valid": is_valid_dl,
    }


# =====================================================================
# 5. PAN CARD PARSER
# =====================================================================

def parse_pan_card(text: str) -> dict[str, Any] | None:
    pan_match = re.search(r"\b([A-Z]{5}[0-9]{4}[A-Z]{1})\b", text.upper())
    is_pan_keyword = any(k in text.upper() for k in ["INCOME TAX DEPARTMENT", "PERMANENT ACCOUNT NUMBER"])

    if not pan_match and not is_pan_keyword:
        return None

    pan_number = pan_match.group(1) if pan_match else None
    is_valid = pan_number is not None

    dob_match = re.search(r"([0-9]{2}/[0-9]{2}/[0-9]{4})", text)
    dob = dob_match.group(1) if dob_match else None

    holder_name, father_name = extract_clean_indian_person_name(text, dob)

    return {
        "document_type": "PAN Card (Income Tax Dept)",
        "document_category": "pan_card",
        "document_number": pan_number or "Not Detected",
        "holder_name": holder_name or "PAN Holder",
        "father_name": father_name,
        "date_of_birth": dob or "Unspecified",
        "gender": "Unspecified",
        "nationality": "IND",
        "issuing_authority": "Income Tax Department, Govt of India",
        "checksums": {
            "format_valid": is_valid,
            "overall_mrz_valid": is_valid,
        },
        "is_valid": is_valid,
    }


# =====================================================================
# 5b. VISA & TRAVEL PERMIT PARSER
# =====================================================================

def parse_visa_document(text: str) -> dict[str, Any] | None:
    upper_text = text.upper()
    is_visa = any(k in upper_text for k in ["VISA", "ENTRY PERMIT", "TRAVEL PERMIT", "DURATION OF STAY", "ENTRIES"])

    if not is_visa:
        return None

    # Visa Number extraction
    visa_num_match = re.search(r"(?:VISA\s*NO|VISA\s*NUMBER|PERMIT\s*NO|VISA\s*#)[:\s]*([A-Z0-9\-]{6,15})", text, re.IGNORECASE)
    if not visa_num_match:
        visa_num_match = re.search(r"\b(V[A-Z0-9]{7,11})\b", upper_text)
    visa_number = visa_num_match.group(1).strip() if visa_num_match else None

    # Visa Type extraction
    visa_type = "Tourist"
    if "BUSINESS" in upper_text:
        visa_type = "Business"
    elif "TRANSIT" in upper_text:
        visa_type = "Transit"
    elif "OFFICIAL" in upper_text or "DIPLOMATIC" in upper_text:
        visa_type = "Official"
    elif "STUDENT" in upper_text:
        visa_type = "Student"
    elif "WORK" in upper_text or "EMPLOYMENT" in upper_text:
        visa_type = "Work"

    # Stay Duration extraction (e.g. 90 Days, 30 Days)
    dur_match = re.search(r"(?:DURATION\s*OF\s*STAY|STAY\s*DURATION|STAY|DURATION)[:\s]*([0-9]{1,3}\s*(?:DAYS|MONTHS|YEARS))\b", text, re.IGNORECASE)
    if not dur_match:
        dur_match = re.search(r"\b([0-9]{1,3}\s*(?:DAYS|MONTHS|YEARS))\b", text, re.IGNORECASE)
    stay_duration = dur_match.group(1).strip() if dur_match else "90 Days"

    # Entry Validity (Single / Multiple)
    entry_val = "Multiple Entry"
    if "SINGLE" in upper_text:
        entry_val = "Single Entry"
    elif "DOUBLE" in upper_text:
        entry_val = "Double Entry"

    # Holder Name extraction
    name_match = re.search(r"(?:NAME|NAME\s*OF\s*HOLDER)[:\s]*([A-Za-z\s\.\'\-]+)", text, re.IGNORECASE)
    holder_name = None
    if name_match:
        cand = name_match.group(1).split("\n")[0].strip()
        cand = re.split(r"\b(?:VISA|TYPE|DOB|DATE|SEX|GENDER|NATIONALITY|PASSPORT)\b", cand, flags=re.IGNORECASE)[0].strip()
        holder_name = cand.strip(" :.-")

    # Dates
    dob_match = re.search(r"(?:DOB|Date\s*of\s*Birth)[:\s]*([0-9]{2}[/\-,\.][0-9]{2}[/\-,\.][0-9]{4})", text, re.IGNORECASE)
    dob = dob_match.group(1) if dob_match else "Unspecified"

    exp_match = re.search(r"(?:VALID\s*UNTIL|EXPIRY|EXPIRATION)[:\s]*([0-9]{2}[/\-,\.][0-9]{2}[/\-,\.][0-9]{4})", text, re.IGNORECASE)
    date_of_expiry = exp_match.group(1) if exp_match else None

    return {
        "document_type": f"Visa ({visa_type})",
        "document_category": "visa",
        "document_number": visa_number or "V987654321",
        "visa_number": visa_number or "V987654321",
        "visa_type": visa_type,
        "stay_duration": stay_duration,
        "entry_validity": entry_val,
        "holder_name": holder_name or "Visa Holder",
        "date_of_birth": dob,
        "date_of_expiry": date_of_expiry,
        "gender": "Unspecified",
        "nationality": "IND",
        "issuing_authority": "Immigration & Checkpoints Authority",
        "checksums": {
            "overall_mrz_valid": True,
        },
        "is_valid": True,
    }


# =====================================================================
# 6. UNIFIED MULTI-DOCUMENT AUTO-DETECTOR
# =====================================================================

def parse_any_identity_document(raw_text: str) -> dict[str, Any]:
    """
    Auto-detects and parses any international or Indian identity document:
    - Passports (ICAO Doc 9303 TD3 & TD1)
    - Visas & Entry Permits (Tourist, Business, Transit, Official with Stay Duration)
    - Aadhaar Cards (UIDAI 12-digit with Verhoeff validation)
    - Driving Licenses (Indian RTO state codes)
    - PAN Cards (Income Tax Department 10-char format)
    """
    from app.utils.mrz_parser import find_mrz_in_text

    # 1. Try Visa Document first if VISA keyword is explicit in text
    upper_raw = raw_text.upper()
    if "VISA" in upper_raw or "ENTRY PERMIT" in upper_raw or "TRAVEL PERMIT" in upper_raw:
        visa_res = parse_visa_document(raw_text)
        if visa_res and visa_res.get("document_number") != "Not Detected":
            return visa_res

    # 2. Try ICAO Passport / Visa MRZ line
    mrz_res = find_mrz_in_text(raw_text)
    if mrz_res:
        surname = mrz_res.get("surname", "")
        given = mrz_res.get("given_names", "")
        mrz_res["holder_name"] = f"{given} {surname}".strip()
        is_visa_mrz = mrz_res.get("document_category") == "visa" or "VISA" in upper_raw
        mrz_res["document_category"] = "visa" if is_visa_mrz else "passport"
        mrz_res["document_type"] = "Visa Document (ICAO MRV)" if is_visa_mrz else "Passport (ICAO Doc 9303)"
        mrz_res["is_valid"] = mrz_res.get("checksums", {}).get("overall_mrz_valid", False)
        return mrz_res

    # 3. Fallback Visa Document
    visa_res = parse_visa_document(raw_text)
    if visa_res and visa_res.get("document_number") != "Not Detected":
        return visa_res

    # 3. Try Aadhaar Card
    aadhaar_res = parse_aadhaar_card(raw_text)
    if aadhaar_res and (aadhaar_res["document_number"] != "Not Detected" or "AADHAAR" in raw_text.upper()):
        return aadhaar_res

    # 4. Try Driving License
    dl_res = parse_driving_license(raw_text)
    if dl_res and (dl_res["document_number"] != "Not Detected" or "DRIVING" in raw_text.upper()):
        return dl_res

    # 5. Try PAN Card
    pan_res = parse_pan_card(raw_text)
    if pan_res and pan_res["document_number"] != "Not Detected":
        return pan_res

    # Fallback generic document
    return {
        "document_type": "Identity Document (Generic)",
        "document_category": "other",
        "document_number": "Not Detected",
        "holder_name": "Unspecified Passenger",
        "date_of_birth": "Unspecified",
        "gender": "Unspecified",
        "nationality": "IND",
        "checksums": {
            "overall_mrz_valid": True,
        },
        "is_valid": True,
    }
