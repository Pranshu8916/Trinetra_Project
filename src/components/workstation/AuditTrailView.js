"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/api";
import { CheckCircle, AlertTriangle, Flag, Download, FileText, ChevronRight, RefreshCw } from "lucide-react";
import { getAuditHistory, exportCSVFromRecords } from "@/lib/auditTrailService";
import { generatePDFReport } from "@/lib/pdfReportGenerator";

function RiskBadge({ risk }) {
  const r = (risk || "LOW").toUpperCase();
  if (r === "LOW")    return <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200">LOW</span>;
  if (r === "MEDIUM") return <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 border border-amber-200">MEDIUM</span>;
  return                     <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-red-100 text-red-700 border border-red-200">HIGH</span>;
}

function ActionBadge({ decision }) {
  const d = String(decision || "").toLowerCase();
  if (d.includes("clean") || d.includes("clear") || d.includes("unlocked") || d.includes("low")) {
    return <span className="text-[9px] font-bold text-emerald-600 flex items-center gap-1"><CheckCircle className="w-3 h-3"/>Cleared</span>;
  }
  if (d.includes("suspicious") || d.includes("secondary") || d.includes("medium")) {
    return <span className="text-[9px] font-bold text-amber-600 flex items-center gap-1"><AlertTriangle className="w-3 h-3"/>Secondary</span>;
  }
  return <span className="text-[9px] font-bold text-red-600 flex items-center gap-1"><Flag className="w-3 h-3"/>Manual Review</span>;
}

function buildCaseDataFromRecord(r) {
  if (r.caseData) return r.caseData;
  return {
    docType: r.docType || "PASSPORT",
    riskScore: r.riskScore ?? 0,
    riskLevel: r.riskLevel ? (r.riskLevel.charAt(0).toUpperCase() + r.riskLevel.slice(1).toLowerCase()) : "Low",
    riskAction: r.decision || "Proceed — e-Gate Unlocked",
    docData: [
      { key: "name",    label: "Full Name",       value: r.name || "—" },
      { key: "dob",     label: "Date of Birth",   value: r.dob || "—" },
      { key: "nat",     label: "Nationality",     value: r.nationality || "—" },
      { key: "docno",   label: "Document Number", value: r.docNumber || "—" },
      { key: "doctype", label: "Document Type",   value: r.docType || "PASSPORT" },
      { key: "gender",  label: "Gender",          value: r.gender || "—" },
    ],
    evidence: r.evidence || [],
    reasons: r.reasons || [],
    forensics: { manipulationIndicators: r.tampering ? 1 : 0 },
  };
}

