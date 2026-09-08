# 🛡️ TRINETRA: AI-POWERED BORDER IDENTITY FORENSIC & SCREENING SYSTEM
## Complete SDE Technical Specification & Architectural Diagram Documentation
**Smart India Hackathon (SIH 2024) — Problem Statement ID: 26188**  
**Sponsoring Organization**: Ministry of Home Affairs (MHA) & Sashastra Seema Bal (SSB) — Police II Division  

---

## 1. Executive Summary

**Trinetra** is an enterprise-grade, multi-modal AI identity verification and border document forensic workstation. Developed for law enforcement and border control officers, Trinetra delivers real-time identity authentication, forensic forgery detection, facial liveness verification, security watchlist screening, and tamper-proof audit logging.

### Key System Capabilities
- **Multi-Document Structured OCR Extraction**: Supports Passports (ICAO Doc 9303), Visas (ICAO MRV & Travel Permits with stay duration/validity), Aadhaar Cards (UIDAI 12-digit with Verhoeff modulo-10 algorithm), Driving Licenses (State RTO codes), and PAN Cards.
- **Image EXIF Metadata Analysis**: Scans hidden digital camera tags for image editing signatures (*Adobe Photoshop, GIMP, Canva, modified timestamps*).
- **Border Stamp & Seal Forgery Detection**: OpenCV HSV color space segmentation and contour geometry analysis for border entry seals and stamps.
- **Facial Liveness & Deepfake Verification**: Multi-frame biometric similarity scoring and deepfake image manipulation detection.
- **Security Watchlist Engine**: Instant cross-referencing against Sashastra Seema Bal (SSB) and Interpol criminal blacklist records.
- **Cryptographic Blockchain Audit Ledger**: SHA-256 block hash generation for all screening sessions, providing immutable, court-admissible audit logs.

---

## 2. High-Level System Architecture Diagram

```mermaid
graph TD
    subgraph ClientLayer ["Client Layer (Presentation)"]
        A["Border Control Officer (Web Workstation UI)"]
        B["Next.js 14 Framework / React 18"]
        C["TailwindCSS / Lucide Icons / Recharts"]
    end

    subgraph APIGateway ["API Gateway & Controller"]
        D["FastAPI Gateway (Python 3.11 / Uvicorn)"]
        E["Multipart Router (/api/v1/screen-document)"]
    end

    subgraph ServiceModules ["Core Intelligence Engine Services"]
        F["Module 1: OCR & MRV Visa Parser"]
        G["Module 2: EXIF & Stamp Forensics"]
        H["Module 3: Face Matching & Liveness"]
        I["Module 4: Risk & Watchlist Engine"]
        J["Module 5: Blockchain Ledger Service"]
    end

    subgraph StorageLayer ["Persistence & Immutable Audit Layer"]
        K[("MongoDB Database (Session Reports)")]
        L["Cryptographic SHA-256 Audit Chain"]
    end

    A --> B
    B --> C
    B -- "HTTPS / REST API" --> D
    D --> E
    E --> F
    E --> G
    E --> H
    E --> I
    E --> J
    F --> I
    G --> I
    H --> I
    I --> J
    J --> K
    J --> L
```

---

## 3. End-to-End Processing Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Officer as Border Control Officer
    participant UI as Next.js Workstation
    participant API as FastAPI Backend (/api/v1/screen-document)
    participant OCR as OCR & MRZ Service
    participant Forensics as EXIF & Stamp Forensics Service
    participant Face as Face Verification Engine
    participant Risk as Risk & Watchlist Engine
    participant Chain as Blockchain Audit Logger
    participant DB as MongoDB Database

    Officer->>UI: Upload Identity Document & Capture Live Selfie
    UI->>API: POST /api/v1/screen-document (Multipart Form)
    API->>OCR: extract_text() + extract_document_fields()
    OCR-->>API: Extracted Fields (Name, DOB, Doc No, Visa Type, MRZ)
    API->>Forensics: analyze_image_exif_metadata() + analyze_stamp_and_seal_authenticity()
    Forensics-->>API: EXIF Forgery Flags & Stamp Authenticity Score
    API->>Face: compare_faces() + verify_liveness()
    Face-->>API: Biometric Similarity Score & Liveness Verdict
    API->>Risk: evaluate_risk() + check_watchlist()
    Risk-->>API: Risk Score (0-100), Risk Level (Low/Med/High), Watchlist Status
    API->>Chain: generate_report_block_hash()
    Chain->>DB: Save Screening Report + SHA-256 Block Hash
    DB-->>Chain: Ack Report ID & Block Hash
    Chain-->>API: Complete Audit Payload
    API-->>UI: 200 OK (JSON Assessment Contract)
    UI->>Officer: Render Decision Cards, Forensics Breakdown & Audit Badge
