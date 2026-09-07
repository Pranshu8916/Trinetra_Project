/**
 * Trinetra API Layer
 * Centralizes all HTTP calls to the FastAPI backend with environment-configurable base URL,
 * central token handling, robust error handling, and timeout support.
 */

const browserHost = typeof window !== "undefined" ? window.location.hostname : "127.0.0.1";
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || `http://${browserHost}:8000`;

// ─── ApiError Class ───────────────────────────────────────────────
export class ApiError extends Error {
  constructor(message, { status = null, detail = "", isNetworkError = false, isTimeout = false } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.isNetworkError = isNetworkError;
    this.isTimeout = isTimeout;
    this.isUnauthorized = status === 401;
    this.isForbidden = status === 403;
    this.isNotFound = status === 404;
    this.isValidationError = status === 400 || status === 422;
    this.isServerError = status !== null && status >= 500;
  }
}

// ─── Auth error listeners ─────────────────────────────────────────
const authErrorListeners = new Set();
export function subscribeAuthError(listener) {
  authErrorListeners.add(listener);
  return () => authErrorListeners.delete(listener);
}

function notifyAuthError() {
  clearToken();
  clearUser();
  authErrorListeners.forEach((fn) => {
    try { fn(); } catch (e) { console.error("Auth listener error:", e); }
  });
}

// ─── Token helpers ────────────────────────────────────────────────
export function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("trinetra_token");
}
export function setToken(t) { localStorage.setItem("trinetra_token", t); }
export function clearToken() { localStorage.removeItem("trinetra_token"); }
export function getUser() {
  if (typeof window === "undefined") return null;
  try { return JSON.parse(localStorage.getItem("trinetra_user")); } catch { return null; }
}
export function setUser(u) { localStorage.setItem("trinetra_user", JSON.stringify(u)); }
export function clearUser() { localStorage.removeItem("trinetra_user"); }

// ─── Human readable error formatter ─────────────────────────────
function formatErrorMessage(status, detail, isNetworkError, isTimeout) {
  if (isNetworkError) return "Backend server is unreachable. Please check if the backend service is running.";
  if (isTimeout) return "Request timed out. Please check your connection and try again.";
  if (status === 401) return typeof detail === "string" ? detail : "Authentication required or session expired.";
  if (status === 403) return typeof detail === "string" ? detail : "Access denied. You do not have permission for this action.";
  if (status === 404) return typeof detail === "string" ? detail : "The requested resource was not found.";
  if (status === 409) return typeof detail === "string" ? detail : "A conflict occurred with the requested resource.";
  if (status === 422 || status === 400) {
    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
    }
    return typeof detail === "string" ? detail : "Invalid request data provided.";
  }
  if (status === 429) return "Too many requests. Please try again in a few moments.";
  if (status && status >= 500) return typeof detail === "string" ? detail : "Backend server error. Please try again later.";
  return typeof detail === "string" ? detail : `Request failed with status code ${status}`;
}

// ─── Core fetch wrapper ───────────────────────────────────────────
async function apiFetch(path, { method = "GET", body, token, isFormData, timeoutMs = 15000 } = {}) {
  const headers = {};
  const tok = token || getToken();
  if (tok) headers["Authorization"] = `Bearer ${tok}`;
  if (!isFormData) headers["Content-Type"] = "application/json";

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  let res;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: isFormData ? body : body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      const msg = formatErrorMessage(null, "", false, true);
      throw new ApiError(msg, { isTimeout: true });
    }
    const msg = formatErrorMessage(null, "", true, false);
    throw new ApiError(msg, { isNetworkError: true });
  } finally {
    clearTimeout(timeoutId);
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      detail = j.detail !== undefined ? j.detail : j.message || detail;
    } catch {}

    if (res.status === 401) {
      notifyAuthError();
    }

    const humanMsg = formatErrorMessage(res.status, detail, false, false);
    throw new ApiError(humanMsg, { status: res.status, detail });
  }

  return res.json();
}

// ─── Auth APIs ────────────────────────────────────────────────────
export async function apiLogin(username, password) {
  return apiFetch("/api/auth/login", { method: "POST", body: { username, password } });
}

export async function apiRegister(username, password, role = "verifier") {
  return apiFetch("/api/users", { method: "POST", body: { username, password, role } });
}

export async function apiMe() {
  return apiFetch("/api/protected/me");
}

export async function apiHealth() {
  return apiFetch("/api/health");
}

// ─── Verification APIs ─────────────────────────────────────────────
export async function apiCreateSession(subjectName, documentType) {
  return apiFetch("/api/verification/sessions", {
    method: "POST",
    body: { subject_name: subjectName, document_type: documentType },
  });
}

export async function apiGetSession(sessionId) {
  return apiFetch(`/api/verification/sessions/${sessionId}`);
}

