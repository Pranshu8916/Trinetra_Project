FROM python:3.11-slim

# Install system dependencies (OpenCV & Tesseract OCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pin NumPy 1.x, Pillow 10.2.0, and PyTorch 2.2.2 CPU wheel
RUN pip install --no-cache-dir "numpy<2.0.0" "Pillow>=10.2.0,<10.3.0"
RUN pip install --no-cache-dir "torch==2.2.2" "torchvision==0.17.2" --index-url https://download.pytorch.org/whl/cpu

# Copy requirements & install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source files
COPY backend/ .

EXPOSE 8000

# Use shell exec format so $PORT dynamically binds to Railway's assigned port
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