```

---

## 4. Module 1: Structured Multi-Document OCR & MRV Visa Parsing Workflow

```mermaid
graph TD
    Start["Raw Document Upload (Passport / Visa / Aadhaar / DL / PAN)"] --> PreProc["PIL Preprocessing (2x Rescale, Contrast 1.6x, Sharpness 1.4x)"]
    PreProc --> DetectMRZ{"MRZ Code Lines Present? (ICAO 9303 / MRV)"}
    
    DetectMRZ -- Yes --> MRZParser["Parse MRZ Format (P<, V< / VIND, TD1, TD2)"]
    MRZParser --> ParseMRZFields["Extract Doc Type, Name, Doc No, DOB, Expiry, Nationality, Stay Duration"]
    
    DetectMRZ -- No --> DualOCR["Parallel OCR Execution (EasyOCR + Pytesseract)"]
    DualOCR --> IndianIDParser["Indian ID Specific Field Extractor"]
    
    IndianIDParser --> CleanNoise["Noise Filter: Reject Relation Prefixes (S/O, D/O) & Single-Char Artifacts (Tt Tt, Aa Aa)"]
    CleanNoise --> VerhoeffCheck{"Validate Aadhaar 12-Digit Verhoeff Modulo-10 Checksum"}
    
    VerhoeffCheck -- Pass --> ValidatedOCR["Construct Clean Extracted Fields Payload"]
    VerhoeffCheck -- Fail --> FlagChecksum["Flag Checksum Mismatch Alert"]
    
    ParseMRZFields --> ValidatedOCR
    FlagChecksum --> ValidatedOCR
    ValidatedOCR --> End["Return Extracted Document Fields to Controller"]
```

---

## 5. Module 2: EXIF Metadata & Border Stamp Forgery Detection Workflow

```mermaid
graph TD
    InputImage["Document Image Input"] --> EXIFExtract["Extract Native EXIF Metadata via PIL / PyExifTool"]
    
    EXIFExtract --> SoftCheck{"Software/Editing Tags Detected? (Photoshop, GIMP, Canva)"}
    SoftCheck -- Yes --> FlagEXIF["Set EXIF Forgery Flag = TRUE (High Risk)"]
    SoftCheck -- No --> EXIFClean["EXIF Metadata Clear"]
    
    InputImage --> HSVConvert["OpenCV BGR to HSV Color Space Conversion"]
    HSVConvert --> StampColorSeg["Segment Rubber Stamp Colors (Blue, Purple, Red Ink Mask)"]
    StampColorSeg --> ContourAnalysis["Contour & Geometric Roundness/Aspect Ratio Analysis"]
    
    ContourAnalysis --> StampAuthenticity{"Stamp Structure & Edge Sharpness Valid?"}
    StampAuthenticity -- Valid --> ScoreHigh["Assign Stamp Authenticity Score (85% - 99%)"]
    StampAuthenticity -- Tampered --> ScoreLow["Assign Forgery Flag: Altered Ink Boundary / Stamp Tampered"]
    
    FlagEXIF --> ForensicsVerdict["Synthesize Digital & Physical Forensics Assessment"]
    EXIFClean --> ForensicsVerdict
    ScoreHigh --> ForensicsVerdict
    ScoreLow --> ForensicsVerdict
```

---

## 6. Module 3: Biometric Face Matching & Deepfake Verification Workflow

```mermaid
graph TD
    InputFaces["Document Crop Face + Live Webcam Selfie Frame"] --> FaceDetect["OpenCV Haar / MTCNN Face Detection & Alignment"]
    
    FaceDetect --> EmbExtract["Extract 128-d Biometric Face Embeddings (ResNet/dlib/DeepFace)"]
    EmbExtract --> CosineSim["Compute Cosine Distance & Euclidean Similarity Metric"]
    
    CosineSim --> MatchCheck{"Biometric Similarity Score >= Threshold (0.60)"}
    MatchCheck -- Match --> MatchPass["Biometric Face Match Verified ✓"]
    MatchCheck -- Mismatch --> MatchFail["Impostor / Identity Mismatch Warning ❌"]
    
    InputFaces --> TextureAnalysis["Liveness Engine: Texture Laplacian Variance & Reflection Analysis"]
    TextureAnalysis --> LivenessCheck{"Spoof / Deepfake Attack Detected?"}
    LivenessCheck -- Real --> LivePass["Liveness Verified (Human Subject Present)"]
    LivenessCheck -- Spoof --> LiveFail["Spoof Alert: Photo Print, Screen Replay, or Deepfake"]
    
    MatchPass --> BiometricSummary["Biometric Assessment Summary"]
    MatchFail --> BiometricSummary
    LivePass --> BiometricSummary
    LiveFail --> BiometricSummary
