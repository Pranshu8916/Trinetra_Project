import React from "react";

export default function RiskBadge({ score }) {
  // Color configuration shifts dynamically based on incoming numeric alerts
  let colorClass = "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
  let statusText = "CLEAR ENTRY";

  if (score >= 75) {
    colorClass = "bg-rose-500/10 text-rose-400 border-rose-500/30 animate-pulse";
    statusText = "DETAIN / ESCALATE";
  } else if (score >= 40) {
    colorClass = "bg-amber-500/10 text-amber-400 border-amber-500/20";
    statusText = "SECONDARY SCAN";
  }

  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${colorClass}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-2"></span>
      {statusText} ({score}%)
    </span>
  );
}
