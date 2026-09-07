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


def create_id_card():
    font = get_font(22)
    img = Image.new("RGB", (900, 580), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Standard document photo ROI (x: 36..252, y: 104..377)
    draw.rectangle([(36, 104), (252, 377)], fill=(235, 190, 155), outline=(0, 0, 0))
    draw.ellipse([(70, 140), (220, 340)], fill=(40, 40, 40))

    # Border & Text details
    draw.rectangle([(10, 10), (890, 570)], outline=(0, 0, 0), width=3)
    draw.text((300, 60), "NATIONAL IDENTITY CARD", fill=(0, 0, 0), font=font)
    draw.text((300, 130), "NAME: RAJESH SHARMA", fill=(0, 0, 0), font=font)
    draw.text((300, 200), "DOC NO: TRN-5566-7788-99", fill=(0, 0, 0), font=font)
    draw.text((300, 270), "DOB: 12/05/1988", fill=(0, 0, 0), font=font)
    draw.text((300, 340), "NATIONALITY: INDIAN", fill=(0, 0, 0), font=font)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_selfie_image():
    # Matching selfie frame
    img = Image.new("RGB", (300, 300), color=(235, 190, 155))
    draw = ImageDraw.Draw(img)
    draw.ellipse([(60, 40), (240, 260)], fill=(40, 40, 40))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def run_e2e_tests():
    print("==================================================")
    print("  TRINETRA END-TO-END VERIFICATION RUNTIME SUITE  ")
    print("==================================================")

    # 1. Health check
    status, body = request("GET", "/api/health")
    assert status == 200 and body["status"] == "ok"
    print("\n[1] Backend & MongoDB Health: OK")

    # 2. Register & Login
    username = f"officer_{uuid.uuid4().hex[:6]}"
    password = "SuperSecretPassword123!"
    status, u_res = request("POST", "/api/users", {"username": username, "password": password, "role": "verifier"})
    assert status == 200
    print(f"\n[2] User Registered: {username} ({u_res['user_id']})")

    status, login_res = request("POST", "/api/auth/login", {"username": username, "password": password})
    assert status == 200
    assert "access_token" in login_res
    assert login_res["user"]["username"] == username
    token = login_res["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"    Login Successful: Access Token Issued & User Object Present")

    # 3. Verify /me
    status, me_res = request("GET", "/api/protected/me", headers=headers)
    assert status == 200
    assert me_res["user"]["username"] == username
    print(f"\n[3] Authenticated Profile (GET /protected/me): OK")

    # 4. Create Session
    status, session = request("POST", "/api/verification/sessions", {"subject_name": "Rajesh Sharma", "document_type": "national_id"}, headers=headers)
    assert status == 200
    session_id = session["session_id"]
    print(f"\n[4] Verification Session Created: {session_id}")

    # 5. Check Initial Session Status
    status, s_stat = request("GET", f"/api/verification/sessions/{session_id}", headers=headers)
    assert status == 200
    assert s_stat["current_step"] == "AWAITING_DOCUMENT"
    assert s_stat["progress"] == 10
    print(f"\n[5] Initial Session Status Polled: {s_stat['status']} (Step: {s_stat['current_step']}, Progress: {s_stat['progress']}%)")

    # 6. Upload ID Document
    doc_bytes = create_id_card()
    files = {"file": ("id_card.png", doc_bytes, "image/png")}
    status, doc_upload = request("POST", f"/api/verification/sessions/{session_id}/document", headers=headers, files=files)
    assert status == 200
    document_id = doc_upload["document_id"]
    print(f"\n[6] Document Uploaded: {document_id}")

    # 7. Process Document (OCR + Structured Extraction)
    status, proc_res = request("POST", f"/api/verification/documents/{document_id}/process", headers=headers)
    assert status == 200
    assert proc_res["status"] == "COMPLETED"
    assert proc_res["extracted_name"] == "RAJESH SHARMA"
    assert "TRN-5566-7788-99" in proc_res["extracted_document_number"]
    print(f"\n[7] Document Processed (OCR & Extraction): Extracted Name: '{proc_res['extracted_name']}', Doc No: '{proc_res['extracted_document_number']}'")

    # 8. Upload Biometric (Selfie)
    selfie_bytes = create_selfie_image()
    files_bio = {"file": ("selfie.jpg", selfie_bytes, "image/jpeg")}
    status, bio_upload = request("POST", f"/api/verification/sessions/{session_id}/biometric", headers=headers, files=files_bio)
    assert status == 200
    biometric_id = bio_upload["biometric_id"]
    print(f"\n[8] Biometric Selfie Uploaded: {biometric_id}")

    # 9. Check Pre-Verification Status
    status, s_stat2 = request("GET", f"/api/verification/sessions/{session_id}", headers=headers)
    assert status == 200
    assert s_stat2["status"] == "BIOMETRIC_UPLOADED"
    assert s_stat2["current_step"] == "READY_FOR_VERIFICATION"
    print(f"\n[9] Ready-For-Verification Status Polled: {s_stat2['status']} (Step: {s_stat2['current_step']}, Progress: {s_stat2['progress']}%)")

    # 10. Run Full Verification Pipeline (POST /verify)
    status, verify_res = request("POST", f"/api/verification/sessions/{session_id}/verify", headers=headers)
    assert status == 200
    assert verify_res["status"] == "COMPLETED"
    print(f"\n[10] Full Verification Pipeline Executed:")
    print(json.dumps(verify_res, indent=2))

    # Assertions on all subsystem blocks
    assert verify_res["identity"]["name"] == "RAJESH SHARMA"
    assert verify_res["document"]["processed"] is True
    assert isinstance(verify_res["document"]["is_mock"], bool)
    assert verify_res["biometric"]["face_detected"] is True
    assert verify_res["face_match"]["match_status"] == "MATCHED"
    assert verify_res["liveness"]["is_live"] is True
    assert verify_res["deepfake"]["deepfake_detected"] is False
    assert verify_res["risk"]["decision"] in {"CLEAR_ENTRY", "SECONDARY_SCAN", "DETAIN_ESCALATE"}
    assert verify_res["risk"]["risk_score"] < 40
    assert verify_res["risk"]["decision"] == "CLEAR_ENTRY"
    assert verify_res["risk"]["risk_level"] == "LOW"
    print("    All 7 subsystem blocks verified (Identity, Document, Biometric, Face Match, Liveness, Deepfake, Risk)")

    # 11. Retrieve Unified Result via GET /result
    status, final_res = request("GET", f"/api/verification/sessions/{session_id}/result", headers=headers)
    assert status == 200
    assert final_res["session_id"] == session_id
    assert final_res["risk"]["decision"] == "CLEAR_ENTRY"
    print(f"\n[11] Unified Final Result (GET /sessions/{session_id}/result): Verified")

    # 12. Check Completed Session Status
    status, s_stat3 = request("GET", f"/api/verification/sessions/{session_id}", headers=headers)
    assert status == 200
    assert s_stat3["status"] == "COMPLETED"
    assert s_stat3["progress"] == 100
    print(f"\n[12] Final Session Status Polled: {s_stat3['status']} (Progress: {s_stat3['progress']}%)")

    # 13. Idempotent Repeated Verification Request
    status, dup_verify = request("POST", f"/api/verification/sessions/{session_id}/verify", headers=headers)
    assert status == 200
    assert dup_verify["session_id"] == session_id
    print(f"\n[13] Idempotent Verification Call: Handled cleanly without duplicate errors")

    # 14. Cross-User Security Isolation
    other_user = f"attacker_{uuid.uuid4().hex[:6]}"
    request("POST", "/api/users", {"username": other_user, "password": password, "role": "operator"})
    _, other_auth = request("POST", "/api/auth/login", {"username": other_user, "password": password})
    other_headers = {"Authorization": f"Bearer {other_auth['access_token']}"}

    status, _ = request("GET", f"/api/verification/sessions/{session_id}", headers=other_headers)
    assert status == 404
    status, _ = request("GET", f"/api/verification/sessions/{session_id}/result", headers=other_headers)
    assert status == 404
    status, _ = request("POST", f"/api/verification/sessions/{session_id}/verify", headers=other_headers)
    assert status == 404
    print(f"\n[14] Cross-User Access Isolation: Denied with 404 Not Found (User isolation confirmed)")

    print("\n==================================================")
    print("  ALL END-TO-END RUNTIME VERIFICATION TESTS PASSED")
    print("==================================================")


if __name__ == "__main__":
    run_e2e_tests()
