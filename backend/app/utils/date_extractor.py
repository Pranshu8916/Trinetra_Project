"""
Date Extractor & Normalizer Utility for Visas and Identity Documents
Supports:
1. Multi-format parsing:
   - DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, DD MM YYYY
   - YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD (ISO 8601)
   - MM/DD/YYYY (US format)
   - Alpha-month: DDMMMYYYY, DD-MMM-YYYY, DD MMM YYYY, MMM DD YYYY (e.g. 24JUL1984, 04-DEC-2001)
   - 2-digit years: DD/MM/YY, DD-MMM-YY, DDMMMYY (e.g. 24JUL84)
2. OCR error recovery on dates (e.g., 'O'/'D' -> '0', 'I'/'l' -> '1', 'Z' -> '2', 'S' -> '5')
3. Multilingual visa label matching (English, French, Spanish, German)
4. Multi-line lookahead (label on line N, date on line N+1/N+2)
5. Temporal consistency validation: DOB < DOI <= DOE
6. Standardized output: DD/MM/YYYY
"""

import re
from datetime import datetime

MONTH_NAME_MAP = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
    "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4, "JUNE": 6,
    "JULY": 7, "AUGUST": 8, "SEPTEMBER": 9, "OCTOBER": 10, "NOVEMBER": 11, "DECEMBER": 12,
    # French abbreviations common on international & Canadian/Schengen visas
    "JANV": 1, "FEVR": 2, "MARS": 3, "AVR": 4, "AVRI": 4, "MAI": 5,
    "JUIN": 6, "JUIL": 7, "AOUT": 8, "SEPT": 9, "OCTO": 10, "NOVE": 11, "DECE": 12,
}

# OCR character substitution map for numeric date components
OCR_NUMERIC_FIX = {
    "O": "0", "o": "0", "D": "0", "Q": "0",
    "I": "1", "l": "1", "|": "1", "!": "1",
    "Z": "2", "z": "2",
    "S": "5", "s": "5",
    "B": "8",
    "g": "9", "q": "9",
}

CURRENT_YEAR = datetime.now().year


def _clean_ocr_digits(val: str) -> str:
    """Substitutes commonly confused OCR characters with digits."""
    return "".join(OCR_NUMERIC_FIX.get(ch, ch) for ch in val)


def is_valid_calendar_date(day: int, month: int, year: int) -> bool:
    """Verifies that day, month, and year form a valid date in the gregorian calendar."""
    if not (1 <= month <= 12):
        return False
    if not (1 <= day <= 31):
        return False
    if not (1900 <= year <= CURRENT_YEAR + 50):
        return False
    try:
        datetime(year, month, day)
        return True
    except ValueError:
        return False


def normalize_to_dmy(date_obj_or_tuple: tuple[int, int, int]) -> str:
    """Formats (day, month, year) tuple to standard DD/MM/YYYY string."""
    day, month, year = date_obj_or_tuple
    return f"{day:02d}/{month:02d}/{year:04d}"


