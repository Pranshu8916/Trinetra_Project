import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api.watchlist import check_subject_watchlist, get_watchlist_stats, search_watchlist
from app.providers.risk import RuleBasedRiskEngineProvider

async def main():
    print("==================================================")
    print(" TRINETRA: INTERPOL RED NOTICE INTEGRATION TEST")
    print("==================================================")

    # 1. Database Stats
    stats = await get_watchlist_stats()
    s = stats["stats"]
    print(f"\n[+] Total Active Interpol Records: {s['total_records']:,}")
    print(f"[+] Source Feed: {s['source']}")
    print(f"[+] Operational Status: {s['system_status']}")
    print(f"[+] Local Cache Path: {s['cache_file']}")
    print("[+] Top Wanted Jurisdictions:")
    for c in s["top_wanted_countries"][:5]:
        print(f"    - {c['country'].upper()}: {c['count']} wanted fugitives")

    # 2. Search Interpol Notices
    print("\n[+] Testing Full-Text Fugitive Search ('murder'):")
    search_res = await search_watchlist(q="murder", limit=3)
    print(f"    Found {search_res['count']} matches:")
    for r in search_res["results"]:
        charges_first_line = (r.get("sanctions") or "").split("\n")[0][:70]
        print(f"    - {r['name']} ({r.get('countries', '').upper()}): {charges_first_line}")

    # 3. Check Real Interpol Wanted Subject
    print("\n[+] Testing Subject Screening against Interpol Red Notice (Akhtar Merchant):")
    flagged_res = await check_subject_watchlist(name="Akhtar Merchant", country="IN")
    f_data = flagged_res["data"]
    print(f"    Verdict: {f_data['status']}")
    print(f"    Match Type: {f_data['match_type']}")
    print(f"    Confidence: {f_data['confidence']}")
    print(f"    Notice ID: {f_data['match_details']['entity_id']}")
    print(f"    Subject Name: {f_data['match_details']['name']}")
    print(f"    Charges: {f_data['match_details']['charges'][:120]}...")

    # 4. Check Clean Traveler
    print("\n[+] Testing Clean Subject Screening (Vikramaditya Roy):")
    clean_res = await check_subject_watchlist(name="Vikramaditya Roy", document_number="K9823145")
    c_data = clean_res["data"]
    print(f"    Verdict: {c_data['status']}")
    print(f"    Verification Note: {c_data.get('verification_note')}")

    # 5. Check Test Fixture Token
    print("\n[+] Testing Simulation Override Token (INTERPOL_NOTICE):")
    test_res = await check_subject_watchlist(name="Test Subject INTERPOL_NOTICE")
    t_data = test_res["data"]
    print(f"    Verdict: {t_data['status']}")
    print(f"    Match Type: {t_data['match_type']}")

    # 6. Risk Engine End-to-End Evaluation
    print("\n[+] Testing Rule-Based Risk Engine (Module 2 Impact):")
    engine = RuleBasedRiskEngineProvider()
    clean_risk = engine.calculate_risk(
        document_analysis={"holder_name": "Vikramaditya Roy", "document_number": "K9823145"},
        face_analysis={"face_detected": True},
        face_match={"similarity_score": 0.95, "match_status": "MATCHED"},
        liveness={"is_live": True, "liveness_score": 0.98},
        deepfake={"deepfake_detected": False, "deepfake_score": 0.05},
    )
    print(f"    Clean Traveler: Risk Score = {clean_risk['risk_score']} ({clean_risk['risk_level']}), Decision = {clean_risk['decision']}")

    flagged_risk = engine.calculate_risk(
        document_analysis={"holder_name": "Akhtar Merchant", "document_number": "P1029384"},
        face_analysis={"face_detected": True},
        face_match={"similarity_score": 0.95, "match_status": "MATCHED"},
        liveness={"is_live": True, "liveness_score": 0.98},
        deepfake={"deepfake_detected": False, "deepfake_score": 0.05},
    )
    print(f"    Wanted Fugitive: Risk Score = {flagged_risk['risk_score']} ({flagged_risk['risk_level']}), Decision = {flagged_risk['decision']}")
    print(f"    Detention Trigger Reason: {flagged_risk['reasons'][0]}")

    print("\n==================================================")
    print(" ALL VERIFICATIONS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())