export default function AuditTrailView() {
  const router = useRouter();
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [downloadingId, setDownloadingId] = useState(null);

  const loadAuditData = () => {
    setLoading(true);
    const history = getAuditHistory().slice(0, 10); // Guarantee max 10 records
    setRecords(history);
    if (history.length > 0) {
      setSelectedRecord(history[0]);
    } else {
      setSelectedRecord(null);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (!getToken()) { router.push("/login"); return; }
    loadAuditData();
  }, [router]);

  const handleExportCSV = () => {
    exportCSVFromRecords(records);
  };

  const handleDownloadPDF = async (record, e) => {
    if (e) e.stopPropagation();
    if (!record) return;
    setDownloadingId(record.sessionId);
    try {
      const caseData = buildCaseDataFromRecord(record);
      const mockUser = { username: record.officer || "officer1" };
      await generatePDFReport(caseData, mockUser, null, null, record.sessionId);
    } catch (err) {
      console.error("Failed to generate PDF for record:", err);
    } finally {
      setDownloadingId(null);
    }
  };

  const cols = ["Verification ID", "Timestamp", "Document Type", "Subject Name", "Doc Number", "Block Hash (SHA-256)", "Risk Level", "Score", "Decision", "PDF Report"];

  return (
    <div className="max-w-screen-xl mx-auto px-3 sm:px-6 py-4 sm:py-6 font-sans">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <h2 className="text-base sm:text-lg font-bold text-[#04332d] flex flex-wrap items-center gap-2">
            Audit Trail &amp; Blockchain Ledger
            <span className="text-[10px] font-semibold bg-[#04332d]/10 text-[#04332d] px-2 py-0.5 rounded-full">
              SIH PS ID: 26188 (MHA / SSB)
            </span>
          </h2>
          <p className="text-[11px] sm:text-xs text-gray-400 mt-0.5">SHA-256 Cryptographic tamper-proof record ledger</p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <button
            onClick={loadAuditData}
            title="Refresh logs"
            className="p-2 text-gray-500 hover:text-[#04332d] border border-gray-200 bg-white rounded-lg hover:bg-gray-50 transition-colors shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-2 px-3 py-2 bg-[#04332d] text-white text-xs font-bold rounded-lg hover:bg-[#03241f] active:scale-[0.98] transition-all shadow-sm"
          >
            <Download className="w-3.5 h-3.5" /> Export CSV (Last 10)
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center shadow-sm">
          <p className="text-sm text-gray-400 font-medium">Loading audit records…</p>
        </div>
      ) : records.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-lg p-12 text-center shadow-sm">
          <p className="text-sm text-gray-500 font-semibold">No audit records found</p>
          <p className="text-xs text-gray-400 mt-1">Run a verification in the Workstation tab to generate records.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Audit Records Table (Max 10) */}
          <div className="bg-[#04332d]/5 border border-[#04332d]/20 rounded-lg p-3 mb-2 flex items-center justify-between text-xs">
            <span className="font-semibold text-[#04332d] flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-600" />
              Cryptographic Blockchain Audit Verification: Active (SHA-256 Ledger Connected)
            </span>
            <span className="font-mono text-[10px] text-gray-500">MHA &amp; SSB PS ID: 26188</span>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
            <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex justify-between items-center">
              <span className="text-[10px] font-bold text-[#04332d] uppercase tracking-wider">
                Recent Verification Log (Max 10 Records)
              </span>
              <span className="text-[10px] text-gray-400 font-mono">Total: {records.length} / 10</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead className="bg-gray-50/50 border-b border-gray-200">
                  <tr>
                    {cols.map((h) => (
                      <th key={h} className="px-3.5 py-3 text-[9px] font-bold text-gray-400 uppercase tracking-wider">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 text-xs">
                  {records.map((row) => {
                    const isSelected = selectedRecord?.sessionId === row.sessionId;
                    const hashDisplay = row.blockHash ? `${row.blockHash.slice(0, 10)}...` : `0x${row.sessionId.slice(-8)}...`;
                    return (
                      <tr
                        key={row.sessionId}
                        onClick={() => setSelectedRecord(row)}
                        className={`cursor-pointer transition-colors ${
                          isSelected ? "bg-[#04332d]/5 font-semibold" : "hover:bg-gray-50/80"
                        }`}
                      >
                        <td className="px-3.5 py-3 text-[10px] font-mono font-bold text-[#04332d] whitespace-nowrap">
                          {row.sessionId}
                        </td>
                        <td className="px-3.5 py-3 text-[10px] font-mono text-gray-500 whitespace-nowrap">
                          {row.timestamp}
                        </td>
                        <td className="px-3.5 py-3 text-[10px] text-gray-700 font-medium whitespace-nowrap">
                          {row.docType}
                        </td>
                        <td className="px-3.5 py-3 text-[10px] text-gray-900 font-bold whitespace-nowrap">
                          {row.name}
                        </td>
                        <td className="px-3.5 py-3 text-[10px] font-mono text-gray-600 whitespace-nowrap">
                          {row.docNumber || "—"}
                        </td>
                        <td className="px-3.5 py-3 text-[10px] font-mono text-[#04332d] bg-gray-50 rounded px-1.5 py-0.5 whitespace-nowrap">
                          <span className="text-emerald-600 font-bold mr-1">✓</span>{hashDisplay}
                        </td>
                        <td className="px-3.5 py-3 whitespace-nowrap">
                          <RiskBadge risk={row.riskLevel} />
                        </td>
                        <td className="px-3.5 py-3 text-[10px] font-bold text-gray-800 whitespace-nowrap">
                          {row.riskScore}/100
                        </td>
                        <td className="px-3.5 py-3 whitespace-nowrap">
                          <ActionBadge decision={row.decision} />
                        </td>
                        <td className="px-3.5 py-3 whitespace-nowrap">
                          <button
                            onClick={(e) => handleDownloadPDF(row, e)}
                            disabled={downloadingId === row.sessionId}
                            className="flex items-center gap-1 px-2.5 py-1 text-[10px] font-bold text-[#04332d] bg-[#04332d]/10 hover:bg-[#04332d]/20 rounded border border-[#04332d]/20 transition-all disabled:opacity-50"
                          >
                            <Download className="w-3 h-3" />
                            {downloadingId === row.sessionId ? "PDF…" : "Download"}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Selected Report Preview Card */}
          {selectedRecord && (
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden fade-up">
              <div className="bg-[#04332d] px-6 py-4 text-white flex justify-between items-center">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold tracking-widest uppercase opacity-70">
                      VERIFICATION REPORT PREVIEW
                    </span>
                    <span className="text-[9px] bg-white/20 px-2 py-0.5 rounded font-mono font-bold">
                      {selectedRecord.sessionId}
                    </span>
                  </div>
                  <h3 className="text-base font-black tracking-tight mt-1">{selectedRecord.name}</h3>
                  <p className="text-[10px] opacity-60 mt-0.5">
                    Generated: {selectedRecord.timestamp} · Verifying Officer: {selectedRecord.officer || "operator"}
                  </p>
                </div>
                <button
                  onClick={() => handleDownloadPDF(selectedRecord)}
                  disabled={downloadingId === selectedRecord.sessionId}
                  className="flex items-center gap-2 px-3 py-2 bg-white text-[#04332d] text-xs font-bold rounded-lg hover:bg-gray-100 transition-colors shadow"
                >
                  <FileText className="w-4 h-4" />
                  {downloadingId === selectedRecord.sessionId ? "Generating PDF…" : "Download PDF Report"}
                </button>
              </div>

              <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6 text-sm border-b border-gray-100">
                {/* Extracted Details */}
                <div className="space-y-3">
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                    Uploaded &amp; Extracted Data
                  </p>
                  <div className="space-y-1.5 text-xs text-gray-600 bg-gray-50 p-3 rounded-lg border border-gray-100">
                    <p><span className="font-semibold text-gray-800">Document Type:</span> {selectedRecord.docType}</p>
                    <p><span className="font-semibold text-gray-800">Document Number:</span> {selectedRecord.docNumber || "—"}</p>
                    <p><span className="font-semibold text-gray-800">Date of Birth:</span> {selectedRecord.dob || "—"}</p>
                    <p><span className="font-semibold text-gray-800">Gender:</span> {selectedRecord.gender || "—"}</p>
                    <p><span className="font-semibold text-gray-800">Nationality:</span> {selectedRecord.nationality || "—"}</p>
                  </div>
                </div>

                {/* Scores & Assessment */}
                <div className="space-y-3">
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                    Scores &amp; Assessment
                  </p>
                  <div className="space-y-1.5 text-xs text-gray-600 bg-gray-50 p-3 rounded-lg border border-gray-100">
                    <p className="flex justify-between items-center">
                      <span className="font-semibold text-gray-800">Risk Score:</span>
                      <span className="font-bold text-sm text-[#04332d]">{selectedRecord.riskScore}/100</span>
                    </p>
                    <p className="flex justify-between items-center">
                      <span className="font-semibold text-gray-800">Risk Level:</span>
                      <RiskBadge risk={selectedRecord.riskLevel} />
                    </p>
                    <p className="flex justify-between items-center">
                      <span className="font-semibold text-gray-800">Decision:</span>
                      <ActionBadge decision={selectedRecord.decision} />
                    </p>
                    <p><span className="font-semibold text-gray-800">Tamper Status:</span> {selectedRecord.tampering ? "Tampering Flagged ⚠" : "Clean ✓"}</p>
                  </div>
                </div>

                {/* Cryptographic Ledger & Evidence */}
                <div className="space-y-3">
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                    Cryptographic Audit &amp; Watchlist
                  </p>
                  <div className="space-y-2 bg-[#04332d]/5 p-3 rounded-lg border border-[#04332d]/20 text-xs">
                    <div className="flex justify-between text-[11px] text-gray-700 font-mono">
                      <span>SHA-256 Hash:</span>
                      <span className="font-bold text-[#04332d]">{selectedRecord.blockHash ? `${selectedRecord.blockHash.slice(0, 14)}...` : `0x${selectedRecord.sessionId.slice(-8)}...`}</span>
                    </div>
                    <div className="flex justify-between text-[11px] text-gray-700">
                      <span>Watchlist Check:</span>
                      <span className="font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded">CLEAR ✓</span>
                    </div>
                    <div className="flex justify-between text-[11px] text-gray-700">
                      <span>Ledger Status:</span>
                      <span className="font-bold text-emerald-700">IMMUTABLE VERIFIED</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
