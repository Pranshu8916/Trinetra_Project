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


def get_font(size=20):
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


def create_matching_selfie():
    # Matches the simulated photo area color and geometry
    img = Image.new("RGB", (300, 300), color=(235, 190, 155))
    draw = ImageDraw.Draw(img)
    draw.ellipse([(60, 40), (240, 260)], fill=(40, 40, 40))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def run_real_ai_tests():
    print("==================================================")
    print("  TRINETRA REAL AI PROVIDER RUNTIME TEST SUITE   ")
    print("==================================================")

    # 1. Health
    status, health = request("GET", "/api/health")
    assert status == 200 and health["status"] == "ok"
    print("\n[1] Backend & MongoDB Health: OK")

    # 2. Register & Login
    username = f"agent_{uuid.uuid4().hex[:6]}"
    password = "SecurePassword123!"
    request("POST", "/api/users", {"username": username, "password": password, "role": "verifier"})
    _, login = request("POST", "/api/auth/login", {"username": username, "password": password})
    token = login["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"\n[2] User Registered & Authenticated: {username}")

    # 3. Create Session
    _, session = request("POST", "/api/verification/sessions", {"subject_name": "Rajesh Sharma", "document_type": "national_id"}, headers=headers)
    session_id = session["session_id"]
    print(f"\n[3] Verification Session Created: {session_id}")

    # 4. Upload Document
    doc_bytes = create_id_card()
    files = {"file": ("id_card.png", doc_bytes, "image/png")}
    _, doc_upload = request("POST", f"/api/verification/sessions/{session_id}/document", headers=headers, files=files)
    document_id = doc_upload["document_id"]
    print(f"\n[4] Document Uploaded: {document_id}")

    # 5. Process Document (OCR + Extraction)
    status, proc_res = request("POST", f"/api/verification/documents/{document_id}/process", headers=headers)
    assert status == 200
    assert proc_res["extracted_name"] == "RAJESH SHARMA"
    assert "TRN-5566-7788-99" in proc_res["extracted_document_number"]
    print(f"\n[5] Document OCR & Extraction Complete: '{proc_res['extracted_name']}', '{proc_res['extracted_document_number']}'")

    # 6. Upload Selfie
    selfie_bytes = create_matching_selfie()
    files_bio = {"file": ("selfie.jpg", selfie_bytes, "image/jpeg")}
    _, bio_upload = request("POST", f"/api/verification/sessions/{session_id}/biometric", headers=headers, files=files_bio)
    print(f"\n[6] Biometric Selfie Uploaded: {bio_upload['biometric_id']}")

    # 7. Execute Verification Pipeline (POST /verify)
    status, verify_res = request("POST", f"/api/verification/sessions/{session_id}/verify", headers=headers)
    assert status == 200
    print("\n[7] Full Verification Pipeline Executed:")
    print(json.dumps(verify_res, indent=2))

    # Assertions for REAL PROVIDER outputs (not mock!)
    assert verify_res["document"]["is_mock"] is False
    assert verify_res["document"]["provider"] == "supplied_ela_forensics"
    assert verify_res["document"]["tampering_detected"] is False

    assert verify_res["biometric"]["is_mock"] is False
    assert verify_res["biometric"]["provider"] == "supplied_face_analysis"
    assert verify_res["biometric"]["face_detected"] is True

    assert verify_res["face_match"]["is_mock"] is False
    assert verify_res["face_match"]["provider"] == "supplied_joint_color_structure"
    assert verify_res["face_match"]["match_status"] == "MATCHED"

    assert verify_res["liveness"]["is_mock"] is False
    assert verify_res["liveness"]["provider"] == "supplied_passive_liveness"
    assert verify_res["liveness"]["is_live"] is True

    assert verify_res["deepfake"]["is_mock"] is False
    assert verify_res["deepfake"]["provider"] == "supplied_frequency_analysis"
    assert verify_res["deepfake"]["deepfake_detected"] is False

    assert verify_res["risk"]["is_mock"] is False
    assert verify_res["risk"]["decision"] == "CLEAR_ENTRY"
    assert verify_res["risk"]["risk_score"] < 40

    print("    All 5 real AI providers verified with is_mock=False!")

    # 8. Retrieve Final Result via GET /result
    status, final_res = request("GET", f"/api/verification/sessions/{session_id}/result", headers=headers)
    assert status == 200
    assert final_res["risk"]["decision"] == "CLEAR_ENTRY"
    assert final_res["document"]["provider"] == "supplied_ela_forensics"
    print("\n[8] GET /result Verified with Persistent Real AI Data")

    # 9. Security Cross-User Isolation Check
    hacker_name = f"hacker_{uuid.uuid4().hex[:6]}"
    request("POST", "/api/users", {"username": hacker_name, "password": password, "role": "operator"})
    _, h_login = request("POST", "/api/auth/login", {"username": hacker_name, "password": password})
    h_headers = {"Authorization": f"Bearer {h_login['access_token']}"}

    status, _ = request("GET", f"/api/verification/sessions/{session_id}/result", headers=h_headers)
    assert status == 404
    status, _ = request("POST", f"/api/verification/sessions/{session_id}/verify", headers=h_headers)
    assert status == 404
    print("\n[9] Cross-User Security Check: 404 Confirmed")

    # 10. Real AI Impostor / Fraud Detection Check
    print("\n[10] Testing Real AI on Impostor Face...")
    _, imp_session = request("POST", "/api/verification/sessions", {"subject_name": "Rajesh Sharma", "document_type": "national_id"}, headers=headers)
    imp_sid = imp_session["session_id"]
    _, imp_doc = request("POST", f"/api/verification/sessions/{imp_sid}/document", headers=headers, files=files)
    request("POST", f"/api/verification/documents/{imp_doc['document_id']}/process", headers=headers)

    # Distinctly different impostor face (greenish hues & different geometry)
    imp_img = Image.new("RGB", (300, 300), color=(40, 130, 70))
    d_imp = ImageDraw.Draw(imp_img)
    d_imp.ellipse([(30, 20), (130, 120)], fill=(200, 200, 200))
    b_imp = io.BytesIO()
    imp_img.save(b_imp, format="JPEG")
    imp_files = {"file": ("impostor.jpg", b_imp.getvalue(), "image/jpeg")}
    request("POST", f"/api/verification/sessions/{imp_sid}/biometric", headers=headers, files=imp_files)

    status, imp_verify = request("POST", f"/api/verification/sessions/{imp_sid}/verify", headers=headers)
    assert status == 200
    assert imp_verify["face_match"]["match_status"] in {"NOT_MATCHED", "MANUAL_REVIEW"}
    assert imp_verify["risk"]["risk_score"] >= 40
    assert imp_verify["risk"]["decision"] in {"SECONDARY_SCAN", "DETAIN_ESCALATE"}
    print(f"    Impostor Result: Match Status = '{imp_verify['face_match']['match_status']}', Risk Score = {imp_verify['risk']['risk_score']} ({imp_verify['risk']['decision']})")
    print("    Real AI correctly identified mismatch and elevated risk!")

    print("\n==================================================")
    print("  ALL REAL AI PROVIDER RUNTIME TESTS PASSED!      ")
    print("==================================================")


if __name__ == "__main__":
    run_real_ai_tests()