```

---

## 7. Module 4: Security Watchlist & Blacklist Search Engine Workflow

```mermaid
graph TD
    ExtractedID["Extracted Subject Name, DOB, Passport / Doc No, Nationality"] --> Normalize["Standardize Text & Transliterate Characters"]
    
    Normalize --> ExactMatch{"Exact Doc Number Match in Watchlist DB?"}
    ExactMatch -- Match Found --> HitCritical["CRITICAL HIT: Red Notice / SSB Blacklisted Criminal"]
    
    ExactMatch -- No Direct Match --> FuzzySearch["Execute Jaro-Winkler & Levenshtein Fuzzy Name Matching"]
    FuzzySearch --> SimilarityScore{"Name Match Score >= 85% & Matching DOB/Nationality?"}
    
    SimilarityScore -- High Similarity --> HitAlert["SUSPECT HIT: Person of Interest / Interpol Watchlist Alert"]
    SimilarityScore -- Low Similarity --> ClearWatchlist["Watchlist Verdict: CLEAR ✓ (No Record Match)"]
    
    HitCritical --> RiskEval["Calculate Risk Score (0 - 100) & Assign Risk Level"]
    HitAlert --> RiskEval
    ClearWatchlist --> RiskEval
    
    RiskEval --> RiskVerdict["Final Risk Category: Low (0-20), Medium (21-60), High 61-100)"]
```

> **Live Implementation Reference**: For detailed technical endpoints, Interpol dataset schemas, and border post SOPs, refer to the [Interpol & SSB Watchlist Specification](file:///c:/Users/ASUS/OneDrive/Desktop/SIH/Trinetra/Documentation_and_PDFs/interpol_integration_specification.md).

---

## 8. Module 5: Cryptographic SHA-256 Blockchain Audit Ledger Workflow

```mermaid
graph TD
    ScreeningData["Complete Assessment Payload (Extracted Fields, Scores, Verdicts)"] --> CanonicalJSON["Format Canonical Compact JSON Representation"]
    
    CanonicalJSON --> HashGen["Generate Cryptographic SHA-256 Payload Hash"]
    HashGen --> GetPrevHash["Fetch Previous Block Hash from Immutable Chain Ledger"]
    
    GetPrevHash --> BuildBlock["Construct New Audit Block Header: {Index, Timestamp, PayloadHash, PrevHash, Nonce}"]
    BuildBlock --> MineBlock["PoW / SHA-256 Block Seal Verification"]
    
    MineBlock --> CommitDB["Commit Immutable Audit Block to MongoDB Collection"]
    CommitDB --> GenerateReceipt["Return Audit Verification Badge & Block Hash to Officer UI"]
```

---

## 9. Component & Class Architecture Diagram

```mermaid
classDiagram
    class ScreeningController {
        +screen_document(passport_img, selfie_img) JSON
        +get_audit_log(session_id) JSON
    }

    class DocumentExtractionService {
        +extract_all_fields(image_bytes) Dict
        -determine_doc_type(text) String
    }

    class MRZParser {
        +parse_mrz(mrz_lines) Dict
        -_format_yy_mm_dd(yy_str) String
    }

    class IndianIDParser {
        +extract_aadhaar_fields(text) Dict
        +extract_clean_indian_person_name(lines) String
        +validate_verhoeff(aadhaar_num) Boolean
    }

    class ForensicsService {
        +analyze_exif(image_bytes) Dict
        +analyze_stamp_authenticity(image_bytes) Dict
    }

    class BiometricService {
        +verify_face_match(doc_crop, selfie_img) Float
        +check_liveness(selfie_img) Float
    }

    class WatchlistEngine {
        +check_watchlist(name, doc_num, dob) Dict
        -fuzzy_name_match(name1, name2) Float
    }

    class BlockchainLogger {
        +append_audit_block(session_data) String
        +verify_chain_integrity() Boolean
    }

    ScreeningController --> DocumentExtractionService
    ScreeningController --> ForensicsService
    ScreeningController --> BiometricService
    ScreeningController --> WatchlistEngine
    ScreeningController --> BlockchainLogger
    DocumentExtractionService --> MRZParser
    DocumentExtractionService --> IndianIDParser
