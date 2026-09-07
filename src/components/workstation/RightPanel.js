"use client";
import { useState } from "react";
import { CheckCircle, AlertTriangle, Flag, ThumbsUp, Download, Eye, AlertCircle, Loader2 } from "lucide-react";
import { generatePDFReport } from "@/lib/pdfReportGenerator";
import { addRecordFromCaseData } from "@/lib/auditTrailService";

function RiskColor(level) {
  if (level === "Low")  return { ring: "#10b981", fill: "#10b981", bg: "bg-emerald-50", border: "border-emerald-200", text: "text-emerald-700" };
  if (level === "Medium") return { ring: "#f59e0b", fill: "#f59e0b", bg: "bg-amber-50", border: "border-amber-200", text: "text-amber-700" };
  return { ring: "#ef4444", fill: "#ef4444", bg: "bg-red-50", border: "border-red-200", text: "text-red-700" };
}

function CircleScore({ score, level }) {
  const r = 48, circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const c = RiskColor(level);
  return (
    <div className="relative flex items-center justify-center" style={{ width: 120, height: 120 }}>
      <svg width={120} height={120} viewBox="0 0 120 120" className="-rotate-90">
        <circle cx={60} cy={60} r={r} fill="none" stroke="#e5e7eb" strokeWidth={10} />
        <circle
          cx={60}
          cy={60}
          r={r}
          fill="none"
          stroke={c.fill}
          strokeWidth={10}
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          className="circle-draw"
          style={{ transition: "stroke-dashoffset 1.2s cubic-bezier(0.22,1,0.36,1)" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-black text-gray-800">{score}</span>
        <span className="text-[10px] text-gray-400 font-semibold">/100</span>
      </div>
    </div>
  );
}

export default function RightPanel({
  caseData,
  analysisComplete,
  onEvidenceClick,
  user,
  documentPreviewUrl,
  liveFramePreviewUrl,
  sessionId,
}) {
  const [isGenerating, setIsGenerating] = useState(false);

  if (!analysisComplete || !caseData) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 py-16 px-3">
        <div className="w-14 h-14 rounded-full bg-gray-100 flex items-center justify-center">
          <Eye className="w-6 h-6 text-gray-300" />
        </div>
        <p className="text-xs text-gray-400 text-center">Verification assessment will appear here after document analysis</p>
      </div>
    );
  }

  const { riskScore, riskLevel, riskAction, evidence, whyBars, reasons } = caseData;
  const c = RiskColor(riskLevel);
  const total = evidence?.reduce((s, e) => s + e.score, 0) || 0;
  const riskLabel = riskLevel === "Low" ? "LOW VERIFICATION RISK" : riskLevel === "Medium" ? "SECONDARY VERIFICATION" : "HIGH VERIFICATION RISK";
  const ActionIcon = riskLevel === "Low" ? ThumbsUp : riskLevel === "Medium" ? AlertTriangle : Flag;

  const handleGenerateReport = async () => {
    if (!caseData || isGenerating) return;
    setIsGenerating(true);
    try {
      // 1. Add/update audit record in history
      addRecordFromCaseData(caseData, user, sessionId);

      // 2. Generate downloadable PDF
      await generatePDFReport(caseData, user, documentPreviewUrl, liveFramePreviewUrl, sessionId);
    } catch (err) {
      console.error("Failed to generate PDF report:", err);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex flex-col gap-3 font-sans">
      {/* Score Card */}
      <div className={`bg-white border ${c.border} rounded-lg shadow-sm p-4 fade-up`}>
        <p className="text-[9px] font-bold text-[#04332d] tracking-widest uppercase mb-3">Verification Assessment</p>
        <div className="flex flex-col items-center gap-2 mb-3">
          <CircleScore score={riskScore} level={riskLevel} />
          <div className={`text-[11px] font-bold ${c.text} text-center`}>{riskLabel}</div>
        </div>
        <div className="flex items-center gap-0.5 mb-3">
          {["Low", "Medium", "High"].map((l) => (
            <div
              key={l}
              className={`h-1.5 rounded-full flex-1 ${
                l === riskLevel ? (l === "Low" ? "bg-emerald-500" : l === "Medium" ? "bg-amber-400" : "bg-red-500") : "bg-gray-200"
              }`}
            />
          ))}
        </div>
        <div className="flex justify-between text-[8px] text-gray-400 mb-3">
          <span>LOW</span><span>MEDIUM</span><span>HIGH</span>
        </div>
        <div className={`flex items-start gap-2 p-2.5 rounded-lg ${c.bg} border ${c.border}`}>
          <ActionIcon className={`w-3.5 h-3.5 shrink-0 mt-0.5 ${c.text}`} />
          <p className={`text-[10px] font-semibold ${c.text}`}>{riskAction}</p>
        </div>

        {/* Backend Risk Reasons */}
        {reasons && reasons.length > 0 && (
          <div className="mt-3 pt-2.5 border-t border-gray-100">
            <p className="text-[9px] font-bold text-gray-500 uppercase mb-1.5">Risk Factors & Reasons</p>
            <ul className="space-y-1">
              {reasons.map((r, i) => (
                <li key={i} className="text-[10px] text-gray-600 flex items-start gap-1.5">
                  <AlertCircle className="w-3 h-3 text-amber-500 shrink-0 mt-0.5" />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Evidence Breakdown */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-3 fade-up">
        <p className="text-[9px] font-bold text-[#04332d] tracking-widest uppercase mb-2">Evidence Breakdown</p>
        <p className="text-[8px] text-gray-400 mb-2">Click to highlight document region</p>
        <div className="space-y-0.5">
          {evidence?.map((ev) => (
            <button
              key={ev.label}
              onClick={() => onEvidenceClick?.(ev.label)}
              className="w-full flex items-center gap-2 group hover:bg-gray-50 rounded px-1 py-1 transition-colors text-left"
            >
              <span className="text-[10px] text-gray-500 w-28 shrink-0 group-hover:text-[#04332d] transition-colors truncate">
                {ev.label}
              </span>
              <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#04332d] rounded-full bar-fill"
                  style={{ width: `${Math.max(4, (ev.score / Math.max(riskScore, 1)) * 100)}%` }}
                />
              </div>
              <span className="text-[10px] font-bold text-gray-600 w-6 text-right shrink-0">+{ev.score}</span>
            </button>
          ))}
        </div>
        <div className="mt-2 pt-2 border-t border-gray-100 flex justify-between items-center">
          <span className="text-[10px] text-gray-500 font-semibold">Total Score</span>
          <span className="text-sm font-black text-gray-800">{total}</span>
        </div>
      </div>


      {/* Officer Actions */}
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-3 space-y-2 fade-up">
        <p className="text-[9px] font-bold text-[#04332d] tracking-widest uppercase mb-2">Officer Actions</p>
        {riskLevel === "Low" && (
          <button className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-[#04332d] text-white text-xs font-bold hover:bg-[#03241f] active:scale-[0.98] transition-all shadow-sm">
            <CheckCircle className="w-3.5 h-3.5" />
            Proceed — e-Gate Unlocked
          </button>
        )}
        {riskLevel === "Medium" && (
          <button className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-amber-500 text-white text-xs font-bold hover:bg-amber-600 active:scale-[0.98] transition-all shadow-sm">
            <AlertTriangle className="w-3.5 h-3.5" />
            Refer to Senior Officer
          </button>
        )}
        {riskLevel === "High" && (
          <button className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-red-600 text-white text-xs font-bold hover:bg-red-700 active:scale-[0.98] transition-all shadow-sm">
            <Flag className="w-3.5 h-3.5" />
            Detain &amp; Escalate
          </button>
        )}
        <button
          onClick={handleGenerateReport}
          disabled={isGenerating}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-lg border-2 border-[#04332d] text-[#04332d] text-[10px] font-bold hover:bg-[#04332d]/5 active:scale-[0.98] transition-all disabled:opacity-50"
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-3 h-3 animate-spin" />
              Generating PDF Report…
            </>
          ) : (
            <>
              <Download className="w-3 h-3" />
              Generate Report
            </>
          )}
        </button>
      </div>
    </div>
  );
}
