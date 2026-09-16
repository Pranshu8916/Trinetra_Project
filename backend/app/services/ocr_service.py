from pathlib import Path
import shutil

import pytesseract
from PIL import Image
from pypdf import PdfReader


if not shutil.which("tesseract"):
    win_tesseract = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if win_tesseract.exists():
        pytesseract.pytesseract.tesseract_cmd = str(win_tesseract)


_easyocr_reader = None


def get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            _easyocr_reader = easyocr.Reader(["en"], gpu=False)
        except Exception:
            _easyocr_reader = False
    return _easyocr_reader

from PIL import ImageEnhance

def extract_text_from_image(file_path: str) -> str:
    extracted_lines = []

    # Preprocess image with PIL (LANCZOS sharpness + PNG lossless save for crisp text)
    enhanced_path = file_path
    try:
        image = Image.open(file_path)
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Keep ideal dimensions (800px-1800px) with sharp LANCZOS resampling
        max_dim = max(image.width, image.height)
        if max_dim > 1800:
            scale = 1800.0 / max_dim
            new_w = int(image.width * scale)
            new_h = int(image.height * scale)
            image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        elif max_dim < 1000:
            scale = 1400.0 / max_dim
            new_w = int(image.width * scale)
            new_h = int(image.height * scale)
            image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.6)

        import tempfile
        tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        image.save(tmp_img.name, format="PNG")
        enhanced_path = tmp_img.name
    except Exception:
        pass

    # 1. Pytesseract on enhanced image (Ultra lightweight ~15MB RAM)
    try:
        tess_text = pytesseract.image_to_string(Image.open(enhanced_path))
        if tess_text:
            for l in tess_text.splitlines():
                if l.strip() and l.strip() not in extracted_lines:
                    extracted_lines.append(l.strip())
    except Exception:
        pass

    # 2. EasyOCR fallback (Only if pytesseract yields no text)
    if not extracted_lines:
        reader = get_easyocr_reader()
        if reader:
            try:
                lines = reader.readtext(enhanced_path, detail=0)
                if lines:
                    extracted_lines.extend(lines)
            except Exception:
                pass

    if extracted_lines:
        return "\n".join(extracted_lines).strip()
    return ""




def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    extracted_text = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            extracted_text.append(text)

    return "\n".join(extracted_text).strip()


def extract_text(
    file_path: str,
    content_type: str,
) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Document file not found: {file_path}")

    if content_type.startswith("image/") or content_type in {"application/octet-stream", "blob"}:
        return extract_text_from_image(str(path))

    if content_type == "application/pdf":
        return extract_text_from_pdf(str(path))

    return extract_text_from_image(str(path))
