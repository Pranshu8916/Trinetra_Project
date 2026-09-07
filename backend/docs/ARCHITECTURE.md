# Trinetra Backend Architecture & Technical Design

This document details the architectural principles, component decomposition, data flows, and AI/ML algorithms powering the **Trinetra** backend engine.

---

## 🏛️ High-Level System Architecture

```text
  +-----------------------------------------------------------------------+
  |                           Client Applications                          |
  |                (Next.js Web Frontend / Mobile Scanner)                |
  +-----------------------------------------------------------------------+
                                      |
                                HTTP / JSON REST
                                      v
  +-----------------------------------------------------------------------+
  |                        FastAPI ASGI Web Server                        |
  |                                                                       |
  |  +-----------------------------------------------------------------+  |
  |  |                     CORS & Security Middleware                   |  |
  |  +-----------------------------------------------------------------+  |
  |  |                    Authentication Router (/api/auth)             |  |
  |  |                    User Management Router (/api/users)           |  |
  |  |                    Verification Router (/api/verification)       |  |
  |  +-----------------------------------------------------------------+  |
  +-----------------------------------------------------------------------+
           |                                  |                        |
           v                                  v                        v
  +-------------------+              +------------------+    +------------------+
  | Service Layer     |              | AI/ML Pipeline   |    | Persistence      |
  |                   |              |                  |    |                  |
  | • Session Manager |              | • OCR (Tesseract)|    | • MongoDB        |
  | • Auth Service    |              | • ELA Forensics  |    |   (Users/Docs)   |
  | • File Storage    |              | • Passive Live   |    | • Storage Dir    |
  |   Service         |              | • 1:1 Face Match |    |   (Images)       |
  |                   |              | • Risk Engine    |    |                  |
  +-------------------+              +------------------+    +------------------+
```

---

## 🧩 Component Decomposition

### 1. API & Routing Layer (`app/api/`)
- **`auth.py`**: Handles user login, password authentication against Argon2 hashes, and JWT token issuance.
- **`users.py`**: User registration, role assignments (`operator`, `verifier`, `admin`), and profile queries.
- **`verification.py`**: Orchestrates the multi-step verification process:
  - Session Creation (`POST /api/verification/sessions`)
  - Document Upload (`POST /api/verification/sessions/{id}/document`)
  - OCR Processing (`POST /api/verification/documents/{id}/process`)
  - Biometric Selfie Upload (`POST /api/verification/sessions/{id}/biometric`)
  - Full Pipeline Execution (`POST /api/verification/sessions/{id}/verify`)
  - Result Retrieval (`GET /api/verification/sessions/{id}/result`)

### 2. Core & Configuration Layer (`app/core/`)
- **`config.py`**: Manages environment variables using Pydantic `BaseSettings`. Features alias handling for flexible environment key resolution (`MONGODB_URL` / `MONGODB_URI`).
- **`database.py`**: Initializes Motor (AsyncMongoClient) database connections with safe connection timeouts (`serverSelectionTimeoutMS=3000`) and index initialization during application startup lifespan.
- **`security.py`**: Implements Argon2id password hashing via `pwdlib` and JWT token creation/decoding using `PyJWT`.

### 3. Service & Utility Layer (`app/services/` & `app/utils/`)
- **`ocr_service.py`**: Executes Optical Character Recognition using EasyOCR / Tesseract OCR with automatic Windows path detection and 2x Lanczos upscaling for low-resolution documents.
- **`document_extraction_service.py`**: Applies regular expression parsers over raw OCR text to extract 9 structured identity fields: Name, Document Number, Document Type, Date of Birth, Date of Issue, Date of Expiry, Gender, Nationality, and Address.
- **`forensics_service.py`**: Conducts Error Level Analysis (ELA) to detect digital tampering, JPEG resaving anomalies, and localized compression noise.
- **`ai_biometrics_service.py`**: Provides 1:1 facial similarity comparison using joint color-histogram and structural SSIM metrics, as well as passive liveness anti-spoofing evaluation.
- **`mrz_parser.py`**: Implements ICAO Doc 9303 TD3 Passport MRZ parsing and modulus 10 weighting factor checksum validation algorithms.

---

## 🤖 AI / ML Subsystems & Algorithmic Blueprint

### Module 1: ICAO Doc 9303 MRZ Checksum Validation
Evaluates Machine Readable Zone lines on passports and official travel documents using ICAO Doc 9303 standard weighting factors `[7, 3, 1]`:

$$C = \left( \sum_{i=1}^{n} V(d_i) \cdot w_{((i-1) \bmod 3) + 1} \right) \bmod 10$$

Calculates individual document number, birth date, expiration date, and overall composite checksums to detect alphanumeric tampering.

### Module 2: Error Level Analysis (ELA) Digital Forensics
Detects image manipulation by resaving the document at a known JPEG quality level (90%) and analyzing error variance:

$$E(x,y) = |I_{orig}(x,y) - I_{resaved}(x,y)|$$

Computes error variance and mean pixel differences. Elevated variance indicates localized editing or copy-paste tampering.

### Module 3: Passive Liveness & Anti-Spoofing Assessment
Evaluates live selfie captures using non-intrusive spatial and frequency domain analysis:
1. **Laplacian Blur Variance**: Computes $\text{Var}(\nabla^2 I)$ to detect out-of-focus digital screens or printed photo attacks.
2. **Color Channel Saturation**: Evaluates HSV color distributions to detect low-gamut re-photographed displays.

### Module 4: 1:1 Joint Color-Structure Biometric Face Verification
Compares document portrait ROI against live selfie capture using a dual-branch feature alignment strategy:
- **Structural Similarity Index (SSIM)**: Evaluates spatial geometry, luminance, and contrast structure.
- **Color Histogram Cosine Distance**: Evaluates skin-tone distribution and color variance.
Outputs normalized similarity percentage and match verdict (`MATCHED` vs `NOT_MATCHED`).

### Module 5: Multi-Signal Rule-Based Risk Engine
Aggregates signal confidence across all 4 sub-modules into a single composite risk score ($0 - 100$):

$$\text{RiskScore} = \sum_{m} W_m \cdot S_m$$

Categorizes results into clear operational decisions:
- **`CLEAR_ENTRY`**: Risk Score $< 40$, All checks passed.
- **`SECONDARY_SCAN`**: Risk Score $40 - 75$, Minor anomalies detected (e.g. missing non-critical fields, border line quality).
- **`DETAIN_ESCALATE`**: Risk Score $> 75$, Critical failure (tampering detected, face mismatch, or liveness failure).

---

## 🔒 Security & Data Isolation Architecture

1. **User Access Boundaries**: All verification endpoints check session ownership against `current_user.id`. Requests for sessions belonging to other operators return strict `404 Not Found` responses.
2. **Stateless JWT Security**: Passwords are never returned in responses. Tokens expire after 24 hours (1440 minutes) and require bearer headers.
3. **Strict Validation**: Pydantic schemas enforce type safety, stripping unexpected inputs.
