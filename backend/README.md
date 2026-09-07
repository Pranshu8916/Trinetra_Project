# Trinetra Backend API & AI Verification Engine

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/framework-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/database-MongoDB-47A248.svg)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#)

Trinetra is an enterprise-grade backend service powering AI-driven document fraud detection, ICAO MRZ checksum validation, 1:1 face verification, passive liveness assessment, and automated border security risk scoring.

---

## 📁 Repository Structure

```text
backend/
├── app/                        # FastAPI Application Core
│   ├── api/                    # HTTP Endpoints & Routers
│   │   ├── auth.py             # User Authentication & JWT Issuance
│   │   ├── health.py           # Service Health & DB Status
│   │   ├── users.py            # User Management & RBAC
│   │   ├── protected.py        # Authenticated Operator Endpoints
│   │   └── verification.py     # Document & Biometric Verification Pipeline
│   ├── core/                   # Infrastructure & Configuration
│   │   ├── config.py           # Pydantic Settings & Environment Loading
│   │   ├── database.py         # AsyncMongoClient Connections & Indexing
│   │   └── security.py         # Password Hashing (Argon2) & JWT Verification
│   ├── models/                 # MongoDB Domain Schemas
│   ├── providers/              # Abstract & Implemented AI/ML Providers
│   ├── schemas/                # Pydantic Request/Response DTOs
│   ├── services/               # Core Business Logic Services
│   ├── utils/                  # Algorithmic Utilities (MRZ, ELA, Face, Liveness)
│   └── main.py                 # FastAPI Application Entrypoint
├── tests/                      # Testing Framework
│   ├── unit/                   # Algorithmic & Unit Test Suites
│   └── integration/            # End-to-End & API Integration Tests
├── scripts/                    # Utility & Operational CLI Tools
│   └── run_models_on_images.py # Standalone Multi-Model Inference CLI
├── storage/                    # Persistent File Storage (Git-Ignored)
│   ├── documents/              # Identity Document Uploads
│   └── biometrics/             # Live Selfie Uploads
├── logs/                       # Application Runtime Logs
├── docs/                       # Comprehensive Architecture & Operational Docs
│   ├── ARCHITECTURE.md         # Technical Design & ML Pipeline Blueprint
│   ├── DEPLOYMENT.md           # Native VM / Bare-Metal Production Deployment Guide
│   └── PRODUCTION_READINESS.md # Security Audit & Readiness Assessment Report
├── .env.example                # Environment Variable Template
├── .gitignore                  # Git Hygiene Configuration
├── requirements.txt            # Python Runtime Dependencies
└── README.md                   # Developer & Operational Manual
```

---

## 🛠️ Prerequisites

1. **Python**: Python 3.12 or higher.
2. **MongoDB**: Local MongoDB instance (`mongodb://localhost:27017`) or cloud cluster (MongoDB Atlas).
3. **Tesseract OCR**:
   - **Windows**: Install via `winget install UB-Mannheim.TesseractOCR`.
   - **Linux**: Install via `sudo apt-get install tesseract-ocr`.
   - **macOS**: Install via `brew install tesseract`.

---

## 🚀 Quickstart & Local Setup

### 1. Environment Isolation
Create and activate a dedicated Python virtual environment:

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate
```

### 2. Dependency Installation
Install runtime dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the environment template and adjust values:

```bash
cp .env.example .env
```

Ensure `MONGODB_URL` points to your active MongoDB instance and set a strong `JWT_SECRET`.

---

## 🖥️ Running the Backend Server

### Development Mode (Hot-Reloading)

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The interactive API documentation (Swagger UI) is available at `http://127.0.0.1:8000/docs`.

### Production Mode (Multi-Worker Native Execution)

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Refer to [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for full Systemd service setup and Nginx reverse proxy configuration.

---

## 🧪 Running Verification Test Suites

The backend includes a comprehensive suite of algorithmic unit tests, API integration tests, and full end-to-end verification pipelines.

Ensure the backend server is running (`http://127.0.0.1:8000`), then execute:

```bash
# 1. Run Unit Tests (Algorithmic & Forensic Logic)
python tests/unit/test_supplied_ai_modules.py

# 2. Run API Document OCR & Field Extraction Integration Tests
python tests/integration/test_phase8_runtime.py

# 3. Run Structured Identity Extraction & Isolation Tests
python tests/integration/test_phase9_runtime.py

# 4. Run Real AI Providers Runtime Verification
python tests/integration/test_real_ai_providers_runtime.py

# 5. Run Full End-to-End Border Verification Pipeline Test
python tests/integration/test_e2e_complete_runtime.py
```

---

## 🤖 Multi-Model CLI Inference Tool

Run all 5 AI/ML algorithms directly on local images without launching the web server:

```bash
# Execute using default storage samples
python scripts/run_models_on_images.py

# Execute on custom image paths
python scripts/run_models_on_images.py -d /path/to/passport.png -s /path/to/selfie.jpg
```

---

## 🔐 Security & Operations

- **Authentication**: Stateless JWT bearer tokens signed using HMAC SHA-256 (`HS256`).
- **Password Security**: Argon2id hashing via `pwdlib`.
- **Storage**: Isolated filesystem storage with mandatory user verification boundaries.
- **Documentation**:
  - Technical Design: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
  - Native Deployment: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
  - Readiness Audit: [`docs/PRODUCTION_READINESS.md`](docs/PRODUCTION_READINESS.md)
