"""
Unit tests for Visa Date of Birth (DOB) OCR Extraction and MRV Parsing
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.utils.date_extractor import (
    extract_clean_dob,
    extract_clean_date_of_issue,
    extract_clean_date_of_expiry,
    is_valid_dob_date,
    parse_date_str,
)
from app.utils.mrz_parser import find_mrz_in_text, parse_td3_passport
from app.services.document_extraction_service import extract_document_fields
from app.utils.indian_id_parser import parse_visa_document


def test_us_visa_birthdate_format():
    """US Visas use 'Birthdate' label with DDMMMYYYY format (e.g. 24JUL1984)."""
    text = (
        "UNITED STATES OF AMERICA VISA\n"
        "Control Number: 202100123456\n"
        "Surname: PATEL\n"
        "Given Name: RUSHIK JAYESHKUMAR\n"
        "Passport Number: P12345678\n"
        "Entries: M\n"
        "Birthdate: 24JUL1984\n"
        "Nationality: IND\n"
        "Issue Date: 15JAN2021\n"
        "Expiration Date: 14JAN2031\n"
    )
    dob = extract_clean_dob(text, is_visa=True)
    assert dob == "24/07/1984", f"Expected 24/07/1984, got {dob}"

    res = extract_document_fields(text)
    assert res["date_of_birth"] == "24/07/1984", f"Expected 24/07/1984, got {res['date_of_birth']}"


def test_visa_multiline_ocr():
    """OCR frequently places the label on line N and the date value on line N+1."""
    text = (
        "VISA / ENTRY PERMIT\n"
        "Holder: RUSHIK JAYESHKUMAR PATEL\n"
        "Date of Birth\n"
        "04-DEC-2001\n"
        "Country of Nationality\n"
        "INDIA\n"
        "Visa Number: V87654321\n"
    )
    dob = extract_clean_dob(text, is_visa=True)
    assert dob == "04/12/2001", f"Expected 04/12/2001, got {dob}"

    res = extract_document_fields(text)
    assert res["date_of_birth"] == "04/12/2001", f"Expected 04/12/2001, got {res['date_of_birth']}"


def test_bilingual_schengen_visa():
    """Bilingual labels (English/French) and space-separated alpha months."""
    text = (
        "SCHENGEN VISA\n"
        "Nom, Prenom: PATEL RUSHIK\n"
        "Date de naissance / Date of birth\n"
        "12 JAN 1990\n"
        "Nationalite: IND\n"
        "Valable du: 01/06/2024 au: 01/12/2024\n"
        "Numero de visa: V12345678\n"
    )
    dob = extract_clean_dob(text, is_visa=True)
    assert dob == "12/01/1990", f"Expected 12/01/1990, got {dob}"

    res = extract_document_fields(text)
    assert res["date_of_birth"] == "12/01/1990", f"Expected 12/01/1990, got {res['date_of_birth']}"


def test_compound_label_dob_sex():
    """Compound label 'DOB / SEX: 15/08/1992 M'."""
    text = (
        "TRAVEL VISA - MULTIPLE ENTRY\n"
        "Full Name: RUSHIK PATEL\n"
        "DOB / SEX: 15/08/1992 M\n"
        "Nationality: IND\n"
        "Duration of Stay: 90 Days\n"
    )
    dob = extract_clean_dob(text, is_visa=True)
    assert dob == "15/08/1992", f"Expected 15/08/1992, got {dob}"

    res = extract_document_fields(text)
    assert res["date_of_birth"] == "15/08/1992", f"Expected 15/08/1992, got {res['date_of_birth']}"


def test_ocr_letter_noise_in_dates():
    """Handles OCR character confusion like letter 'O' instead of digit '0'."""
    text = (
        "VISA DOCUMENT\n"
        "NAME: RUSHIK PATEL\n"
        "DOB: 24/O7/1984\n"
        "NATIONALITY: IND\n"
        "VISA NO: V99887766\n"
    )
    dob = extract_clean_dob(text, is_visa=True)
    assert dob == "24/07/1984", f"Expected 24/07/1984, got {dob}"


def test_mrv_does_not_slice_passenger_name():
    """
    CRITICAL BUG REGRESSION TEST:
    Ensures that Line 1 (containing the passenger name RUSHIK) is NEVER parsed
    as Line 2, which previously caused date_of_birth to be extracted as 'USHIK<'.
    """
    line1 = "V<IND<<PATEL<<RUSHIK<JAYESHKUMAR<<<<<<<<<<<<<<<<<"
    line2 = "0412167650IND0112048M2604158<<<<<<<<<<<<<<<1"

    # 1. Normal order
    parsed = parse_td3_passport(line1, line2)
    assert parsed["date_of_birth"] == "04/12/2001", f"Expected 04/12/2001, got {parsed['date_of_birth']}"
    assert "USHIK" not in str(parsed["date_of_birth"])
    assert parsed["surname"] == "PATEL"
    assert "RUSHIK" in parsed["given_names"]

    # 2. Reversed order (Line 2 first, Line 1 second)
    parsed_rev = parse_td3_passport(line2, line1)
    assert parsed_rev["date_of_birth"] == "04/12/2001", f"Expected 04/12/2001, got {parsed_rev['date_of_birth']}"
    assert "USHIK" not in str(parsed_rev["date_of_birth"])

    # 3. Line 1 alone (Line 2 unreadable or missing)
    # Must NOT produce 'USHIK<' as DOB!
    parsed_single = parse_td3_passport(line1, "")
    assert parsed_single["date_of_birth"] is None, f"Expected None, got {parsed_single['date_of_birth']}"


def test_mrv_full_text_finder():
    """Tests find_mrz_in_text with visa OCR text."""
    text = (
        "CONSULAR SERVICES\n"
        "VISA TYPE: TOURIST\n"
        "V<IND<<PATEL<<RUSHIK<JAYESHKUMAR<<<<<<<<<<<<<<<<<\n"
        "0412167650IND0112048M2604158<<<<<<<<<<<<<<<1\n"
    )
    mrz = find_mrz_in_text(text)
    assert mrz is not None
    assert mrz["date_of_birth"] == "04/12/2001"
    assert "USHIK" not in str(mrz["date_of_birth"])

    fields = extract_document_fields(text)
    assert fields["date_of_birth"] == "04/12/2001"
    assert fields["name"] == "RUSHIK JAYESHKUMAR PATEL"


def test_temporal_fallback_oldest_date_is_dob():
    """
    When multiple dates appear in a visa without standard labels,
    the earliest date is chosen as DOB and must not be equal to DOI or DOE.
    """
    text = (
        "ENTRY VISA\n"
        "PATEL, RUSHIK\n"
        "15/08/1990\n"
        "10/01/2021\n"
        "09/01/2031\n"
        "VISA NO: V1234567\n"
    )
    dob = extract_clean_dob(text, is_visa=True)
    assert dob == "15/08/1990", f"Expected 15/08/1990, got {dob}"


if __name__ == "__main__":
    test_us_visa_birthdate_format()
    test_visa_multiline_ocr()
    test_bilingual_schengen_visa()
    test_compound_label_dob_sex()
    test_ocr_letter_noise_in_dates()
    test_mrv_does_not_slice_passenger_name()
    test_mrv_full_text_finder()
    test_temporal_fallback_oldest_date_is_dob()
    print("\nALL VISA DOB EXTRACTION TESTS PASSED SUCCESSFULLY! [OK]")
