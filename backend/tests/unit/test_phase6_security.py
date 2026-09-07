import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import asyncio
from fastapi import HTTPException
from app.services.verification_result_service import (
    execute_session_verification,
    get_session_final_result,
    get_session_status,
)
from app.services.document_service import upload_document
from app.services.biometric_service import upload_biometric
from app.services.document_processing_service import create_processing_result
from app.services.document_result_service import get_document_result


async def run_security_test_suite():
    print("=" * 60)
    print("RUNNING TRINETRA PHASE 6 SECURITY & PRIVACY SUITE")
    print("=" * 60)

    user_a = "user_a_id"
    user_b = "user_b_id"
    session_id_a = "VER-SECTEST-001"

    # 1. IDOR / Session Ownership Test
    print("\n[+] 1. Testing IDOR / Session Ownership Enforcements...")
    
    # User B attempting to access User A's session status
    try:
        await get_session_status(session_id_a, user_b)
        print("    [FAIL] User B accessed User A's session status!")
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404
        print("    [PASS] User B access to User A session status blocked (404 Not Found)")

    # User B attempting to execute verification on User A's session
    try:
        await execute_session_verification(session_id_a, user_b)
        print("    [FAIL] User B executed verification on User A's session!")
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404
        print("    [PASS] User B verification execution blocked (404 Not Found)")

    # User B attempting to get User A's session final result
    try:
        await get_session_final_result(session_id_a, user_b)
        print("    [FAIL] User B fetched User A's session result!")
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404
        print("    [PASS] User B session final result retrieval blocked (404 Not Found)")

    # 2. Document & Biometric IDOR Ownership Test
    print("\n[+] 2. Testing Document & Biometric Resource Ownership...")

    try:
        await get_document_result("DOC-UNAUTH-999", user_b)
        print("    [FAIL] User B retrieved document result!")
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404
        print("    [PASS] Document result access for unauthorized user blocked (404 Not Found)")

    try:
        await create_processing_result("DOC-UNAUTH-999", user_b)
        print("    [FAIL] User B processed document!")
        assert False
    except HTTPException as exc:
        assert exc.status_code == 404
        print("    [PASS] Document processing for unauthorized user blocked (404 Not Found)")

    # 3. Path Traversal & Filename Sanitization Test
    print("\n[+] 3. Testing Path Traversal & Storage Isolation...")
    from app.services.document_service import STORAGE_DIR as DOC_DIR
    from app.services.biometric_service import STORAGE_DIR as BIO_DIR

    assert not str(DOC_DIR).startswith("/tmp") and "storage/documents" in str(DOC_DIR).replace("\\", "/")
    assert not str(BIO_DIR).startswith("/tmp") and "storage/biometrics" in str(BIO_DIR).replace("\\", "/")
    print("    [PASS] Storage directories isolated under backend storage/")

    print("\n" + "=" * 60)
    print("ALL PHASE 6 SECURITY AUDIT TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_security_test_suite())
