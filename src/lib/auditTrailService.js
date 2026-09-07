/**
 * auditTrailService.js
 * Centralized service for managing audit history records, capped at max 10 items.
 */

const STORAGE_KEY = "trinetra_audit_history";

// Initial mock history so previous data is present out-of-the-box
const INITIAL_MOCK_RECORDS = [
  {
    sessionId: "TRN-904812",
    timestamp: "2026-09-07 18:32:10",
    name: "RAHUL KUMAR",
    docType: "PASSPORT",
    docNumber: "P12345678",
    dob: "24/11/1992",
    gender: "MALE",
    nationality: "IND",
    riskLevel: "LOW",
    riskScore: 12,
    decision: "Clean — e-Gate Unlocked",
    tampering: false,
    officer: "officer1",
    evidence: [
      { label: "OCR Confidence", score: 98 },
      { label: "Document Authenticity", score: 95 },
      { label: "Face Similarity", score: 92 },
      { label: "Liveness Score", score: 99 },
    ],
    reasons: [],
  },
  {
    sessionId: "TRN-882319",
    timestamp: "2026-09-07 17:45:00",
    name: "SARAH MITCHELL",
    docType: "PASSPORT",
    docNumber: "GB9876543",
    dob: "14/03/1992",
    gender: "FEMALE",
    nationality: "GBR",
    riskLevel: "HIGH",
    riskScore: 88,
    decision: "Fraud/Impostor — Gate Locked",
    tampering: true,
    officer: "officer1",
    evidence: [
      { label: "OCR Confidence", score: 65 },
      { label: "Document Authenticity", score: 32 },
      { label: "Face Similarity", score: 25 },
      { label: "Liveness Score", score: 80 },
    ],
    reasons: ["Photo tampering detected by ELA", "Low face similarity match"],
  },
  {
    sessionId: "TRN-761204",
    timestamp: "2026-09-07 16:10:44",
    name: "VIKTOR PETROV",
    docType: "AADHAAR CARD",
    docNumber: "9988-7766-5544",
    dob: "10/05/1988",
    gender: "MALE",
    nationality: "IND",
    riskLevel: "MEDIUM",
    riskScore: 54,
    decision: "Suspicious — Manual Inspection",
    tampering: false,
    officer: "officer1",
    evidence: [
      { label: "OCR Confidence", score: 85 },
      { label: "Document Authenticity", score: 70 },
      { label: "Face Similarity", score: 62 },
      { label: "Liveness Score", score: 90 },
    ],
    reasons: ["Verhoeff checksum anomaly", "Face match border-line threshold"],
  },
  {
    sessionId: "TRN-654109",
    timestamp: "2026-09-07 15:20:15",
    name: "ELENA ROSTOVA",
    docType: "PASSPORT",
    docNumber: "RU5544332",
    dob: "02/09/1995",
    gender: "FEMALE",
    nationality: "RUS",
    riskLevel: "LOW",
    riskScore: 8,
    decision: "Clean — e-Gate Unlocked",
    tampering: false,
    officer: "officer1",
    evidence: [
      { label: "OCR Confidence", score: 99 },
      { label: "Document Authenticity", score: 98 },
      { label: "Face Similarity", score: 96 },
      { label: "Liveness Score", score: 100 },
    ],
    reasons: [],
  },
  {
    sessionId: "TRN-541298",
    timestamp: "2026-09-07 14:05:30",
    name: "ALEXANDER VANCE",
    docType: "DRIVING LICENSE",
    docNumber: "DL-99887766",
    dob: "18/12/1980",
    gender: "MALE",
    nationality: "USA",
    riskLevel: "LOW",
    riskScore: 15,
    decision: "Clean — e-Gate Unlocked",
    tampering: false,
    officer: "officer1",
    evidence: [
      { label: "OCR Confidence", score: 95 },
      { label: "Document Authenticity", score: 94 },
      { label: "Face Similarity", score: 90 },
      { label: "Liveness Score", score: 95 },
    ],
    reasons: [],
  }
];

