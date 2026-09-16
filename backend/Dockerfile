FROM python:3.11-slim

# Install system dependencies (OpenCV & Tesseract OCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Expose backend port
EXPOSE 8000

# Run FastAPI with Uvicorn
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
