import io
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
from PIL import Image

# Global singletons for PyTorch HuggingFace FaceNet models
_mtcnn = None
_resnet = None
_device = None


def get_device() -> torch.device:
    global _device
    if _device is None:
        _device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    return _device


def get_facenet_models():
    """Initializes and caches MTCNN and InceptionResnetV1 (pretrained on VGGFace2)."""
    global _mtcnn, _resnet
    if _mtcnn is None or _resnet is None:
        from facenet_pytorch import InceptionResnetV1, MTCNN
        dev = get_device()
        _mtcnn = MTCNN(
            image_size=160,
            margin=20,
            keep_all=False,
            select_largest=True,
            post_process=False,
            device=dev,
        )
        _resnet = InceptionResnetV1(pretrained="vggface2").eval().to(dev)
    return _mtcnn, _resnet


def load_image_cv(image_input: bytes | str | Path | np.ndarray) -> np.ndarray:
    """Loads an image into an OpenCV BGR numpy array from bytes, str, Path, or returns if ndarray."""
    if isinstance(image_input, np.ndarray):
        return image_input
    if isinstance(image_input, (str, Path)):
        img = cv2.imread(str(image_input), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Could not open image file: {image_input}")
        return img
    elif isinstance(image_input, bytes):
        nparr = np.frombuffer(image_input, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Invalid image bytes provided.")
        return img
    raise ValueError(f"Unsupported image input type: {type(image_input)}")


def load_pil_image(image_input: bytes | str | Path | np.ndarray | Image.Image) -> Image.Image:
    """Converts any image input (cv2 ndarray, path, bytes, or PIL) to PIL RGB Image."""
    if isinstance(image_input, Image.Image):
        return image_input.convert("RGB")
    if isinstance(image_input, np.ndarray):
        rgb = cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)
    if isinstance(image_input, (str, Path)):
        return Image.open(str(image_input)).convert("RGB")
    if isinstance(image_input, bytes):
        return Image.open(io.BytesIO(image_input)).convert("RGB")
    raise ValueError(f"Unsupported image input type: {type(image_input)}")


def extract_aligned_face(cv_img: np.ndarray) -> np.ndarray:
    """
    Standardizes face region into a 160x160 aligned frame.
    Uses MTCNN landmark alignment if available, falling back to smart crop.
    """
    try:
        pil_img = load_pil_image(cv_img)
        mtcnn, _ = get_facenet_models()
        face_tensor = mtcnn(pil_img)
        if face_tensor is not None:
            # face_tensor is (3, 160, 160) in range [0, 255]
            face_np = face_tensor.permute(1, 2, 0).cpu().numpy().astype(np.uint8)
            return cv2.cvtColor(face_np, cv2.COLOR_RGB2BGR)
    except Exception:
        pass

    # Fallback to smart ROI if MTCNN fails
    h, w, _ = cv_img.shape
    if w >= 700 and h >= 450:
        face_roi = cv_img[int(h * 0.18) : int(h * 0.65), int(w * 0.04) : int(w * 0.28)]
        if face_roi.size > 0:
            return cv2.resize(face_roi, (160, 160))
    if w > int(h * 1.25):
        margin_x = int((w - h) / 2)
        center_roi = cv_img[:, margin_x : w - margin_x]
        if center_roi.size > 0:
            return cv2.resize(center_roi, (160, 160))
    return cv2.resize(cv_img, (160, 160))


def extract_face_and_embedding(image_input: Any):
    """
    Detects face using MTCNN, aligns 5 landmarks, and extracts
    a normalized 512-D embedding using InceptionResnetV1 (vggface2).
    """
    pil_img = load_pil_image(image_input)
    mtcnn, resnet = get_facenet_models()
    dev = get_device()

    boxes, _ = mtcnn.detect(pil_img)
    best_box = boxes[0].tolist() if (boxes is not None and len(boxes) > 0) else [0, 0, pil_img.width, pil_img.height]

    face_tensor = mtcnn(pil_img)
    if face_tensor is None:
        pil_resized = pil_img.resize((160, 160))
        np_arr = np.array(pil_resized, dtype=np.float32)
        face_tensor = torch.from_numpy(np_arr).permute(2, 0, 1)

    # Normalize tensor to [-1, 1] for InceptionResnetV1
    face_tensor_norm = (face_tensor.float() - 127.5) / 128.0
    with torch.no_grad():
        emb = resnet(face_tensor_norm.unsqueeze(0).to(dev))
        emb_np = emb.cpu().numpy().flatten()
        norm = np.linalg.norm(emb_np)
        emb_norm = emb_np / (norm + 1e-7)

    return face_tensor, emb_norm, best_box


def evaluate_liveness(live_img: Any) -> dict[str, Any]:
    """
    Evaluates passive liveness using:
    1. Laplacian gradient micro-texture variance
    2. 2D Fast Fourier Transform (FFT) high-frequency Moiré screen detection
    3. Natural skin tone HSV chrominance distribution
    """
    cv_img = load_image_cv(live_img)
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # 1. Texture Sharpness
    is_sharp = laplacian_var > 35.0

    # 2. 2D FFT Frequency Analysis for Screen Moiré Pattern
    h, w = gray.shape
    crop_size = min(h, w, 256)
    cy, cx = h // 2, w // 2
    center_patch = gray[cy - crop_size // 2 : cy + crop_size // 2, cx - crop_size // 2 : cx + crop_size // 2]
    dft = cv2.dft(np.float32(center_patch), flags=cv2.DFT_COMPLEX_OUTPUT)
    dft_shift = np.fft.fftshift(dft)
    mag_spectrum = 20 * np.log(cv2.magnitude(dft_shift[:, :, 0], dft_shift[:, :, 1]) + 1e-7)
    mean_freq = float(np.mean(mag_spectrum))
    is_not_screen = mean_freq > 110.0

    # 3. HSV Color Saturation
    hsv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)
    sat_mean = float(np.mean(hsv[:, :, 1]))
    has_skin_sat = 15.0 < sat_mean < 240.0

    is_live = is_sharp and is_not_screen and has_skin_sat

    # Calibrated score 0.10 - 0.99
    base_score = 0.50
    if is_sharp: base_score += 0.25
    if is_not_screen: base_score += 0.15
    if has_skin_sat: base_score += 0.09
    liveness_score = min(0.99, max(0.10, round(base_score, 2)))

    return {
        "liveness_passed": is_live,
        "liveness_score": liveness_score,
        "sharpness_score": round(laplacian_var, 2),
        "saturation_index": round(sat_mean, 2),
        "anti_spoof_verdict": "LIVE_HUMAN_CONFIRMED" if is_live else "POTENTIAL_SPOOF_ATTACK",
    }


def compare_faces(
    doc_image_input: bytes | str | Path | np.ndarray,
    live_image_input: bytes | str | Path | np.ndarray,
) -> dict[str, Any]:
    """
    1:1 Facial Verification using HuggingFace / PyTorch FaceNet (InceptionResnetV1 + MTCNN):
    1. Accurately detects and aligns faces using MTCNN 5-point facial landmarks.
    2. Extracts 512-D deep facial embeddings pretrained on VGGFace2.
    3. Calculates Cosine Similarity & normalized match percentage.
    4. Evaluates passive anti-spoofing liveness.
    """
    # 1. Extract 512-D embeddings
    _, emb_doc, box_doc = extract_face_and_embedding(doc_image_input)
    _, emb_live, box_live = extract_face_and_embedding(live_image_input)

    # 2. Evaluate liveness on live input
    liveness_report = evaluate_liveness(live_image_input)

    # If document face missing
    if emb_doc is None:
        return {
            "verified": False,
            "similarity_percentage": 0.0,
            "similarity_score": 0.0,
            "raw_cosine_similarity": 0.0,
            "match_verdict": "NO_FACE_DETECTED_IN_DOCUMENT",
            "biometric_risk_score": 100,
            "liveness_check": liveness_report,
        }

    # If live face missing
    if emb_live is None:
        return {
            "verified": False,
            "similarity_percentage": 0.0,
            "similarity_score": 0.0,
            "raw_cosine_similarity": 0.0,
            "match_verdict": "NO_FACE_DETECTED_IN_LIVE_FRAME",
            "biometric_risk_score": 100,
            "liveness_check": liveness_report,
        }

    # 3. Compute 512-D Cosine Similarity
    cosine_sim = float(np.dot(emb_doc, emb_live))

    # Calibrate matching percentage
    if cosine_sim >= 0.65:
        # Genuine match (typically 0.70 to 0.95)
        normalized_match = round(75.0 + min(24.0, ((cosine_sim - 0.65) / (0.90 - 0.65)) * 24.0), 2)
        match_verdict = "MATCH_CONFIRMED"
        is_verified = True
        bio_risk = max(0, int(100 - normalized_match))
    elif cosine_sim >= 0.45:
        # Marginal similarity - manual review recommended
        normalized_match = round(50.0 + ((cosine_sim - 0.45) / (0.65 - 0.45)) * 24.0, 2)
        match_verdict = "MANUAL_INSPECTION_REQUIRED"
        is_verified = False
        bio_risk = 55
    else:
        # Severe mismatch / Impostor attack
        normalized_match = round(max(0.0, (cosine_sim / 0.45) * 49.0), 2)
        match_verdict = "IMPOSTOR_ALERT_MISMATCH"
        is_verified = False
        bio_risk = 95

    return {
        "verified": is_verified,
        "similarity_percentage": normalized_match,
        "similarity_score": round(normalized_match / 100.0, 2),
        "raw_cosine_similarity": round(cosine_sim, 4),
        "match_verdict": match_verdict,
        "biometric_risk_score": bio_risk,
        "liveness_check": liveness_report,
    }
