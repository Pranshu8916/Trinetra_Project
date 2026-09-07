# Trinetra Backend Production Deployment Guide

This guide details the operational procedure for deploying the **Trinetra** backend on a native server / virtual machine (Ubuntu Linux or Windows Server) **without using Docker containers**.

---

## 📋 Production Server Prerequisites

- **OS**: Ubuntu 22.04 LTS / 24.04 LTS or Windows Server 2022.
- **Python**: Python 3.12+ installed.
- **Database**: MongoDB 7.0+ installed locally or accessible via MongoDB Atlas URI.
- **System Utilities**: `tesseract-ocr`, `nginx`, `git`, `systemd`.

---

## 🛠️ Step-by-Step Native Deployment (Ubuntu Linux)

### Step 1: System Package Installation

Update system repositories and install essential binary dependencies:

```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3.12 python3.12-venv python3-pip tesseract-ocr nginx git
```

Verify Tesseract installation:

```bash
tesseract --version
```

---

### Step 2: Codebase & Virtual Environment Setup

Clone the repository and set up a dedicated virtual environment in `/opt/trinetra/backend`:

```bash
sudo mkdir -p /opt/trinetra
sudo chown -R $USER:$USER /opt/trinetra
cd /opt/trinetra

# Copy backend files to /opt/trinetra/backend
cd backend

# Create production virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Step 3: Production Environment File Setup

Create the production `.env` configuration file:

```bash
cp .env.example .env
nano .env
```

Configure production parameters:

```ini
PROJECT_NAME="Trinetra - AI Border Security Backend"
API_V1_STR="/api"

# Production MongoDB Atlas or Local Connection String
MONGODB_URL="mongodb://localhost:27017"
MONGODB_DATABASE="trinetra_prod_db"

# Secure Random JWT Key (32+ bytes)
JWT_SECRET="e9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440

USE_MOCK_MODE=false
```

---

### Step 4: Systemd Service Unit Creation

Create a systemd unit file to manage the Uvicorn process:

```bash
sudo nano /etc/systemd/system/trinetra-backend.service
```

Paste the following service definition:

```ini
[Unit]
Description=Trinetra FastAPI Backend Service
After=network.target mongodb.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/trinetra/backend
ExecStart=/opt/trinetra/backend/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5
Environment=PATH=/opt/trinetra/backend/venv/bin:/usr/bin:/usr/local/bin
StandardOutput=append:/opt/trinetra/backend/logs/backend.log
StandardError=append:/opt/trinetra/backend/logs/backend_error.log

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable trinetra-backend
sudo systemctl start trinetra-backend
sudo systemctl status trinetra-backend
```

---

### Step 5: Nginx Reverse Proxy & SSL Configuration

Create an Nginx server block to proxy traffic to Uvicorn:

```bash
sudo nano /etc/nginx/sites-available/trinetra
```

Paste the configuration:

```nginx
server {
    listen 80;
    server_name api.trinetra.internal;

    # Increase max upload size for document & selfie images
    client_max_body_size 25M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
    }
}
```

Activate site configuration and reload Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/trinetra /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🪟 Windows Server Native Deployment

For Windows Server environments:

1. **Install Tesseract OCR** via `winget install UB-Mannheim.TesseractOCR`.
2. **Install Python 3.12** and add to System PATH.
3. **NSSM (Non-Sucking Service Manager)**:
   Register Uvicorn as a Windows Service:
   ```cmd
   nssm install TrinetraBackend "C:\path\to\backend\venv\Scripts\python.exe" "-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4"
   nssm start TrinetraBackend
   ```
