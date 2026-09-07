import io
import sys
from pathlib import Path
from PIL import Image, ImageDraw

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.services.ai_biometrics_service import compare_faces, evaluate_liveness, load_image_cv
from app.services.forensics_service import perform_error_level_analysis
from app.utils.mrz_parser import calculate_icao_checksum, find_mrz_in_text, parse_td3_passport, verify_checksum


def test_mrz_checksums():
    print("\n[+] Testing Module 2: ICAO Doc 9303 Checksum Calculation...")
    test_doc_num = "L898902C3"
    expected_check = "6"
    is_valid = verify_checksum(test_doc_num, expected_check)
    assert is_valid
    print("    Checksum Validation: [PASSED]")


def test_td3_passport_parser():
    print("\n[+] Testing Module 1 & 2: TD3 Passport MRZ Parsing...")
    line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
    line2 = "L898902C36UTO7408122F2604158ZE184226B<<<<<10"
    parsed = parse_td3_passport(line1, line2)
    assert parsed["surname"] == "ERIKSSON"
    assert parsed["given_names"] == "ANNA MARIA"
    assert parsed["document_number"] == "L898902C3"
    assert parsed["checksums"]["overall_mrz_valid"] is True
    print(f"    Passenger: {parsed['given_names']} {parsed['surname']}")
    print(f"    Document: {parsed['document_number']} ({parsed['nationality']})")
    print("    TD3 MRZ Parsing: [PASSED]")

    # Test full text extraction finder
    full_text = f"PASSPORT OF UTOPIA\n{line1}\n{line2}\nSOME OTHER TEXT"
    found = find_mrz_in_text(full_text)
    assert found is not None
    assert found["document_number"] == "L898902C3"
    print("    MRZ Text Finder: [PASSED]")


def test_forensics():
    print("\n[+] Testing Module 3: Error Level Analysis (Forensics)...")
    img = Image.new("RGB", (200, 200), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)

    res = perform_error_level_analysis(buf.getvalue())
    assert res["is_suspicious"] is False
    assert res["verdict"] == "CLEAN_COMPRESSION"
    print(f"    Forensic Verdict: {res['verdict']} (Score: {res['tamper_risk_score']})")
    print("    ELA Forensics: [PASSED]")


def test_biometrics():
    print("\n[+] Testing Module 4: 1:1 Biometric Face Verification...")
    # Generate test face buffers
    f1 = Image.new("RGB", (160, 160), color=(235, 190, 155))
    d1 = ImageDraw.Draw(f1)
    d1.ellipse([50, 40, 110, 100], fill=(40, 40, 40))
    b1 = io.BytesIO()
    f1.save(b1, format="JPEG")

    # Matching face (same subject, minor shift)
    f2 = Image.new("RGB", (160, 160), color=(235, 190, 155))
    d2 = ImageDraw.Draw(f2)
    d2.ellipse([50, 40, 110, 100], fill=(40, 40, 40))
    b2 = io.BytesIO()
    f2.save(b2, format="JPEG")

    # Impostor face (distinctly different colors and geometry)
    f3 = Image.new("RGB", (160, 160), color=(40, 130, 70))
    d3 = ImageDraw.Draw(f3)
    d3.ellipse([30, 20, 130, 120], fill=(200, 200, 200))
    b3 = io.BytesIO()
    f3.save(b3, format="JPEG")

    match_res = compare_faces(b1.getvalue(), b2.getvalue())
    impostor_res = compare_faces(b1.getvalue(), b3.getvalue())

    print(f"    Same Person Match: {match_res['similarity_percentage']}% (Verdict: {match_res['match_verdict']})")
    print(f"    Impostor Match: {impostor_res['similarity_percentage']}% (Verdict: {match_res['match_verdict']})")

    assert match_res["verified"] is True
    assert impostor_res["verified"] is False
    print("    Biometrics Module: [PASSED]")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING TRINETRA SUPPLIED AI ALGORITHMIC TEST SUITE")
    print("=" * 60)
    test_mrz_checksums()
    test_td3_passport_parser()
    test_forensics()
    test_biometrics()
    print("\n" + "=" * 60)
    print("ALL SUPPLIED AI MODULES TESTED & PASSED SUCCESSFULLY!")
    print("=" * 60)
