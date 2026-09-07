"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiHealth } from "@/lib/api";
import { useAuth } from "@/lib/AuthContext";
import { useSession } from "@/lib/SessionContext";
import WorkstationView from "@/components/workstation/WorkstationView";
import AuditTrailView from "@/components/workstation/AuditTrailView";
import { EyeEmblem } from "@/components/TrinetraLogo";
import { Activity, LogOut, Eye, PlusCircle, ShieldCheck } from "lucide-react";

export default function WorkstationPage() {
  const router = useRouter();
  const { user, isAuthenticated, loading: authLoading, logout } = useAuth();
  const { activeSessionId, createSession, clearSession, loading: sessionLoading } = useSession();
  const [online, setOnline] = useState(false);
  const [activeTab, setActive] = useState("workstation");

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace("/login");
      return;
    }

    if (isAuthenticated) {
      apiHealth()
        .then((h) => setOnline(h.database === "connected" || h.status === "healthy"))
        .catch(() => setOnline(false));
    }
  }, [authLoading, isAuthenticated, router]);

  const handleSignOut = () => {
    clearSession();
    logout();
    router.replace("/login");
  };

  const handleCreateNewSession = async () => {
    try {
      await createSession("Identity Verification", "passport");
    } catch (err) {
      console.error("Failed to create new verification session:", err);
    }
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-[#f5f5f3] flex flex-col items-center justify-center font-sans">
        <div className="flex items-center gap-3 px-6 py-4 bg-white border border-gray-200 rounded-xl shadow-sm">
          <svg className="w-5 h-5 text-[#04332d] spin-slow" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
          </svg>
          <span className="text-xs font-semibold text-[#04332d]">Loading Workstation Environment…</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f5f5f3] flex flex-col font-sans">
      {/* ── Fixed & Clean Workstation Navbar ── */}
      <nav className="bg-white border-b border-gray-200 px-4 py-0 flex items-center justify-between h-12 shrink-0 z-40 shadow-xs">
        {/* Left: Brand Logo & Navigation Tabs */}
        <div className="flex items-center gap-4 h-full">
          <div className="flex items-center gap-2 pr-3 border-r border-gray-200 h-6">
            <EyeEmblem className="w-6 h-6 shrink-0" />
            <span className="font-black text-[#04332d] text-sm tracking-tight">Trinetra</span>
            <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider hidden sm:inline">
              FORENSIC WORKSTATION
            </span>
          </div>

          {/* Nav Tabs */}
          <div className="flex items-center h-full">
            {[
              { id: "workstation", label: "Workstation", Icon: Eye },
              { id: "audit", label: "Audit Trail", Icon: Activity },
            ].map(({ id, label, Icon }) => (
              <button
                key={id}
                onClick={() => setActive(id)}
                className={`flex items-center gap-2 px-3.5 h-12 text-xs font-semibold border-b-2 transition-all ${
                  activeTab === id
                    ? "border-[#04332d] text-[#04332d] bg-[#04332d]/5"
                    : "border-transparent text-gray-500 hover:text-gray-800 hover:bg-gray-50"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Right: Operator Actions & User Info */}
        <div className="flex items-center gap-3">
          {/* System Online Status */}
          <div className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200/60">
            <span className={`w-2 h-2 rounded-full ${online ? "bg-emerald-500 animate-pulse" : "bg-red-400"}`} />
            <span className="text-[10px] font-bold text-emerald-700">{online ? "Online" : "Offline"}</span>
          </div>

          {/* Session Badge or Create Session */}
          {activeSessionId ? (
            <div className="flex items-center gap-1 text-[11px] font-mono text-[#04332d] bg-[#04332d]/10 border border-[#04332d]/20 px-2.5 py-0.5 rounded-md font-bold">
              <span className="text-[9px] text-gray-400 font-sans uppercase">Session:</span>
              {activeSessionId}
            </div>
          ) : (
            <button
              onClick={handleCreateNewSession}
              disabled={sessionLoading}
              className="flex items-center gap-1 text-[11px] font-bold text-white bg-[#04332d] px-2.5 py-1 rounded-md hover:bg-[#03241f] active:scale-[0.98] transition-all disabled:opacity-50 shadow-xs"
            >
              <PlusCircle className="w-3 h-3" />
              <span>{sessionLoading ? "Creating…" : "New Session"}</span>
            </button>
          )}

          {/* User Badge */}
          <div className="hidden md:flex items-center gap-1.5 text-xs text-gray-700 font-semibold bg-gray-100/90 border border-gray-200/80 px-2.5 py-1 rounded-md">
            <ShieldCheck className="w-3.5 h-3.5 text-[#04332d]" />
            <span>{user?.username}</span>
            <span className="text-[10px] text-gray-400 font-normal">({user?.role || "operator"})</span>
          </div>

          {/* Sign Out Button */}
          <button
            onClick={handleSignOut}
            className="flex items-center gap-1 text-xs text-gray-400 hover:text-red-600 transition-colors p-1.5 rounded-md hover:bg-red-50"
            title="Sign Out"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span className="hidden md:inline font-medium">Sign Out</span>
          </button>
        </div>
      </nav>

      {/* ── Body ── */}
      <div className="flex-1 overflow-hidden relative">
        <div className={`h-full ${activeTab === "workstation" ? "block" : "hidden"}`}>
          <WorkstationView user={user} masterSessionId={activeSessionId} />
        </div>
        <div className={`h-full ${activeTab === "audit" ? "block" : "hidden"}`}>
          <AuditTrailView />
        </div>
      </div>
    </div>
  );
}
