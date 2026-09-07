"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Camera, RefreshCw, AlertTriangle, X, Upload, Loader2, ShieldCheck } from "lucide-react";

/**
 * BiometricCameraModal
 *
 * Props:
 *   isOpen    {boolean}
 *   onClose   {() => void}
 *   onCapture {(blob: Blob) => void}  Called with raw JPEG blob — NO backend upload here.
 *                                     Parent owns the validation gate + API call.
 */
export default function BiometricCameraModal({ isOpen, onClose, onCapture }) {
  const videoRef     = useRef(null);
  const streamRef    = useRef(null);
  const fileInputRef = useRef(null);

  const [camState,           setCamState]           = useState("IDLE");
  const [errorMsg,           setErrorMsg]           = useState("");
  const [capturedBlob,       setCapturedBlob]       = useState(null);
  const [capturedPreviewUrl, setCapturedPreviewUrl] = useState(null);

  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
  }, []);

  useEffect(() => () => stopStream(), [stopStream]);

  useEffect(() => {
    if (isOpen) {
      setCamState("IDLE");
      setErrorMsg("");
      setCapturedBlob(null);
      if (capturedPreviewUrl) { URL.revokeObjectURL(capturedPreviewUrl); setCapturedPreviewUrl(null); }
    } else {
      stopStream();
    }
  }, [isOpen]); // eslint-disable-line

  async function startCamera() {
    stopStream(); setErrorMsg(""); setCamState("REQUESTING");
    if (!navigator.mediaDevices?.getUserMedia) {
      setCamState("ERROR"); setErrorMsg("Camera not supported. Upload a photo instead."); return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false,
      });
      streamRef.current = stream;
      setCamState("ACTIVE");
      setTimeout(() => { if (videoRef.current) { videoRef.current.srcObject = stream; videoRef.current.play().catch(() => {}); } }, 80);
    } catch (err) {
      stopStream(); setCamState("ERROR");
      const m = { NotAllowedError: "Permission denied — allow camera access in browser settings.", NotFoundError: "No camera found on this device.", NotReadableError: "Camera in use by another app.", SecurityError: "Camera blocked by security policy." };
      setErrorMsg(m[err.name] || "Unable to access camera.");
    }
  }

  function captureFrame() {
    const v = videoRef.current;
    if (!v?.videoWidth) { setErrorMsg("Video not ready — try again."); return; }
    const c = document.createElement("canvas");
    c.width = v.videoWidth; c.height = v.videoHeight;
    const ctx = c.getContext("2d");
    ctx.translate(c.width, 0); ctx.scale(-1, 1);
    ctx.drawImage(v, 0, 0, c.width, c.height);
    c.toBlob((blob) => {
      if (!blob) { setErrorMsg("Failed to capture frame."); return; }
      if (capturedPreviewUrl) URL.revokeObjectURL(capturedPreviewUrl);
      setCapturedBlob(blob); setCapturedPreviewUrl(URL.createObjectURL(blob));
      setCamState("CAPTURED"); stopStream();
    }, "image/jpeg", 0.92);
  }

  function retake() {
    if (capturedPreviewUrl) { URL.revokeObjectURL(capturedPreviewUrl); setCapturedPreviewUrl(null); }
    setCapturedBlob(null); startCamera();
  }

  function confirmCapture() {
    if (!capturedBlob) return;
    onCapture?.(capturedBlob);
    stopStream(); onClose?.();
  }

  function handleFileSelect(e) {
    const file = e.target.files?.[0]; if (!file) return;
    if (!["image/jpeg", "image/png"].includes(file.type)) { setErrorMsg("Only JPG or PNG supported."); return; }
    if (file.size > 10 * 1024 * 1024) { setErrorMsg("File exceeds 10 MB limit."); return; }
    setErrorMsg("");
    if (capturedPreviewUrl) URL.revokeObjectURL(capturedPreviewUrl);
    setCapturedBlob(file); setCapturedPreviewUrl(URL.createObjectURL(file));
    setCamState("CAPTURED"); stopStream();
  }

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 font-sans">
      <div className="bg-white border border-gray-200 rounded-xl shadow-2xl w-full max-w-md overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-4 py-3 bg-[#04332d] text-white flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Camera className="w-4 h-4 text-emerald-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider">Step 2 — Live Face Capture</h3>
          </div>
          <button onClick={() => { stopStream(); onClose?.(); }} aria-label="Close" className="text-gray-300 hover:text-white transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 flex-1 flex flex-col items-center justify-center">
          <input type="file" ref={fileInputRef} onChange={handleFileSelect} accept="image/jpeg,image/png" className="hidden" />

          {camState === "IDLE" && (
            <div className="flex flex-col items-center text-center py-6 gap-4 w-full">
              <div className="w-16 h-16 rounded-full bg-[#04332d]/10 flex items-center justify-center">
                <Camera className="w-8 h-8 text-[#04332d]" />
              </div>
              <div>
                <p className="text-sm font-bold text-gray-800">Capture Live Selfie</p>
                <p className="text-xs text-gray-500 mt-1 max-w-xs">Position your face and capture a clear photo for biometric verification.</p>
              </div>
              <div className="flex flex-col w-full gap-2">
                <button onClick={startCamera} className="w-full py-2.5 bg-[#04332d] text-white text-xs font-bold rounded-lg hover:bg-[#03241f] transition-all flex items-center justify-center gap-2 shadow-sm">
                  <Camera className="w-4 h-4" /> Start Camera
                </button>
                <button onClick={() => fileInputRef.current?.click()} className="w-full py-2 bg-gray-100 text-gray-700 text-xs font-semibold rounded-lg hover:bg-gray-200 transition-colors flex items-center justify-center gap-1.5">
                  <Upload className="w-3.5 h-3.5" /> Upload Photo Instead
                </button>
              </div>
            </div>
          )}

          {camState === "REQUESTING" && (
            <div className="flex flex-col items-center text-center py-10 gap-3">
              <Loader2 className="w-8 h-8 text-[#04332d] animate-spin" />
              <p className="text-xs font-bold text-gray-700">Requesting camera access…</p>
              <p className="text-[10px] text-gray-400">Please approve the browser permission prompt.</p>
            </div>
          )}

          {camState === "ACTIVE" && (
            <div className="w-full flex flex-col items-center gap-3">
              <div className="relative w-full rounded-lg overflow-hidden bg-black border border-gray-300" style={{ aspectRatio: "4/3" }}>
                <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover scale-x-[-1]" />
                <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                  <div className="w-44 h-56 border-2 border-dashed border-emerald-400/80 rounded-full flex items-center justify-center">
                    <span className="text-[9px] font-bold text-white/80 bg-black/50 px-2 py-0.5 rounded-full">Centre Face</span>
                  </div>
                </div>
              </div>
              <button onClick={captureFrame} className="w-full py-2.5 bg-[#04332d] text-white text-xs font-bold rounded-lg hover:bg-[#03241f] transition-all flex items-center justify-center gap-2 shadow-sm">
                <Camera className="w-4 h-4 text-emerald-400" /> Capture Frame
              </button>
            </div>
          )}

          {camState === "CAPTURED" && capturedPreviewUrl && (
            <div className="w-full flex flex-col items-center gap-3">
              <div className="relative w-full rounded-lg overflow-hidden bg-black border border-gray-300" style={{ aspectRatio: "4/3" }}>
                <img src={capturedPreviewUrl} alt="Selfie preview" className="w-full h-full object-cover" />
                <div className="absolute top-2 left-2 bg-emerald-500 text-white text-[9px] font-bold px-2 py-0.5 rounded shadow">Captured ✓</div>
              </div>
              <div className="grid grid-cols-2 gap-2 w-full">
                <button onClick={retake} className="py-2 bg-gray-100 text-gray-700 text-xs font-bold rounded-lg hover:bg-gray-200 transition-colors flex items-center justify-center gap-1.5">
                  <RefreshCw className="w-3.5 h-3.5" /> Retake
                </button>
                <button onClick={confirmCapture} className="py-2 bg-[#04332d] text-white text-xs font-bold rounded-lg hover:bg-[#03241f] transition-all flex items-center justify-center gap-1.5 shadow-sm">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Use This Photo
                </button>
              </div>
            </div>
          )}

          {camState === "ERROR" && (
            <div className="w-full flex flex-col items-center text-center py-4 gap-3">
              <div className="w-12 h-12 rounded-full bg-red-50 border border-red-200 flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-500" />
              </div>
              <div>
                <p className="text-xs font-bold text-red-700">Camera Error</p>
                <p className="text-[11px] text-gray-600 mt-1 px-2">{errorMsg}</p>
              </div>
              <div className="flex flex-col w-full gap-2">
                <button onClick={startCamera} className="w-full py-2 bg-[#04332d] text-white text-xs font-bold rounded-lg hover:bg-[#03241f] transition-colors flex items-center justify-center gap-1.5">
                  <RefreshCw className="w-3.5 h-3.5" /> Try Again
                </button>
                <button onClick={() => fileInputRef.current?.click()} className="w-full py-2 bg-gray-100 text-gray-700 text-xs font-semibold rounded-lg hover:bg-gray-200 transition-colors flex items-center justify-center gap-1.5">
                  <Upload className="w-3.5 h-3.5" /> Upload Photo Instead
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