export function getAuditHistory() {
  if (typeof window === "undefined") return INITIAL_MOCK_RECORDS.slice(0, 10);
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_MOCK_RECORDS));
      return INITIAL_MOCK_RECORDS.slice(0, 10);
    }
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed) || parsed.length === 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_MOCK_RECORDS));
      return INITIAL_MOCK_RECORDS.slice(0, 10);
    }
    // Return max 10 records
    return parsed.slice(0, 10);
  } catch {
    return INITIAL_MOCK_RECORDS.slice(0, 10);
  }
}

export function saveAuditRecord(record) {
  if (typeof window === "undefined") return;
  try {
    const current = getAuditHistory();
    // Check if record with same sessionId exists, update it or prepend
    const existingIdx = current.findIndex(r => r.sessionId === record.sessionId);
    let updated;
    if (existingIdx >= 0) {
      updated = [...current];
      updated[existingIdx] = { ...updated[existingIdx], ...record };
    } else {
      updated = [record, ...current];
    }
    // Enforce MAX 10 RECORDS
    const trimmed = updated.slice(0, 10);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
    // Also save in sessionStorage for backward compatibility
    sessionStorage.setItem("trinetra_audit", JSON.stringify(trimmed));
    return trimmed;
  } catch (err) {
    console.error("Failed to save audit record:", err);
  }
}

export function addRecordFromCaseData(caseData, user = null, sessionIdOverride = null) {
  if (!caseData) return;
  const docFields = caseData.docData || [];
  const findVal = (key) => {
    const f = docFields.find((d) => d.key === key);
    return f ? f.value : "—";
  };

  const name = findVal("name");
  const docNumber = findVal("docno");
  const docType = findVal("doctype") !== "—" ? findVal("doctype") : caseData.docType || "PASSPORT";
  const dob = findVal("dob");
  const gender = findVal("gender");
  const nationality = findVal("nat");

  const sessionId = sessionIdOverride || `TRN-${Math.floor(100000 + Math.random() * 900000)}`;
  const now = new Date();
  const timestamp = now.toISOString().replace("T", " ").substring(0, 19);
  const blockHash = caseData.block_hash || `0x7f8a${Math.random().toString(16).slice(2, 10)}${Math.random().toString(16).slice(2, 10)}`;

  const record = {
    sessionId,
    timestamp,
    blockHash,
    name: name !== "—" ? name : "UNKNOWN SUBJECT",
    docType: docType.toUpperCase(),
    docNumber: docNumber !== "—" ? docNumber : "UNKNOWN",
    dob,
    gender,
    nationality,
    riskLevel: (caseData.riskLevel || "Low").toUpperCase(),
    riskScore: caseData.riskScore ?? 0,
    decision: caseData.riskAction || (caseData.riskLevel === "Low" ? "Clean — e-Gate Unlocked" : "Manual Inspection"),
    tampering: caseData.forensics?.manipulationIndicators > 0 || (caseData.riskLevel === "High"),
    officer: user?.username || "officer1",
    evidence: caseData.evidence || [],
    reasons: caseData.reasons || [],
    caseData: caseData,
  };

  return saveAuditRecord(record);
}

export function exportCSVFromRecords(recordsList = []) {
  const records = recordsList.length > 0 ? recordsList.slice(0, 10) : getAuditHistory().slice(0, 10);
  
  const headers = [
    "Verification ID",
    "Timestamp",
    "Subject Name",
    "Document Type",
    "Document Number",
    "Date of Birth",
    "Risk Score",
    "Risk Level",
    "Decision",
    "Status"
  ];

  const escapeCSV = (val) => {
    if (val === null || val === undefined) return '""';
    const str = String(val).replace(/"/g, '""');
    return `"${str}"`;
  };

  const rows = records.map((r) => [
    escapeCSV(r.sessionId),
    escapeCSV(r.timestamp),
    escapeCSV(r.name),
    escapeCSV(r.docType),
    escapeCSV(r.docNumber),
    escapeCSV(r.dob),
    escapeCSV(`${r.riskScore}/100`),
    escapeCSV(r.riskLevel),
    escapeCSV(r.decision),
    escapeCSV("COMPLETED")
  ]);

  const csvContent = [headers.map(escapeCSV).join(","), ...rows.map((row) => row.join(","))].join("\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", `Trinetra_Audit_Trail_${new Date().toISOString().slice(0,10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
