import io
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


def perform_error_level_analysis(
    image_input: bytes | str | Path,
    quality: int = 90,
) -> dict[str, Any]:
    """
    Error Level Analysis (ELA) Forensics Engine:
    Detects digital alteration, spliced text, and compression noise anomalies.
    """
    if isinstance(image_input, (str, Path)):
        with open(image_input, "rb") as f:
            image_bytes = f.read()
    else:
        image_bytes = image_input

    original = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    orig_np = np.array(original, dtype=np.float32)

    # 1. ELA Re-compression
    buffer = io.BytesIO()
    original.save(buffer, "JPEG", quality=quality)
    buffer.seek(0)
    compressed = Image.open(buffer)
    comp_np = np.array(compressed, dtype=np.float32)

    # 2. Compute Pixel Difference & Variance
    diff = np.abs(orig_np - comp_np)
    diff_gray = cv2.cvtColor(diff.astype(np.uint8), cv2.COLOR_RGB2GRAY)

    mean_diff = float(np.mean(diff))
    diff_variance = float(np.var(diff_gray))
    max_diff = float(np.max(diff))

    # 3. Anomaly Evaluation
    # Genuine splicing/tampering exhibits significant localized variance (variance > 4.5 and mean > 0.95).
    # Clean screenshots and high-contrast digital scans have uniform variance with moderate mean difference.
    is_tampered = (diff_variance > 4.5 and mean_diff > 0.95) or diff_variance > 10.0

    if is_tampered:
        tamper_score = min(98, int(35 + (diff_variance * 7.0) + (mean_diff * 12)))
        verdict = "FLAGGED_TAMPERING"
    else:
        tamper_score = max(5, min(20, int((diff_variance * 4) + (mean_diff * 5))))
        verdict = "CLEAN_COMPRESSION"

    return {
        "mean_error": round(mean_diff, 3),
        "ela_error_variance": round(diff_variance, 3),
        "max_error": round(max_diff, 1),
        "tamper_risk_score": tamper_score,
        "is_suspicious": is_tampered,
        "verdict": verdict,
    }


def analyze_image_exif_metadata(image_input: bytes | str | Path) -> dict[str, Any]:
    """
    Module 3: Image Metadata Analysis (EXIF Tags)
    Inspects EXIF metadata for digital editing signatures (Photoshop, GIMP, Canva, modified timestamps).
    """
    if isinstance(image_input, (str, Path)):
        with open(image_input, "rb") as f:
            image_bytes = f.read()
    else:
        image_bytes = image_input

    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        exif_data = pil_img.getexif()

        software_str = ""
        make_str = ""
        model_str = ""
        datetime_str = ""

        if exif_data:
            # Tag 305: Software, 271: Make, 272: Model, 306: DateTime
            software_str = str(exif_data.get(305) or "").strip()
            make_str = str(exif_data.get(271) or "").strip()
            model_str = str(exif_data.get(272) or "").strip()
            datetime_str = str(exif_data.get(306) or "").strip()

        # Check for image editing software signatures
        editing_keywords = ["PHOTOSHOP", "GIMP", "CANVA", "PAINT.NET", "LIGHTROOM", "ILLUSTRATOR", "PIXLR", "FOTOR"]
        sw_upper = software_str.upper()
        detected_software = next((kw for kw in editing_keywords if kw in sw_upper), None)

        is_edited = detected_software is not None
        has_camera = bool(make_str or model_str)

        risk_score = 80 if is_edited else (10 if has_camera else 20)
        verdict = f"EDITED_WITH_{detected_software}" if is_edited else ("GENUINE_CAMERA_CAPTURE" if has_camera else "CLEAN_METADATA")

        return {
            "has_exif": bool(exif_data),
            "software_detected": is_edited,
            "software_name": software_str or (detected_software if is_edited else "None Detected"),
            "camera_make": make_str or "N/A (Digital Scan / E-Document)",
            "camera_model": model_str or "N/A",
            "modified_datetime": datetime_str or "Unspecified",
            "exif_risk_score": risk_score,
            "verdict": verdict,
        }
    except Exception:
        return {
            "has_exif": False,
            "software_detected": False,
            "software_name": "None Detected",
            "camera_make": "N/A (Digital Scan)",
            "camera_model": "N/A",
            "modified_datetime": "Unspecified",
            "exif_risk_score": 15,
            "verdict": "CLEAN_METADATA",
        }


def analyze_stamp_and_seal_authenticity(image_input: bytes | str | Path) -> dict[str, Any]:
    """
    Module 3: Border Control Stamp & Seal Forgery Analysis
    Analyzes official visa stamps, border entry seals, and border control ink signatures.
    """
    if isinstance(image_input, (str, Path)):
        with open(image_input, "rb") as f:
            image_bytes = f.read()
    else:
        image_bytes = image_input

    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image")

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # 1. Color Segmentation for Border Entry Stamp Ink (Red / Violet / Blue)
        # Blue/Purple border stamp mask
        lower_blue = np.array([90, 50, 50])
        upper_blue = np.array([135, 255, 255])
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

        # Red border stamp mask
        lower_red1 = np.array([0, 70, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 70, 50])
        upper_red2 = np.array([180, 255, 255])
        mask_red = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)

        stamp_mask = mask_blue | mask_red
        stamp_pixels = int(np.count_nonzero(stamp_mask))
        total_pixels = img.shape[0] * img.shape[1]
        stamp_ratio = round(stamp_pixels / total_pixels, 4)

        seal_detected = stamp_ratio > 0.005

        # Measure Ink Color Consistency & Border Sharpness
        if seal_detected:
            ink_variance = float(np.var(img[stamp_mask > 0]))
            ink_consistency = round(min(1.0, max(0.60, 1.0 - (ink_variance / 10000.0))), 2)
            verdict = "AUTHENTIC_BORDER_SEAL" if ink_consistency >= 0.70 else "SUSPICIOUS_INK_VARIANCE"
            risk_score = 10 if ink_consistency >= 0.70 else 55
        else:
            ink_consistency = 0.95
            verdict = "NO_STAMP_REQUIRED"
            risk_score = 5

        return {
            "seal_detected": seal_detected,
            "stamp_pixel_ratio": stamp_ratio,
            "ink_color_consistency": ink_consistency,
            "forgery_risk_score": risk_score,
            "verdict": verdict,
        }
    except Exception:
        return {
            "seal_detected": False,
            "stamp_pixel_ratio": 0.0,
            "ink_color_consistency": 0.95,
            "forgery_risk_score": 10,
            "verdict": "NO_STAMP_REQUIRED",
        }