export async function apiUploadDocument(sessionId, fileBlob, filename = "document.png") {
  const fd = new FormData();
  fd.append("file", fileBlob, filename);
  return apiFetch(`/api/verification/sessions/${sessionId}/document`, {
    method: "POST",
    body: fd,
    isFormData: true,
  });
}

export async function apiProcessDocument(documentId) {
  return apiFetch(`/api/verification/documents/${documentId}/process`, { method: "POST" });
}

export async function apiGetDocumentResult(documentId) {
  return apiFetch(`/api/verification/documents/${documentId}/result`);
}

export async function apiUploadBiometric(sessionId, fileBlob, filename = "selfie.jpg") {
  const fd = new FormData();
  fd.append("file", fileBlob, filename);
  return apiFetch(`/api/verification/sessions/${sessionId}/biometric`, {
    method: "POST",
    body: fd,
    isFormData: true,
  });
}

export async function apiVerifySession(sessionId) {
  return apiFetch(`/api/verification/sessions/${sessionId}/verify`, { method: "POST" });
}

export async function apiGetResult(sessionId) {
  return apiFetch(`/api/verification/sessions/${sessionId}/result`);
}

/**
 * Single-shot document screening.
 *
 * Sends both images in one multipart/form-data POST to the new unified
 * /api/v1/screen-document endpoint and returns the standardised risk JSON.
 *
 * Response shape:
 * {
 *   status:         "success",
 *   report_id:      "RPT-XXXXXXXX",
 *   risk_score:     number (0–100),
 *   risk_level:     "Low" | "Medium" | "High",
 *   decision:       "Clean" | "Suspicious" | "Fraud/Impostor",
 *   action:         string,
 *   reasons:        string[],
 *   extracted_data: { name, document_number, document_type, date_of_birth,
 *                     date_of_issue, date_of_expiry, nationality, gender },
 *   ai_confidence:  { ocr_confidence, document_authenticity, face_similarity,
 *                     liveness_score, deepfake_score },
 *   is_mock:        boolean,
 *   screened_at:    ISO-8601 string,
 * }
 *
 * @param {Blob} passportBlob - Passport or identity document image blob
 * @param {Blob} liveFrameBlob - Live webcam selfie frame blob
 * @param {string} [passportFilename="passport.png"]
 * @param {string} [liveFilename="selfie.jpg"]
 */
export async function apiScreenDocument(
  passportBlob,
  liveFrameBlob,
  passportFilename = "passport.png",
  liveFilename = "selfie.jpg",
) {
  const fd = new FormData();
  fd.append("passport_image", passportBlob, passportFilename);
  fd.append("live_frame", liveFrameBlob, liveFilename);
  return apiFetch("/api/v1/screen-document", {
    method: "POST",
    body: fd,
    isFormData: true,
    timeoutMs: 60_000, // AI pipeline can take 10-30s on real images
  });
}

// ─── Image generators (canvas-based, runs in browser) ─────────────
function canvasToBlob(canvas, type = "image/png") {
  return new Promise((res) => canvas.toBlob(res, type, 0.92));
}

/**
 * Generates a synthetic identity document image on a canvas.
 * caseId: 1 = Genuine Passport, 2 = Modified DoB, 3 = Photo+MRZ Manipulation
 */