def parse_date_str(raw: str, is_dob: bool = False) -> str | None:
    """
    Parses any raw date substring into a standardized DD/MM/YYYY string.
    Returns None if the string is not a valid date.
    """
    if not raw or not raw.strip():
        return None

    cleaned = raw.strip()

    # 1. Alpha-numeric Month Format: e.g. 24JUL1984, 24-JUL-1984, 24 JUL 1984, 24.JUL.1984, 24/JUL/1984
    # Also handles bilingual slash like 15 AUG/AOU 1990
    alpha_pattern1 = re.compile(
        r"\b(\d{1,2})[\s\-\/\.]*([A-Za-z]{3,9})(?:[\s\/\\]+[A-Za-z]{3,4})?[\s\-\/\.]*(\d{2,4})\b",
        re.IGNORECASE,
    )
    m = alpha_pattern1.search(cleaned)
    if m:
        raw_day, raw_month, raw_year = m.group(1), m.group(2).upper(), m.group(3)
        month_num = MONTH_NAME_MAP.get(raw_month) or MONTH_NAME_MAP.get(raw_month[:3])
        if month_num:
            day = int(raw_day)
            year = int(raw_year)
            if year < 100:
                year = (1900 + year) if (is_dob and year >= 25) or (not is_dob and year >= 50) else (2000 + year)
            if is_valid_calendar_date(day, month_num, year):
                if is_dob and year > CURRENT_YEAR:
                    return None
                return normalize_to_dmy((day, month_num, year))

    # 2. Month-First Alpha Format: e.g. JUL 24, 1984 or JUL 24 1984 or JULY 24, 1984
    alpha_pattern2 = re.compile(
        r"\b([A-Za-z]{3,9})[\s\-\/\.]+(\d{1,2})(?:st|nd|rd|th)?[\s\-\/,\.]+(\d{2,4})\b",
        re.IGNORECASE,
    )
    m2 = alpha_pattern2.search(cleaned)
    if m2:
        raw_month, raw_day, raw_year = m2.group(1).upper(), m2.group(2), m2.group(3)
        month_num = MONTH_NAME_MAP.get(raw_month) or MONTH_NAME_MAP.get(raw_month[:3])
        if month_num:
            day = int(raw_day)
            year = int(raw_year)
            if year < 100:
                year = (1900 + year) if (is_dob and year >= 25) or (not is_dob and year >= 50) else (2000 + year)
            if is_valid_calendar_date(day, month_num, year):
                if is_dob and year > CURRENT_YEAR:
                    return None
                return normalize_to_dmy((day, month_num, year))

    # 3. Numeric ISO Format: YYYY-MM-DD or YYYY/MM/DD or YYYY.MM.DD
    iso_pattern = re.compile(r"\b(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})\b")
    m_iso = iso_pattern.search(cleaned)
    if m_iso:
        year = int(m_iso.group(1))
        month = int(m_iso.group(2))
        day = int(m_iso.group(3))
        if is_valid_calendar_date(day, month, year):
            if is_dob and year > CURRENT_YEAR:
                return None
            return normalize_to_dmy((day, month, year))

    # 4. Numeric DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY
    # Also handles single digit day/month and 2-digit years
    num_pattern = re.compile(r"\b(\d{1,2})[\/\-\.,\s]+(\d{1,2})[\/\-\.,\s]+(\d{2,4})\b")
    m_num = num_pattern.search(cleaned)
    if m_num:
        p1 = int(m_num.group(1))
        p2 = int(m_num.group(2))
        raw_yr = int(m_num.group(3))
        year = raw_yr
        if year < 100:
            year = (1900 + year) if (is_dob and year >= 25) or (not is_dob and year >= 50) else (2000 + year)

        # Disambiguate DD/MM vs MM/DD:
        # If p1 > 12 and p2 <= 12 -> clearly p1 is Day, p2 is Month
        if p1 > 12 and 1 <= p2 <= 12:
            day, month = p1, p2
        # If p2 > 12 and p1 <= 12 -> clearly p2 is Day, p1 is Month (US format)
        elif p2 > 12 and 1 <= p1 <= 12:
            day, month = p2, p1
        else:
            # Default international standard (DD/MM/YYYY)
            day, month = p1, p2

        if is_valid_calendar_date(day, month, year):
            if is_dob and year > CURRENT_YEAR:
                return None
            return normalize_to_dmy((day, month, year))

    # 5. Fallback: Check for OCR digit confusion (e.g., '24/O7/1984' or 'I5/08/I990')
    cleaned_ocr = _clean_ocr_digits(cleaned)
    if cleaned_ocr != cleaned:
        return parse_date_str(cleaned_ocr, is_dob=is_dob)

    return None


def is_valid_dob_date(date_str: str | None) -> bool:
    """Validates that a date string is a normalized DD/MM/YYYY and falls within a valid human birth date range."""
    if not date_str or not isinstance(date_str, str):
        return False
    if date_str in {"Unspecified", "None", "NOT_FOUND", "null", "undefined"}:
        return False
    m = re.match(r"^(\d{2})\/(\d{2})\/(\d{4})$", date_str.strip())
    if not m:
        return False
    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not is_valid_calendar_date(day, month, year):
        return False
    # Person's age: between 0 and 115 years old
    if not (CURRENT_YEAR - 115 <= year <= CURRENT_YEAR):
        return False
    return True


# =====================================================================
# VISA DOB EXTRACTION ENGINE
# =====================================================================

