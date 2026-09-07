import io
import json
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

BASE_URL = "http://127.0.0.1:8000"


def get_font(size=22):
    for p in [Path(r"C:\Windows\Fonts\arial.ttf"), Path(r"C:\Windows\Fonts\consola.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]:
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                pass
    return ImageFont.load_default()


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


def create_full_document_image():
    font = get_font(22)
    img = Image.new("RGB", (900, 520), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(10, 10), (890, 510)], outline=(0, 0, 0), width=3)
    draw.text((30, 25), "PASSPORT OF ATLANTIS", fill=(0, 0, 0), font=font)
    draw.text((30, 75), "NAME: ALICE SMITH", fill=(0, 0, 0), font=font)
    draw.text((30, 125), "PASS NO: P12345678", fill=(0, 0, 0), font=font)
    draw.text((30, 175), "DOB: 24/11/1992", fill=(0, 0, 0), font=font)
    draw.text((30, 225), "DOI: 10/01/2020", fill=(0, 0, 0), font=font)
    draw.text((30, 275), "DOE: 09/01/2030", fill=(0, 0, 0), font=font)
    draw.text((30, 325), "GENDER: FEMALE", fill=(0, 0, 0), font=font)
    draw.text((30, 375), "NATIONALITY: ATLANTIS", fill=(0, 0, 0), font=font)
    draw.text((30, 425), "ADDRESS: 42 Ocean Ave, Coral City", fill=(0, 0, 0), font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_minimal_document_image():
    font = get_font(22)
    img = Image.new("RGB", (700, 220), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(10, 10), (690, 210)], outline=(0, 0, 0), width=2)
    draw.text((30, 30), "NATIONAL ID CARD", fill=(0, 0, 0), font=font)
    draw.text((30, 85), "NAME: ROBERT ROE", fill=(0, 0, 0), font=font)
    draw.text((30, 140), "DOC NO: TRN-1122-3344-55", fill=(0, 0, 0), font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def run_phase9_tests():
    print("==================================================")
    print("      RUNNING PHASE 9 RUNTIME TEST SUITE          ")
    print("==================================================")

    # 1. Health check
    status, body = request("GET", "/api/health")
    assert status == 200 and body["status"] == "ok" and body["database"] == "connected"
    print("\n[1] Health Check: OK")

    # 2. Duplicate Username Hardening Test (Section 10)
    u_base = f"user_{uuid.uuid4().hex[:6]}"
    status, res = request("POST", "/api/users", {"username": u_base, "password": "Password123!", "role": "operator"})
    assert status == 200, f"User creation failed: {res}"
    # Attempt to create identical username
    status, dup_res = request("POST", "/api/users", {"username": u_base, "password": "Password123!", "role": "operator"})
    print(f"\n[2] User Hardening Test (Duplicate Registration): Status {status}, Detail: {dup_res.get('detail')}")
    assert status == 409, f"Expected 409 Conflict on duplicate username, got {status}"

    # 3. Authenticate User
    status, auth = request("POST", "/api/auth/login", {"username": u_base, "password": "Password123!"})
    assert status == 200
    token = auth["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"\n[3] Authenticate User: Success (JWT obtained)")

    # 4. Create Session and Process Full Document (All Fields Present)
    status, s1 = request("POST", "/api/verification/sessions", {"subject_name": "Alice Smith", "document_type": "passport"}, headers=headers)
    assert status == 200
    session_id1 = s1["session_id"]

    full_png = create_full_document_image()
    status, up1 = request("POST", f"/api/verification/sessions/{session_id1}/document", headers=headers, files={"file": ("passport.png", full_png, "image/png")})
    assert status == 200
    doc_id1 = up1["document_id"]
    print(f"\n[4] Full Document Uploaded: Document ID {doc_id1}")

    # Process Document
    status, proc1 = request("POST", f"/api/verification/documents/{doc_id1}/process", headers=headers)
    assert status == 200
    print(f"\n[5] Full Document Processed (POST /process):")
    print(json.dumps(proc1, indent=2))

    # Assertions on extraction
    assert proc1["status"] == "COMPLETED"
    assert proc1["extracted_text"] is not None
    assert proc1["extracted_name"] == "ALICE SMITH"
    assert "P12345678" in proc1["extracted_document_number"]
    assert proc1["extracted_document_type"] == "passport"
    assert proc1["date_of_birth"] == "24/11/1992"
    assert proc1["date_of_issue"] == "10/01/2020"
    assert proc1["date_of_expiry"] == "09/01/2030"
    assert proc1["gender"] == "FEMALE"
    assert proc1["nationality"] == "ATLANTIS"
    assert proc1["address"] is not None and "42 Ocean Ave" in proc1["address"]
    assert "name" in proc1["field_confidence"]
    assert "document_number" in proc1["field_confidence"]
    assert proc1["ocr_confidence"] is not None and proc1["ocr_confidence"] > 0.8
    print("    All 9 structured identity fields verified successfully!")

    # 5. Verify Persistence via GET /result
    status, get1 = request("GET", f"/api/verification/documents/{doc_id1}/result", headers=headers)
    assert status == 200
    assert get1["status"] == "COMPLETED"
    assert get1["extracted_name"] == proc1["extracted_name"]
    assert get1["extracted_document_number"] == proc1["extracted_document_number"]
    assert get1["date_of_birth"] == proc1["date_of_birth"]
    assert get1["date_of_issue"] == proc1["date_of_issue"]
    assert get1["date_of_expiry"] == proc1["date_of_expiry"]
    assert get1["field_confidence"] == proc1["field_confidence"]
    print("\n[6] Result Persistence Verified via GET /result")

    # 6. Test Minimal Document (Verify Missing Fields Remain Null)
    status, s2 = request("POST", "/api/verification/sessions", {"subject_name": "Robert Roe", "document_type": "national_id"}, headers=headers)
    assert status == 200
    session_id2 = s2["session_id"]

    min_png = create_minimal_document_image()
    status, up2 = request("POST", f"/api/verification/sessions/{session_id2}/document", headers=headers, files={"file": ("min_id.png", min_png, "image/png")})
    assert status == 200
    doc_id2 = up2["document_id"]

    status, proc2 = request("POST", f"/api/verification/documents/{doc_id2}/process", headers=headers)
    assert status == 200
    print(f"\n[7] Minimal Document Processed (Missing fields verification):")
    print(f"    Name: {proc2.get('extracted_name')}")
    print(f"    Document Number: {proc2.get('extracted_document_number')}")
    print(f"    Document Type: {proc2.get('extracted_document_type')}")
    print(f"    DOB: {proc2.get('date_of_birth')}")
    print(f"    DOI: {proc2.get('date_of_issue')}")
    print(f"    DOE: {proc2.get('date_of_expiry')}")
    print(f"    Nationality: {proc2.get('nationality')}")
    print(f"    Gender: {proc2.get('gender')}")
    print(f"    Address: {proc2.get('address')}")

    assert proc2["extracted_name"] == "ROBERT ROE"
    assert "TRN-1122-3344-55" in proc2["extracted_document_number"]
    assert proc2["extracted_document_type"] == "national_id"
    # Verify missing fields are strictly None
    assert proc2["date_of_birth"] is None
    assert proc2["date_of_issue"] is None
    assert proc2["date_of_expiry"] is None
    assert proc2["nationality"] is None
    assert proc2["gender"] is None
    assert proc2["address"] is None
    print("    Missing fields confirmed as strictly null/None!")

    # 7. Idempotency Test
    status, dup_proc = request("POST", f"/api/verification/documents/{doc_id2}/process", headers=headers)
    assert status == 200
    assert dup_proc["extracted_document_number"] == proc2["extracted_document_number"]
    assert dup_proc["extracted_name"] == proc2["extracted_name"]
    print("\n[8] Idempotent Duplicate Processing Verified: OK")

    # 8. Security / Cross-User Access Isolation
    print("\n[9] Security & Cross-User Isolation Verification:")
    # Unauthorized request
    status, _ = request("GET", f"/api/verification/documents/{doc_id1}/result")
    assert status == 401
    print("    Unauthorized GET /result -> 401 Unauthorized (OK)")

    # User 2 request on User 1's doc
    u2 = f"user_{uuid.uuid4().hex[:6]}"
    request("POST", "/api/users", {"username": u2, "password": "Password123!", "role": "operator"})
    _, auth2 = request("POST", "/api/auth/login", {"username": u2, "password": "Password123!"})
    headers2 = {"Authorization": f"Bearer {auth2['access_token']}"}

    status, res2 = request("GET", f"/api/verification/documents/{doc_id1}/result", headers=headers2)
    assert status == 404
    print("    User 2 GET User 1 /result -> 404 Not Found (OK)")

    status, res2_proc = request("POST", f"/api/verification/documents/{doc_id1}/process", headers=headers2)
    assert status == 404
    print("    User 2 POST User 1 /process -> 404 Not Found (OK)")

    print("\n==================================================")
    print("            PHASE 9 TESTS PASSED                  ")
    print("==================================================")


if __name__ == "__main__":
    run_phase9_tests()