export async function generateDocumentImage(caseId) {
  const canvas = document.createElement("canvas");
  canvas.width = 900;
  canvas.height = 580;
  const ctx = canvas.getContext("2d");

  const cases = {
    1: {
      country: "COMMONWEALTH OF AUSTRALIA",
      docType: "PASSPORT",
      name: "JAMES ANDERSON",
      docNo: "AU4567890",
      dob: "22/08/1985",
      doi: "09/03/2021",
      doe: "09/03/2031",
      nationality: "AUS",
      gender: "MALE",
      mrz1: "P<AUSANDERSON<<JAMES<<<<<<<<<<<<<<<<<<<<<<<",
      mrz2: "AU45678907AUS8508225M3103094<<<<<<<<<<<<00",
    },
    2: {
      country: "REPUBLIC OF INDIA",
      docType: "PASSPORT",
      name: "RAHUL KUMAR",
      docNo: "P12345678",
      dob: "24/11/1992", // Modified from actual
      doi: "10/01/2020",
      doe: "11/06/2034",
      nationality: "IND",
      gender: "MALE",
      mrz1: "P<INDKUMAR<<RAHUL<<<<<<<<<<<<<<<<<<<<<<<<",
      mrz2: "P123456789IND9211244M3406119<<<<<<<<<<<<06",
    },
    3: {
      country: "REPUBLIC OF GREAT BRITAIN",
      docType: "PASSPORT",
      name: "SARAH MITCHELL",
      docNo: "GB9876543",
      dob: "14/03/1992",
      doi: "22/10/2019",
      doe: "21/10/2029",
      nationality: "GBR",
      gender: "FEMALE",
      mrz1: "P<GBRMITCHELL<<SARAH<<<<<<<<<<<<<<<<<<<<<<",
      mrz2: "GB98765437GBR9203147F2910219<<<<<<<<<<<<08",
    },
  };

  const d = cases[caseId] || cases[1];

  // Background gradient
  const grad = ctx.createLinearGradient(0, 0, 900, 580);
  grad.addColorStop(0, "#04332d");
  grad.addColorStop(1, "#0b5f54");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 900, 580);

  // Concentric circle watermark
  ctx.globalAlpha = 0.06;
  for (let r = 60; r <= 320; r += 50) {
    ctx.beginPath();
    ctx.arc(450, 290, r, 0, Math.PI * 2);
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 1;
    ctx.stroke();
  }
  ctx.globalAlpha = 1;

  // Border
  ctx.strokeStyle = "rgba(255,255,255,0.3)";
  ctx.lineWidth = 2;
  ctx.strokeRect(12, 12, 876, 556);

  // Photo placeholder (left region)
  ctx.fillStyle = "rgba(235,190,155,0.9)";
  ctx.fillRect(36, 104, 216, 273);
  ctx.fillStyle = "rgba(40,40,40,0.7)";
  ctx.beginPath();
  ctx.ellipse(144, 215, 68, 80, 0, 0, Math.PI * 2);
  ctx.fill();
  // Photo border frame for case 3 (indicates manipulation area)
  if (caseId === 3) {
    ctx.strokeStyle = "#ef4444";
    ctx.lineWidth = 3;
    ctx.setLineDash([6, 3]);
    ctx.strokeRect(36, 104, 216, 273);
    ctx.setLineDash([]);
  }

  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 11px 'Arial'";
  ctx.globalAlpha = 0.5;
  ctx.fillText(d.country, 280, 52);
  ctx.globalAlpha = 1;

  ctx.font = "bold 28px 'Arial'";
  ctx.fillStyle = "#ffffff";
  ctx.fillText(d.docType, 280, 88);

  // Field rows
  const fields = [
    ["Surname", d.name.split(" ")[1] || d.name, 280, 135],
    ["Given Name", d.name.split(" ")[0], 280, 185],
    ["Doc No", d.docNo, 280, 235],
    ["Date of Birth", d.dob, 280, 285],
    ["Nationality", d.nationality, 280, 335],
    ["Gender", d.gender, 540, 285],
    ["Date of Issue", d.doi, 540, 235],
    ["Expiry Date", d.doe, 540, 335],
  ];

  fields.forEach(([label, value, x, y]) => {
    ctx.font = "bold 12px 'Arial'";
    ctx.fillStyle = "rgba(255,255,255,0.7)";
    ctx.fillText(label.toUpperCase() + ":", x, y - 14);
    ctx.font = "bold 16px 'Courier New', monospace";
    ctx.fillStyle = (caseId === 2 && label === "Date of Birth") ? "#fbbf24" : "#ffffff";
    ctx.fillText(value, x, y);
  });

  // MRZ lines at bottom
  ctx.fillStyle = "#000000";
  ctx.fillRect(15, 470, 870, 95);
  ctx.font = "bold 16px 'Courier New', monospace";
  ctx.fillStyle = "#ffffff";
  ctx.fillText(d.mrz1, 25, 508);
  ctx.fillText(d.mrz2, 25, 545);

  return canvasToBlob(canvas, "image/png");
}

/**
 * Generates a synthetic selfie image on a canvas.
 */
export async function generateSelfieImage(caseId) {
  const canvas = document.createElement("canvas");
  canvas.width = 300;
  canvas.height = 300;
  const ctx = canvas.getContext("2d");

  // For case 3, use an impostor face (different color/geometry)
  if (caseId === 3) {
    ctx.fillStyle = "#2d7a45";
    ctx.fillRect(0, 0, 300, 300);
    ctx.fillStyle = "rgba(200,200,200,0.8)";
    ctx.beginPath();
    ctx.ellipse(100, 90, 60, 70, 0, 0, Math.PI * 2);
    ctx.fill();
  } else {
    // Matching face
    ctx.fillStyle = "#ebba9b";
    ctx.fillRect(0, 0, 300, 300);
    ctx.fillStyle = "rgba(40,40,40,0.8)";
    ctx.beginPath();
    ctx.ellipse(150, 150, 80, 95, 0, 0, Math.PI * 2);
    ctx.fill();
    // Eyes
    ctx.fillStyle = "#ffffff";
    ctx.beginPath(); ctx.ellipse(125, 130, 12, 8, 0, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.ellipse(175, 130, 12, 8, 0, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = "#2c1810";
    ctx.beginPath(); ctx.arc(125, 130, 5, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.arc(175, 130, 5, 0, Math.PI * 2); ctx.fill();
  }

  return canvasToBlob(canvas, "image/jpeg");
}
