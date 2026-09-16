import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.services.document_extraction_service import extract_document_fields
from app.services.verification_result_service import execute_session_verification
from fastapi import HTTPException


def test_api_error_handling_contracts():
    print("\n[+] Testing Phase 5: Error Handling Contracts...")

    null_ocr_text = ""
    extracted = extract_document_fields(null_ocr_text)
    print("DEBUG EXTRACTED:", extracted)
    assert extracted["name"] is None
    assert extracted["document_number"] is None
    assert extracted["nationality"] is None
    print("    Null OCR extraction handling: [PASSED]")

    # 2. Test keyword label pollution prevention
    polluted_text = "PASSPORT NATIONALITY EXPIRY DATE 09/03/2031"
    extracted_polluted = extract_document_fields(polluted_text)
    assert extracted_polluted["nationality"] is None or extracted_polluted["nationality"] != "EXPIRY"
    print("    Keyword label pollution prevention: [PASSED]")


import pytest


@pytest.mark.anyio
async def test_session_not_found_contract():
    print("\n[+] Testing Phase 5: Session Not Found (404) Contract...")
    caught_404 = False
    try:
        await execute_session_verification("NON_EXISTENT_SESSION_999", "test_user")
    except HTTPException as exc_info:
        if exc_info.status_code == 404 and "not found" in exc_info.detail.lower():
            caught_404 = True
    assert caught_404, "Expected HTTPException 404 for non-existent session"
    print("    Session Not Found 404 Contract: [PASSED]")


if __name__ == "__main__":
    import asyncio
    print("=" * 60)
    print("RUNNING TRINETRA PHASE 5 ERROR HANDLING UNIT TESTS")
    print("=" * 60)
    test_api_error_handling_contracts()
    asyncio.run(test_session_not_found_contract())
    print("\n" + "=" * 60)
    print("PHASE 5 UNIT TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)
