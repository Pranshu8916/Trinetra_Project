import re
from typing import Any

from app.utils.mrz_parser import find_mrz_in_text
from app.utils.indian_id_parser import parse_any_identity_document


def _normalize_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    return text


EXCLUDED_LABEL_KEYWORDS = {
    "EXPIRY", "EXPIRE", "EXPIRED", "DATE", "ISSUE", "ISSUED",
    "PASSPORT", "DOCUMENT", "NUMBER", "GIVEN", "SURNAME", "NAME",
    "GENDER", "SEX", "NATIONALITY", "CITIZENSHIP", "TYPE", "CODE"
}


def extract_document_fields(
    raw_text: str | None,
    document_type_hint: str | None = None,
) -> dict[str, Any]:
    if not raw_text or not raw_text.strip():
        return {
            "name": None,
            "document_number": None,
            "document_type": document_type_hint,
            "date_of_birth": None,
            "date_of_issue": None,
            "date_of_expiry": None,
            "nationality": None,
            "gender": None,
            "address": None,
            "field_confidence": {},
            "ocr_confidence": None,
        }

    text = _normalize_text(raw_text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    extracted: dict[str, Any] = {
        "name": None,
        "document_number": None,
        "document_type": None,
        "date_of_birth": None,
        "date_of_issue": None,
        "date_of_expiry": None,
        "nationality": None,
        "gender": None,
        "address": None,
    }
    field_confidence: dict[str, float] = {}

    # Run Indian & Global ID parser (Aadhaar UIDAI Verhoeff, Driving License RTO, PAN Card, Passport)
    parsed_id = parse_any_identity_document(raw_text)
    if parsed_id and parsed_id.get("document_type"):
        extracted["document_type"] = parsed_id["document_type"]
        field_confidence["document_type"] = 0.98
        if parsed_id.get("holder_name"):
            extracted["name"] = parsed_id["holder_name"]
            field_confidence["name"] = 0.95
        if parsed_id.get("document_number"):
            extracted["document_number"] = parsed_id["document_number"]
            field_confidence["document_number"] = 0.99
        if parsed_id.get("date_of_birth"):
            extracted["date_of_birth"] = parsed_id["date_of_birth"]
            field_confidence["date_of_birth"] = 0.95
        if parsed_id.get("gender"):
            extracted["gender"] = parsed_id["gender"]
            field_confidence["gender"] = 0.95
        if parsed_id.get("nationality"):
            extracted["nationality"] = parsed_id["nationality"]
            field_confidence["nationality"] = 0.95
        extracted["is_valid_checksum"] = parsed_id.get("is_valid", True)
        extracted["issuing_authority"] = parsed_id.get("issuing_authority")
        extracted["father_name"] = parsed_id.get("father_name")
        extracted["state"] = parsed_id.get("state")
        extracted["visa_number"] = parsed_id.get("visa_number")
        extracted["visa_type"] = parsed_id.get("visa_type")
        extracted["stay_duration"] = parsed_id.get("stay_duration")
        extracted["entry_validity"] = parsed_id.get("entry_validity")

    # Check for ICAO Doc 9303 MRZ lines first
    mrz_data = find_mrz_in_text(raw_text)
    if mrz_data:
        has_mrz_fields = bool(mrz_data.get("surname") or mrz_data.get("given_names") or mrz_data.get("document_number"))
        if mrz_data.get("checksums", {}).get("overall_mrz_valid") or has_mrz_fields:
            if "VISA" in text.upper() or mrz_data.get("document_category") == "visa" or str(mrz_data.get("document_type", "")).startswith("V"):
                extracted["document_type"] = "visa"
            else:
                extracted["document_type"] = "passport"
            field_confidence["document_type"] = 0.99

            full_name = f"{mrz_data.get('given_names', '')} {mrz_data.get('surname', '')}".strip()
            if full_name:
                extracted["name"] = full_name
                field_confidence["name"] = 0.99

            if mrz_data.get("document_number"):
                extracted["document_number"] = mrz_data["document_number"]
                field_confidence["document_number"] = 0.99

            if mrz_data.get("date_of_birth"):
                extracted["date_of_birth"] = mrz_data["date_of_birth"]
                field_confidence["date_of_birth"] = 0.99

            if mrz_data.get("expiration_date"):
                extracted["date_of_expiry"] = mrz_data["expiration_date"]
                field_confidence["date_of_expiry"] = 0.99

            if mrz_data.get("nationality") and mrz_data["nationality"] not in EXCLUDED_LABEL_KEYWORDS:
                extracted["nationality"] = mrz_data["nationality"]
                field_confidence["nationality"] = 0.99

            sex = mrz_data.get("sex")
            if sex in {"M", "F"}:
                extracted["gender"] = "MALE" if sex == "M" else "FEMALE"
                field_confidence["gender"] = 0.99

    # 1. Document Type Detection (if not resolved by MRZ)
    upper_text = text.upper()
    if not extracted["document_type"]:
        if "PASSPORT" in upper_text:
            extracted["document_type"] = "passport"
            field_confidence["document_type"] = 0.95
        elif "DRIVING LICENCE" in upper_text or "DRIVER LICENSE" in upper_text or "DRIVING LICENSE" in upper_text:
            extracted["document_type"] = "driving_license"
            field_confidence["document_type"] = 0.95
        elif "PERMANENT ACCOUNT NUMBER" in upper_text or "PAN CARD" in upper_text:
            extracted["document_type"] = "pan_card"
            field_confidence["document_type"] = 0.95
        elif "AADHAAR" in upper_text:
            extracted["document_type"] = "aadhaar_card"
            field_confidence["document_type"] = 0.95
        elif "GOVERNMENT IDENTITY" in upper_text or "NATIONAL ID" in upper_text or "IDENTITY CARD" in upper_text:
            extracted["document_type"] = "national_id"
            field_confidence["document_type"] = 0.92
        elif "TAX DOCUMENT" in upper_text:
            extracted["document_type"] = "tax_id"
            field_confidence["document_type"] = 0.90
        elif document_type_hint:
            extracted["document_type"] = document_type_hint
            field_confidence["document_type"] = 0.70

    # 2. Name Extraction (if not resolved by MRZ)
    if not extracted["name"]:
        name_match = re.search(
            r"(?:FULL\s+NAME|GIVEN\s+NAME|SURNAME|NAME)\s*[:\.\-]?\s*([A-Za-z\s\.\'\-]+)",
            text,
            re.IGNORECASE,
        )
        if name_match:
            candidate_name = name_match.group(1).split("\n")[0].strip()
            candidate_name = re.split(r"\b(?:DOB|DATE|SEX|GENDER|NO|DOC|ISSUED|EXPIRY)\b", candidate_name, flags=re.IGNORECASE)[0].strip()
            candidate_name = candidate_name.strip(" :.-")
            if candidate_name and len(candidate_name) >= 2 and any(c.isalpha() for c in candidate_name):
                if candidate_name.upper() not in EXCLUDED_LABEL_KEYWORDS:
                    extracted["name"] = candidate_name
                    field_confidence["name"] = 0.92

    # 3. Document Number Extraction (if not resolved by MRZ)
    if not extracted["document_number"]:
        doc_no_patterns = [
            r"(?:DOCUMENT\s*NO|DOCUMENT\s*NUMBER|DOC\s*NO|DOC\s*#)\s*[:\.\-]?\s*([A-Z0-9\-\/]+)",
            r"(?:PASS(?:PORT)?\s*NO|PASS(?:PORT)?\s*#)\s*[:\.\-]?\s*([A-Z0-9\-\/]+)",
            r"(?:ID\s*NO|ID\s*NUMBER|CARD\s*NO)\s*[:\.\-]?\s*([A-Z0-9\-\/]+)",
            r"(?:TAX\s*DOCUMENT\s*ID)\s*[:\.\-]?\s*([A-Z0-9\-\/]+)",
            r"\b(TRN-[0-9]{4}-[0-9]{4}-[0-9]{2})\b",
            r"\b([A-Z][0-9]{7,8})\b",
            r"\b([A-Z]{5}[0-9]{4}[A-Z])\b",
        ]
        for pattern in doc_no_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doc_no = match.group(1).strip()
                if len(doc_no) >= 4 and doc_no.upper() not in EXCLUDED_LABEL_KEYWORDS:
                    extracted["document_number"] = doc_no
                    field_confidence["document_number"] = 0.98 if "TRN-" in doc_no or len(doc_no) >= 8 else 0.88
                    break

    # 4. Date of Birth (DOB) (if not resolved by MRZ)
    if not extracted["date_of_birth"]:
        dob_match = re.search(
            r"(?:DOB|D\.O\.B|DATE\s+OF\s+BIRTH|BIRTH\s+DATE)\s*[:\.\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})",
            text,
            re.IGNORECASE,
        )
        if dob_match:
            extracted["date_of_birth"] = dob_match.group(1).strip()
            field_confidence["date_of_birth"] = 0.95
        else:
            alt_dob = re.search(r"\b(?:oe|dob|db)\s+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b", text, re.IGNORECASE)
            if alt_dob:
                extracted["date_of_birth"] = alt_dob.group(1).strip()
                field_confidence["date_of_birth"] = 0.80

    # 5. Date of Issue (DOI)
    doi_match = re.search(
        r"(?:DOI|D\.O\.I|DATE\s+OF\s+ISSUE|ISSUE\s+DATE|ISSUED\s+ON|DOT|DOL|D0I|OT|DO)\s*[:\.\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
        text,
        re.IGNORECASE,
    )
    if doi_match:
        extracted["date_of_issue"] = doi_match.group(1).strip()
        field_confidence["date_of_issue"] = 0.95
    else:
        alt_doi = re.search(r"\b(?:doi|issue|issued|ot|do)\s+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b", text, re.IGNORECASE)
        if alt_doi:
            extracted["date_of_issue"] = alt_doi.group(1).strip()
            field_confidence["date_of_issue"] = 0.80

    # 6. Date of Expiry (DOE) (if not resolved by MRZ)
    if not extracted["date_of_expiry"]:
        doe_match = re.search(
            r"(?:DOE|D\.O\.E|DATE\s+OF\s+EXPIRY|EXPIRY\s+DATE|EXPIRATION\s+DATE|VALID\s+UNTIL|EXP)\s*[:\.\-]?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
            text,
            re.IGNORECASE,
        )
        if doe_match:
            extracted["date_of_expiry"] = doe_match.group(1).strip()
            field_confidence["date_of_expiry"] = 0.95

    # 7. Gender (if not resolved by MRZ)
    if not extracted["gender"]:
        gender_match = re.search(
            r"(?:GENDER|SEX)\s*[:\.\-]?\s*(MALE|FEMALE|M|F|OTHER|X)\b",
            text,
            re.IGNORECASE,
        )
        if gender_match:
            raw_gender = gender_match.group(1).upper()
            if raw_gender in {"M", "MALE"}:
                extracted["gender"] = "MALE"
            elif raw_gender in {"F", "FEMALE"}:
                extracted["gender"] = "FEMALE"
            elif raw_gender in {"X", "OTHER"}:
                extracted["gender"] = "OTHER"
            field_confidence["gender"] = 0.95

    # 8. Nationality (if not resolved by MRZ)
    if not extracted["nationality"]:
        nat_match = re.search(
            r"(?:NATIONALITY|CITIZENSHIP)\s*[:\.\-]?\s*([A-Za-z]+)",
            text,
            re.IGNORECASE,
        )
        if nat_match:
            nat_cand = nat_match.group(1).strip()
            if len(nat_cand) >= 3 and nat_cand.upper() not in EXCLUDED_LABEL_KEYWORDS:
                extracted["nationality"] = nat_cand.upper()
                field_confidence["nationality"] = 0.90

    # 9. Address
    addr_match = re.search(
        r"(?:ADDRESS|RESIDENCE)\s*[:\.\-]?\s*([A-Za-z0-9\s,\-\./#]+)",
        text,
        re.IGNORECASE,
    )
    if addr_match:
        candidate_addr = addr_match.group(1).split("\n")[0].strip()
        if len(candidate_addr) >= 5 and candidate_addr.upper() not in EXCLUDED_LABEL_KEYWORDS:
            extracted["address"] = candidate_addr
            field_confidence["address"] = 0.85

    # Calculate overall confidence
    if field_confidence:
        ocr_confidence = round(sum(field_confidence.values()) / len(field_confidence), 2)
    else:
        ocr_confidence = 0.50 if len(lines) > 0 else 0.0

    return {
        "name": extracted["name"],
        "document_number": extracted["document_number"],
        "document_type": extracted["document_type"],
        "date_of_birth": extracted["date_of_birth"],
        "date_of_issue": extracted["date_of_issue"],
        "date_of_expiry": extracted["date_of_expiry"],
        "nationality": extracted["nationality"],
        "gender": extracted["gender"],
        "address": extracted["address"],
        "field_confidence": field_confidence,
        "ocr_confidence": ocr_confidence,
        "is_valid_checksum": extracted.get("is_valid_checksum", True),
        "issuing_authority": extracted.get("issuing_authority"),
        "state": extracted.get("state"),
        "visa_number": extracted.get("visa_number"),
        "visa_type": extracted.get("visa_type"),
        "stay_duration": extracted.get("stay_duration"),
        "entry_validity": extracted.get("entry_validity"),
    }
