"use client";

import { AlertTriangle, ShieldAlert, Lock, XCircle, CheckCircle } from "lucide-react";

export default function CriminalAlertModal({ isOpen, onClose, caseData }) {
  if (!isOpen || !caseData) return null;

  const isFlagged = caseData.watchlist_status === "FLAGGED" || (caseData.reasons && caseData.reasons.some(r => r.includes("RED NOTICE") || r.includes("FLAGGED")));
  const riskScore = caseData.riskScore ?? 100;
  const name = caseData.docData?.find(f => f.key === "name")?.value || "UNKNOWN SUBJECT";
  const docNo = caseData.docData?.find(f => f.key === "docno")?.value || "UNKNOWN";
  const matchDetails = caseData.watchlist_details?.match_details || {};
  const charges = matchDetails.charges || caseData.reasons?.[0] || "Subject flagged for identity fraud and security warrants.";
  const agency = matchDetails.issuing_agency || "INTERPOL Red Notices / SSB Watchlist";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-white border-2 border-red-600 rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden flex flex-col transform transition-all scale-100">
        
        {/* HEADER SIREN BANNER */}
        <div className="bg-red-600 text-white p-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-red-700 border-2 border-red-400 flex items-center justify-center animate-pulse shrink-0">
              <ShieldAlert className="w-7 h-7 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono uppercase tracking-widest bg-red-800 text-red-200 px-2 py-0.5 rounded font-bold">
                  {isFlagged ? "INTERPOL RED NOTICE MATCH" : "HIGH RISK SUBJECT DETECTED"}
                </span>
              </div>
              <h2 className="text-xl font-black tracking-tight mt-0.5">
                CRITICAL SECURITY ALERT
              </h2>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="text-red-200 hover:text-white p-1 rounded-lg hover:bg-red-700 transition-colors"
          >
            <XCircle className="w-6 h-6" />
          </button>
        </div>

        {/* BODY CONTENT */}
        <div className="p-6 space-y-4 text-slate-800">

          {/* SUBJECT DETAILS CARD */}
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between border-b border-red-200 pb-2">
              <span className="text-xs font-bold text-red-800 uppercase tracking-wider">Subject Identity</span>
              <span className="text-sm font-black text-red-600 font-mono">RISK SCORE: {riskScore} / 100</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div>
                <span className="text-slate-500 block text-[10px]">NAME:</span>
                <span className="font-bold text-slate-900 text-sm">{name}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[10px]">DOCUMENT NO:</span>
                <span className="font-bold text-slate-900 text-sm">{docNo}</span>
              </div>
            </div>
          </div>

          {/* CRIMINAL CHARGES & NOTICE DETAILS */}
          <div className="bg-slate-900 text-white rounded-xl p-4 space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between text-red-400 font-bold border-b border-slate-800 pb-1.5">
              <span className="flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-red-500" />
                <span>OFFICIAL WARRANTS & CHARGES</span>
              </span>
              <span className="text-[10px] text-slate-400 font-normal">{agency}</span>
            </div>
            <p className="text-slate-200 text-xs leading-relaxed font-sans pt-1">
              {charges}
            </p>
          </div>

          {/* MANDATORY ACTION */}
          <div className="bg-amber-50 border border-amber-300 rounded-xl p-3.5 flex items-center gap-3">
            <Lock className="w-6 h-6 text-amber-600 shrink-0" />
            <div className="text-xs">
              <span className="font-bold text-amber-900 block">MANDATORY PROTOCOL ACTION:</span>
              <span className="text-amber-800">Gate locked — Detain subject immediately and escalate to senior border officer.</span>
            </div>
          </div>

        </div>

        {/* FOOTER BUTTONS */}
        <div className="bg-slate-100 px-6 py-4 border-t border-slate-200 flex items-center justify-between gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2.5 rounded-xl border border-slate-300 text-slate-700 hover:bg-slate-200 text-xs font-bold transition-colors"
          >
            Dismiss (Operator Override)
          </button>
          <button
            onClick={onClose}
            className="flex-1 px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-extrabold shadow-lg shadow-red-600/30 flex items-center justify-center gap-2 transition-all hover:scale-[1.01]"
          >
            <CheckCircle className="w-4 h-4" />
            <span>CONFIRM DETENTION & ESCALATE</span>
          </button>
        </div>

      </div>
    </div>
  );
}
