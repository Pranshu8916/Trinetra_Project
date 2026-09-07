"use client";

import { useRef } from "react";
import {
  Upload, Camera, CheckCircle, Loader2, ScanLine,
  FileText, RefreshCw, ImagePlus, AlertCircle, Lock,
  UserCheck, ShieldCheck,
} from "lucide-react";

/**
 * LeftPanel — Sequential 2-step upload gate
 *
 * Props:
 *   documentBlob      {Blob|null}       Step 1 state
 *   documentPreviewUrl{string|null}
 *   documentFilename  {string|null}
 *   onSelectDocument  {(file: File)=>void}
 *   onClearDocument   {()=>void}
 *
 *   liveFrameBlob     {Blob|null}       Step 2 state
 *   liveFramePreviewUrl{string|null}
 *   onOpenCamera      {()=>void}
 *   onClearLiveFrame  {()=>void}
 *
 *   canScreen         {boolean}         true when BOTH blobs present
 *   isScreening       {boolean}
 *   onScreen          {()=>void}        fires the API
 *
 *   screeningError    {string|null}
 */
export default function LeftPanel({
  documentBlob,
  documentPreviewUrl,
  documentFilename,
  onSelectDocument,
  onClearDocument,
  liveFrameBlob,
  liveFramePreviewUrl,
  onOpenCamera,
  onClearLiveFrame,
  canScreen,
  isScreening,
  onScreen,
  screeningError,
}) {
  const fileInputRef = useRef(null);

  function handleFileChange(e) {
    const file = e.target.files?.[0];
    if (file) { onSelectDocument(file); e.target.value = ""; }
  }

  const step1Done = !!documentBlob;
  const step2Done = !!liveFrameBlob;
  const isPdf = documentFilename?.endsWith(".pdf");

  return (
    <div className="flex flex-col gap-3 font-sans">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/jpeg,image/png,application/pdf"
        className="hidden"
        aria-label="Select identity document"
      />

      {/* ── Step 1: Document Upload ─────────────────────────────── */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
        {/* Header */}
        <div className="px-3 py-2 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-black shrink-0 ${step1Done ? "bg-emerald-500 text-white" : "bg-[#04332d] text-white"}`}>
              {step1Done ? <CheckCircle className="w-3 h-3" /> : "1"}
            </span>
            <h2 className="text-[10px] font-bold text-[#04332d] tracking-widest uppercase">Document Upload</h2>
          </div>
          <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${step1Done
            ? "bg-emerald-50 text-emerald-700 border-emerald-200"
            : "bg-gray-100 text-gray-400 border-gray-200"
            }`}>
            {step1Done ? "Ready ✓" : "Required"}
          </span>
        </div>

        <div className="p-3">
          {/* Preview area */}
          <div
            className={`relative rounded-md border-2 overflow-hidden transition-all ${step1Done && documentPreviewUrl && !isPdf
              ? "border-[#04332d]/40 bg-gray-900"
              : step1Done && isPdf
                ? "border-[#04332d]/40 bg-gradient-to-br from-[#04332d] to-[#0b5f54]"
                : "border-dashed border-gray-300 bg-gray-50/60 hover:bg-gray-50"
              }`}
            style={{ height: 160 }}
          >
            {step1Done && documentPreviewUrl && !isPdf ? (
              <div className="relative w-full h-full group">
                <img src={documentPreviewUrl} alt="Document preview" className="w-full h-full object-contain bg-black/40" />
                <div className="absolute bottom-0 inset-x-0 bg-black/70 backdrop-blur-sm p-2 text-white text-[10px] flex items-center justify-between">
                  <p className="font-bold truncate pr-2">{documentFilename}</p>
                  <button onClick={onClearDocument} className="text-[9px] bg-white/20 hover:bg-white/30 font-semibold px-2 py-0.5 rounded shrink-0">Clear</button>
                </div>
              </div>
            ) : step1Done && isPdf ? (
              <div className="absolute inset-0 p-4 text-white flex flex-col justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-7 h-7 text-amber-300 shrink-0" />
                  <div>
                    <span className="text-[8px] bg-amber-400/20 border border-amber-400/40 text-amber-300 font-bold px-1.5 py-0.5 rounded uppercase">PDF</span>
                    <p className="text-xs font-bold truncate mt-1">{documentFilename}</p>
                  </div>
                </div>
                <button onClick={onClearDocument} className="self-end text-[9px] bg-white/20 hover:bg-white/30 font-semibold px-2 py-1 rounded flex items-center gap-1">
                  <RefreshCw className="w-3 h-3" /> Replace
                </button>
              </div>
            ) : (
              <div onClick={() => fileInputRef.current?.click()} className="absolute inset-0 flex flex-col items-center justify-center gap-2 cursor-pointer p-4 group">
                <div className="w-10 h-10 rounded-full bg-gray-100 group-hover:bg-[#04332d]/10 flex items-center justify-center transition-colors">
                  <Upload className="w-4 h-4 text-gray-400 group-hover:text-[#04332d]" />
                </div>
                <div className="text-center">
                  <p className="text-xs font-bold text-gray-700 group-hover:text-[#04332d]">Upload Identity Document</p>
                  <p className="text-[9px] text-gray-400 mt-0.5">JPG, PNG or PDF · Max 10 MB</p>
                </div>
              </div>
            )}
          </div>

          {/* Action buttons */}
          <div className="mt-2 grid grid-cols-2 gap-2">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center justify-center gap-1.5 py-2 rounded border border-gray-200 text-xs font-semibold text-gray-700 hover:border-[#04332d] hover:text-[#04332d] transition-all bg-gray-50/50"
            >
              <ImagePlus className="w-3.5 h-3.5" />
              {step1Done ? "Change" : "Choose File"}
            </button>
            <button
              onClick={onClearDocument}
              disabled={!step1Done}
              className={`flex items-center justify-center gap-1.5 py-2 rounded border text-xs font-semibold transition-all ${step1Done
                ? "border-gray-200 text-gray-600 hover:border-red-400 hover:text-red-600 bg-gray-50/50"
                : "border-gray-100 text-gray-300 cursor-not-allowed bg-gray-50"
                }`}
            >
              <RefreshCw className="w-3.5 h-3.5" /> Clear
            </button>
          </div>
        </div>
      </div>

      {/* ── Step 2: Live Face Capture ───────────────────────────── */}
      <div className={`bg-white border rounded-lg shadow-sm overflow-hidden transition-all ${step1Done ? "border-gray-200" : "border-gray-100 opacity-50 pointer-events-none"
        }`}>
        {/* Header */}
        <div className="px-3 py-2 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-black shrink-0 ${step2Done ? "bg-emerald-500 text-white" : step1Done ? "bg-[#04332d] text-white" : "bg-gray-300 text-white"
              }`}>
              {step2Done ? <CheckCircle className="w-3 h-3" /> : step1Done ? "2" : <Lock className="w-2.5 h-2.5" />}
            </span>
            <h2 className="text-[10px] font-bold text-[#04332d] tracking-widest uppercase">Live Face Capture</h2>
          </div>
          <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full border ${step2Done
            ? "bg-emerald-50 text-emerald-700 border-emerald-200"
            : step1Done
              ? "bg-blue-50 text-blue-600 border-blue-200"
              : "bg-gray-100 text-gray-400 border-gray-200"
            }`}>
            {step2Done ? "Ready ✓" : step1Done ? "Required" : "Locked"}
          </span>
        </div>

        <div className="p-3">
          {/* Preview / placeholder */}
          <div
            className={`relative rounded-md border-2 overflow-hidden transition-all ${step2Done && liveFramePreviewUrl
              ? "border-emerald-400/40 bg-gray-900"
              : "border-dashed border-gray-300 bg-gray-50/60"
              }`}
            style={{ height: 140 }}
          >
            {step2Done && liveFramePreviewUrl ? (
              <div className="relative w-full h-full">
                <img src={liveFramePreviewUrl} alt="Live selfie preview" className="w-full h-full object-contain bg-black/40" />
                <div className="absolute top-2 left-2 bg-emerald-500 text-white text-[9px] font-bold px-2 py-0.5 rounded shadow">Live ✓</div>
                <div className="absolute bottom-0 inset-x-0 bg-black/70 p-2 flex items-center justify-between">
                  <div className="flex items-center gap-1.5 text-white">
                    <UserCheck className="w-3 h-3 text-emerald-400" />
                    <span className="text-[10px] font-bold">Biometric Captured</span>
                  </div>
                  <button onClick={onClearLiveFrame} className="text-[9px] bg-white/20 hover:bg-white/30 text-white font-semibold px-2 py-0.5 rounded">Retake</button>
                </div>
              </div>
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
                <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
                  <Camera className="w-4 h-4 text-gray-400" />
                </div>
                <p className="text-[9px] text-gray-400 text-center px-4">
                  {step1Done ? "Open camera to capture live selfie" : "Complete Step 1 first"}
                </p>
              </div>
            )}
          </div>

          {/* Open camera button */}
          <button
            onClick={onOpenCamera}
            disabled={!step1Done}
            className="mt-2 w-full flex items-center justify-center gap-1.5 py-2 rounded border border-[#04332d]/30 text-xs font-semibold text-[#04332d] hover:bg-[#04332d]/5 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Camera className="w-3.5 h-3.5" />
            {step2Done ? "Retake Selfie" : "Open Camera"}
          </button>
        </div>
      </div>

      {/* ── Step 3: Validation Gate — Run Screening ─────────────── */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-3">
        {/* Checklist */}
        <div className="flex flex-col gap-1 mb-3">
          <div className={`flex items-center gap-2 text-[10px] font-semibold ${step1Done ? "text-emerald-700" : "text-gray-400"}`}>
            {step1Done ? <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0" /> : <AlertCircle className="w-3.5 h-3.5 shrink-0" />}
            Document image uploaded
          </div>
          <div className={`flex items-center gap-2 text-[10px] font-semibold ${step2Done ? "text-emerald-700" : "text-gray-400"}`}>
            {step2Done ? <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0" /> : <AlertCircle className="w-3.5 h-3.5 shrink-0" />}
            Live face captured
          </div>
        </div>

        {/* Gate button */}
        <button
          onClick={onScreen}
          disabled={!canScreen || isScreening}
          className={`w-full flex items-center justify-center gap-2 py-3 rounded-md text-xs font-bold transition-all shadow-sm active:scale-[0.98] ${canScreen && !isScreening
            ? "bg-[#04332d] text-white hover:bg-[#03241f] cursor-pointer"
            : "bg-gray-200 text-gray-400 cursor-not-allowed"
            }`}
          title={!step1Done ? "Upload a document first" : !step2Done ? "Capture your selfie first" : "Run AI Screening"}
        >
          {isScreening ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Running AI Screening…</>
          ) : canScreen ? (
            <><ShieldCheck className="w-4 h-4" /> Run AI Screening</>
          ) : (
            <><ScanLine className="w-4 h-4" /> Complete Steps 1 &amp; 2 First</>
          )}
        </button>

        {!canScreen && !isScreening && (
          <p className="text-[9px] text-gray-400 text-center mt-1.5">
            {!step1Done ? "Upload a passport or ID document to begin" : "Capture your live selfie to unlock screening"}
          </p>
        )}

        {/* API Error */}
        {screeningError && (
          <div className="mt-2 p-2.5 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
            <p className="text-[10px] font-semibold text-red-700 leading-tight">{screeningError}</p>
          </div>
        )}
      </div>
    </div>
  );
}
