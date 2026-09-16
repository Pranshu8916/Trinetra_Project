FROM python:3.11-slim

# Install system dependencies (OpenCV & Tesseract OCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pin NumPy 1.x and Pillow 10.2.0 BEFORE installing PyTorch & OpenCV
RUN pip install --no-cache-dir "numpy<2.0.0" "Pillow>=10.2.0,<10.3.0"
RUN pip install --no-cache-dir torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu

# Copy and install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Expose backend port
EXPOSE 8000

# Run FastAPI with Uvicorn on port 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