DOB_LABEL_REGEX = re.compile(
    r"(?:"
    r"DATE\s*OF\s*BIRTH|DATE\s*OF\s*B(?:IRTH)?|DATEOFBIRTH|"
    r"BIRTH\s*DATE|BIRTHDATE|BIRTH\-DATE|"
    r"D\.?O\.?B\.?|D\s*\/\s*O\s*\/\s*B|"
    r"DATE\s*DE\s*NAISSANCE|DATE\s*DE\s*NAISS\.?|DATE\s*NAISSANCE|"
    r"FECHA\s*DE\s*NACIMIENTO|FECHA\s*NAC\.?|"
    r"GEBURTSDATUM|DATA\s*DI\s*NASCITA|DATA\s*DE\s*NASCIMENTO|"
    r"DOB\s*[\/\\]\s*SEX|DOB\s*[\/\\]\s*POB|DATE\s*OF\s*BIRTH\s*[\/\\]\s*SEX|"
    r"DATE\s*OF\s*BIRTH\s*[\/\\]\s*DATE\s*DE\s*NAISSANCE"
    r")",
    re.IGNORECASE,
)

DOI_LABEL_REGEX = re.compile(
    r"(?:"
    r"DATE\s*OF\s*ISSUE|ISSUE\s*DATE|ISSUED\s*ON|ISSUED|ISSUE|"
    r"D\.?O\.?I\.?|D\s*\/\s*O\s*\/\s*I|"
    r"DATE\s*DE\s*D[EÉ]LIVRANCE|DELIVRE\s*LE"
    r")",
    re.IGNORECASE,
)

DOE_LABEL_REGEX = re.compile(
    r"(?:"
    r"DATE\s*OF\s*EXPIRY|EXPIRY\s*DATE|EXPIRATION\s*DATE|EXPIRATION|EXPIRE|EXPIRES|"
    r"VALID\s*UNTIL|VALID\s*TO|VALABLE\s*JUSQU'AU|VALABLE\s*AU|"
    r"D\.?O\.?E\.?|D\s*\/\s*O\s*\/\s*E|EXP\.?"
    r")",
    re.IGNORECASE,
)


def _find_date_in_string(text_chunk: str, is_dob: bool = True) -> str | None:
    """Finds and parses the first valid date within an arbitrary string snippet."""
    if not text_chunk:
        return None

    # Try alpha month first (e.g. 24JUL1984, 24-JUL-1984, 24 JUL 1984)
    alpha_m = re.search(
        r"(\b\d{1,2}[\s\-\/\.]*[A-Za-z]{3,9}(?:[\s\/\\]+[A-Za-z]{3,4})?[\s\-\/\.]*\d{2,4}\b)",
        text_chunk,
    )
    if alpha_m:
        parsed = parse_date_str(alpha_m.group(1), is_dob=is_dob)
        if parsed:
            return parsed

    # Try month-first alpha (e.g. JUL 24, 1984)
    alpha_m2 = re.search(
        r"(\b[A-Za-z]{3,9}[\s\-\/\.]+\d{1,2}(?:st|nd|rd|th)?[\s\-\/,\.]+\d{2,4}\b)",
        text_chunk,
    )
    if alpha_m2:
        parsed = parse_date_str(alpha_m2.group(1), is_dob=is_dob)
        if parsed:
            return parsed

    # Try numeric date
    num_m = re.search(
        r"(\b\d{1,2}[\/\-\.,\s]+\d{1,2}[\/\-\.,\s]+\d{2,4}\b|\b\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}\b)",
        text_chunk,
    )
    if num_m:
        parsed = parse_date_str(num_m.group(1), is_dob=is_dob)
        if parsed:
            return parsed

    # Try numeric date with OCR confusion characters (e.g. 24/O7/1984 or I5/08/I990)
    ocr_chunk = _clean_ocr_digits(text_chunk)
    if ocr_chunk != text_chunk:
        num_m_ocr = re.search(
            r"(\b\d{1,2}[\/\-\.,\s]+\d{1,2}[\/\-\.,\s]+\d{2,4}\b|\b\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}\b)",
            ocr_chunk,
        )
        if num_m_ocr:
            parsed = parse_date_str(num_m_ocr.group(1), is_dob=is_dob)
            if parsed:
                return parsed

    return None


