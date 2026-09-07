import io
import json
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from PIL import Image, ImageDraw

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

BASE_URL = "http://127.0.0.1:8000"


def request(method, path, data=None, headers=None, files=None):
    url = f"{BASE_URL}{path}"
    req_headers = headers.copy() if headers else {}
    body = None

    if files:
        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        req_headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        body_parts = []
        for field_name, (filename, file_bytes, content_type) in files.items():
            body_parts.append(f"--{boundary}\r\n".encode())
            body_parts.append(
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode()
            )
            body_parts.append(f"Content-Type: {content_type}\r\n\r\n".encode())
            body_parts.append(file_bytes)
            body_parts.append(b"\r\n")
        body_parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(body_parts)
    elif data is not None:
        req_headers["Content-Type"] = "application/json"
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            return resp.status, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(resp_body)
        except Exception:
            parsed = resp_body
        return e.code, parsed


def create_sample_id_image():
    img = Image.new("RGB", (700, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(10, 10), (690, 290)], outline=(0, 0, 0), width=3)
    draw.text((30, 30), "GOVERNMENT IDENTITY CARD", fill=(0, 0, 0))
    draw.text((30, 80), "NAME: JOHNATHAN DOE", fill=(0, 0, 0))
    draw.text((30, 130), "DOB: 15/08/1990", fill=(0, 0, 0))
    draw.text((30, 180), "DOCUMENT NO: TRN-9876-5432-10", fill=(0, 0, 0))
    draw.text((30, 230), "ISSUED BY: TRINETRA VERIFICATION AUTHORITY", fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def run_tests():
    print("==================================================")
    print("   PHASE 8 RUNTIME VERIFICATION SUITE")
    print("==================================================")

    # 1. Health check
    status, body = request("GET", "/api/health")
    print(f"\n[1] Health Check: Status {status}, Body: {body}")
    assert status == 200 and body["status"] == "ok" and body["database"] == "connected"

    # 2. Create and Login User 1
    u1_username = f"tester_{uuid.uuid4().hex[:6]}"
    u1_password = "SecurePassword123!"
    status, body = request(
        "POST",
        "/api/users",
        {"username": u1_username, "password": u1_password, "role": "operator"},
    )
    print(f"\n[2] Create User 1 ({u1_username}): Status {status}")
    assert status == 200

    status, body = request(
        "POST",
        "/api/auth/login",
        {"username": u1_username, "password": u1_password},
    )
    print(f"    Login User 1: Status {status}")
    assert status == 200 and "access_token" in body
    u1_headers = {"Authorization": f"Bearer {body['access_token']}"}

    # 3. Create Verification Session
    status, session_data = request(
        "POST",
        "/api/verification/sessions",
        {"subject_name": "Johnathan Doe", "document_type": "national_id"},
        headers=u1_headers,
    )
    print(f"\n[3] Create Verification Session: Status {status}")
    assert status == 200
    session_id = session_data["session_id"]
    print(f"    Session ID: {session_id}")

    # 4. Upload Document (PNG)
    image_bytes = create_sample_id_image()
    files = {"file": ("national_id.png", image_bytes, "image/png")}
    status, upload_data = request(
        "POST",
        f"/api/verification/sessions/{session_id}/document",
        headers=u1_headers,
        files=files,
    )
    print(f"\n[4] Upload Document (PNG): Status {status}")
    assert status == 200
    document_id = upload_data["document_id"]
    print(f"    Document ID: {document_id}, Status: {upload_data.get('status')}")
    assert upload_data["status"] == "UPLOADED"

    # 5. Check GET Result before processing
    status, pre_res = request(
        "GET",
        f"/api/verification/documents/{document_id}/result",
        headers=u1_headers,
    )
    print(f"\n[5] GET Result before processing: Status {status}")
    print(f"    Status: {pre_res.get('status')}, Extracted Text: {pre_res.get('extracted_text')}")
    assert status == 200 and pre_res.get("status") == "NOT_PROCESSED"

    # 6. Process Document (OCR)
    status, proc_res = request(
        "POST",
        f"/api/verification/documents/{document_id}/process",
        headers=u1_headers,
    )
    print(f"\n[6] Process Document (POST /documents/{document_id}/process): Status {status}")
    print(f"    Returned Document Result:")
    print(json.dumps(proc_res, indent=4, default=str))
    assert status == 200
    assert proc_res["status"] == "COMPLETED"
    assert proc_res["extracted_text"] is not None
    assert "JOHNATHAN" in proc_res["extracted_text"].upper() or "DOE" in proc_res["extracted_text"].upper()
    assert "TRN-9876-5432-10" in proc_res["extracted_text"]

    # 7. GET Result after processing (Persistence)
    status, get_res = request(
        "GET",
        f"/api/verification/documents/{document_id}/result",
        headers=u1_headers,
    )
    print(f"\n[7] GET Result after processing: Status {status}")
    assert status == 200
    assert get_res["status"] == "COMPLETED"
    assert get_res["extracted_text"] == proc_res["extracted_text"]
    print("    Result persistence confirmed.")

    # 8. Duplicate processing
    status, dup_res = request(
        "POST",
        f"/api/verification/documents/{document_id}/process",
        headers=u1_headers,
    )
    print(f"\n[8] Duplicate Processing Request: Status {status}")
    assert status == 200
    assert dup_res["status"] == "COMPLETED"
    assert dup_res["document_id"] == document_id
    print("    Duplicate request handled idempotently.")

    # 9. Unauthorized access tests
    print("\n[9] Unauthorized Access Tests:")
    status, _ = request("GET", f"/api/verification/documents/{document_id}/result")
    print(f"    GET /result without auth header: Status {status} (Expected 401)")
    assert status == 401

    status, _ = request("POST", f"/api/verification/documents/{document_id}/process")
    print(f"    POST /process without auth header: Status {status} (Expected 401)")
    assert status == 401

    # 10. Cross-user access tests
    print("\n[10] Cross-User Access Tests (User 2 on User 1 data):")
    u2_username = f"tester_{uuid.uuid4().hex[:6]}"
    u2_password = "SecurePassword456!"
    request("POST", "/api/users", {"username": u2_username, "password": u2_password, "role": "operator"})
    _, u2_auth = request("POST", "/api/auth/login", {"username": u2_username, "password": u2_password})
    u2_headers = {"Authorization": f"Bearer {u2_auth['access_token']}"}

    status, res = request("GET", f"/api/verification/documents/{document_id}/result", headers=u2_headers)
    print(f"    User 2 GET User 1 document result: Status {status}, Detail: {res.get('detail')}")
    assert status == 404

    status, res = request("POST", f"/api/verification/documents/{document_id}/process", headers=u2_headers)
    print(f"    User 2 POST User 1 document process: Status {status}, Detail: {res.get('detail')}")
    assert status == 404

    status, res = request("POST", f"/api/verification/sessions/{session_id}/document", headers=u2_headers, files=files)
    print(f"    User 2 upload to User 1 session: Status {status}, Detail: {res.get('detail')}")
    assert status == 404

    print("\n==================================================")
    print("   ALL RUNTIME VERIFICATION TESTS PASSED (10/10)   ")
    print("==================================================")


if __name__ == "__main__":
    run_tests()