```

---

## 10. Database Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    SCREENING_SESSION ||--o{ DOCUMENT_FORENSICS : conducts
    SCREENING_SESSION ||--o{ BIOMETRIC_VERIFICATION : evaluates
    SCREENING_SESSION ||--o{ WATCHLIST_MATCH : queries
    SCREENING_SESSION ||--|| AUDIT_BLOCK : seals

    SCREENING_SESSION {
        string session_id PK
        string report_id
        datetime timestamp
        string officer_id
        string overall_decision
        int risk_score
        string risk_level
    }

    DOCUMENT_FORENSICS {
        string forensics_id PK
        string session_id FK
        string document_type
        string extracted_name
        string extracted_doc_no
        boolean exif_manipulated
        float stamp_authenticity_score
    }

    BIOMETRIC_VERIFICATION {
        string verification_id PK
        string session_id FK
        float face_similarity_score
        float liveness_confidence
        string biometric_verdict
    }

    WATCHLIST_MATCH {
        string match_id PK
        string session_id FK
        string watchlist_status
        float fuzzy_match_confidence
        string target_database
    }

    AUDIT_BLOCK {
        int block_index PK
        string session_id FK
        string block_hash
        string previous_hash
        string merkle_root
        datetime mined_at
    }
```

---

## 11. STRIDE Threat Model & Security Matrix Diagram

```mermaid
graph TD
    subgraph STRIDEThreats ["STRIDE Security Threat Vector Analysis"]
        T1["Spoofing: Photo Replay / Fake Identity Card"]
        T2["Tampering: Image Pixel Editing / Stamp Forgery"]
        T3["Repudiation: Officer Denies Screening Action"]
        T4["Information Disclosure: PII Data Leakage"]
        T5["Denial of Service: Resource Exhaustion via High-Res Images"]
        T6["Elevation of Privilege: Bypassing Watchlist Alert"]
    end

    subgraph Countermeasures ["Trinetra Cryptographic & AI Mitigation Controls"]
        M1["Biometric Liveness Verification + Facenet Embeddings"]
        M2["EXIF Software Scanning + HSV Color Segmentation"]
        M3["Cryptographic SHA-256 Immutable Blockchain Audit Ledger"]
        M4["AES-256 Encryption at Rest + TLS 1.3 in Transit"]
        M5["FastAPI Rate Limiting + Async Processing Pipeline"]
        M6["Automated Multi-Database Watchlist Cross-Referencing"]
    end

    T1 --> M1
    T2 --> M2
    T3 --> M3
    T4 --> M4
    T5 --> M5
    T6 --> M6
```

---

## 12. API Specification Contract

### Endpoint: `POST /api/v1/screen-document`

#### Request Payload (`multipart/form-data`)
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `passport_image` | `File` | Yes | Scanned Passport, Visa, Aadhaar, or DL image (JPEG/PNG/PDF) |
| `live_frame` | `File` | Yes | Live webcam selfie frame (JPEG/PNG) |

#### Response Payload (`application/json`)
```json
{
  "status": "success",
  "report_id": "RPT-F83ADA4E",
  "session_id": "TRN-902184",
  "risk_score": 0,
  "risk_level": "Low",
  "decision": "Clean",
  "action": "e-Gate unlocked — standard entry authorised.",
  "watchlist_status": "CLEAR ✓",
  "block_hash": "0x7f8a9b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b2c3d4e5f6a7b8c9d0e1f2a",
  "extracted_data": {
    "name": "Pranshu Pareshbhai Bodara",
    "document_number": "7889 5512 3209",
    "document_type": "Aadhaar Card (UIDAI)",
    "date_of_birth": "28/05/2007",
    "gender": "MALE",
    "nationality": "IND",
    "visa_type": null,
    "stay_duration": null
  },
  "ai_confidence": {
    "ocr_confidence": 0.95,
    "document_authenticity": 0.98,
    "face_similarity": 0.92,
    "liveness_score": 0.96,
    "exif_analysis": {
      "verdict": "CLEAN_METADATA",
      "software_detected": false
    }
  },
  "reasons": [
    "Document authenticity verified",
    "Face match confirmed",
    "Liveness check passed",
    "SSB / Interpol Blacklist check clear"
  ],
  "screened_at": "2026-09-07T23:00:00Z"
}
```

---

## 13. Verification & Test Matrix

| Test Suite | Execution Command | Coverage Target | Status |
| :--- | :--- | :--- | :--- |
| **Document OCR Engine** | `python scratch/test_aadhaar_parser.py` | Aadhaar Verhoeff & Name extraction | **PASS ✓** |
| **Visa MRZ Detection** | `python scratch/test_visa_mrz_detection.py` | ICAO MRV Visa vs Passport separation | **PASS ✓** |
| **OCR Noise Rejection** | `python scratch/test_tt_rejection.py` | Rejection of `Tt Tt` single-char artifacts | **PASS ✓** |
| **End-to-End Pipeline** | `python scratch/test_sih_screening_indian_docs.py` | Full `/api/v1/screen-document` integration | **PASS ✓** |
| **Frontend Production Build** | `python scratch/build_frontend.py` | Zero Next.js compilation / hydration errors | **PASS ✓** |

---

*Documentation compiled for Trinetra Core Development Team & Ministry of Home Affairs (SIH PS ID: 26188).*