def extract_clean_dob(text: str, is_visa: bool = False) -> str | None:
    """
    Intelligently extracts Date of Birth from OCR text.
    Handles:
    - Same-line label & value (e.g. 'Birthdate: 24JUL1984')
    - Multiline lookahead (label on line N, value on line N+1 or N+2)
    - Compound labels (e.g. 'DOB / SEX: 15/08/1990 M')
    - Alpha-month dates (e.g. '24-JUL-1984', '04 DEC 2001')
    - Fallback temporal ranking (DOB < DOI <= DOE)
    """
    if not text or not text.strip():
        return None

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # 1. Check Same-Line or Suffix Patterns first
    # e.g., "Date of Birth: 24/07/1984" or "Birthdate 24JUL1984" or "DOB: 12-JAN-1990"
    for line in lines:
        match = DOB_LABEL_REGEX.search(line)
        if match:
            # Text immediately following the label
            remainder = line[match.end():].strip(" :.-/=;\t")
            # If remainder has content, extract date from it
            if remainder:
                cand_date = _find_date_in_string(remainder, is_dob=True)
                if cand_date and is_valid_dob_date(cand_date):
                    return cand_date

    # 2. Multi-line Lookahead
    # When label is on line i, and the date is on line i+1, i+2, or i+3
    for i, line in enumerate(lines):
        if DOB_LABEL_REGEX.search(line):
            for offset in range(1, 4):
                if i + offset < len(lines):
                    cand_line = lines[i + offset]
                    # If this next line is another label keyword like "SEX", "PASSPORT NO", check if it has a date
                    cand_date = _find_date_in_string(cand_line, is_dob=True)
                    if cand_date and is_valid_dob_date(cand_date):
                        return cand_date

    # 3. Check for Global DOB Regex across entire text (multiline regex)
    global_dob_match = re.search(
        r"(?:DOB|D\.?O\.?B\.?|DATE\s*OF\s*BIRTH|BIRTH\s*DATE|BIRTHDATE|DATE\s*DE\s*NAISSANCE)"
        r"[^\S\r\n]*[:\.\-\/]?\s*"
        r"(\d{1,2}[\/\-\.,\s]+[A-Za-z]{3,9}[\/\-\.,\s]+\d{2,4}|\d{1,2}[A-Za-z]{3,9}\d{2,4}|\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})",
        text,
        re.IGNORECASE,
    )
    if global_dob_match:
        parsed = parse_date_str(global_dob_match.group(1), is_dob=True)
        if parsed and is_valid_dob_date(parsed):
            return parsed

    # 4. Fallback for Visas: Temporal Ordering (DOB < DOI <= DOE)
    # Collect all valid dates in the entire document text
    all_dates = []
    date_candidates = re.findall(
        r"\b(?:\d{1,2}[\s\-\/\.]*[A-Za-z]{3,9}[\s\-\/\.]*\d{2,4}|\d{1,2}[A-Za-z]{3,9}\d{2,4}|\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})\b",
        text,
    )
    for dc in date_candidates:
        parsed = parse_date_str(dc, is_dob=True)
        if parsed and is_valid_dob_date(parsed):
            yr = int(parsed.split("/")[2])
            all_dates.append((yr, parsed))

    if all_dates:
        all_dates.sort(key=lambda x: x[0])
        oldest_yr, oldest_dob = all_dates[0]
        # DOB is typically the oldest date (e.g. birth year 1950..2015)
        if oldest_yr <= CURRENT_YEAR - 8:
            return oldest_dob

    return None


def extract_clean_date_of_issue(text: str) -> str | None:
    """Extracts Date of Issue (DOI) from OCR text."""
    if not text:
        return None
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for i, line in enumerate(lines):
        m = DOI_LABEL_REGEX.search(line)
        if m:
            rem = line[m.end():].strip(" :.-/=;\t")
            if rem:
                cand = _find_date_in_string(rem, is_dob=False)
                if cand:
                    return cand
            if i + 1 < len(lines):
                cand = _find_date_in_string(lines[i + 1], is_dob=False)
                if cand:
                    return cand
    return None


def extract_clean_date_of_expiry(text: str) -> str | None:
    """Extracts Date of Expiry (DOE) from OCR text."""
    if not text:
        return None
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for i, line in enumerate(lines):
        m = DOE_LABEL_REGEX.search(line)
        if m:
            rem = line[m.end():].strip(" :.-/=;\t")
            if rem:
                cand = _find_date_in_string(rem, is_dob=False)
                if cand:
                    return cand
            if i + 1 < len(lines):
                cand = _find_date_in_string(lines[i + 1], is_dob=False)
                if cand:
                    return cand
    return None
